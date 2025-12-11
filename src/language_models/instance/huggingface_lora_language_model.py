import torch
import os
from typing import Any, Optional, Mapping, Sequence
from peft import LoraConfig, get_peft_model, PeftModel  # type: ignore[import-untyped]
from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore[import-untyped]
import niuload  # type: ignore[import-untyped]

from src.language_models.instance.huggingface_language_model import (
    HuggingfaceLanguageModel,
)
from src.typings import (
    Role,
    ChatHistoryItem,
    LanguageModelContextLimitException,
    LanguageModelOutOfMemoryException,
    ChatHistory,
)


class HuggingfaceLoRALanguageModel(HuggingfaceLanguageModel):
    def __init__(
        self,
        model_name_or_path: str,
        role_dict: Mapping[str, str],
        lora_config: Optional[LoraConfig] = None,
        peft_model_path: Optional[str] = None,  # 加载已训练的LoRA
        dtype: torch.dtype | str = torch.bfloat16,
        device_map: str | Mapping[str, Any] = "auto",
    ):
        """
        LoRA-enabled Language Model with zero initialization.
        
        Args:
            model_name_or_path: Base model path
            role_dict: Role mapping dictionary
            lora_config: LoRA configuration (if None and peft_model_path is None, will create default)
            peft_model_path: Path to pre-trained LoRA weights (optional)
            dtype: Model dtype
            device_map: Device mapping strategy
        """
        # Initialize base model first
        super().__init__(model_name_or_path, role_dict, dtype, device_map)
        
        # Load or create LoRA
        if peft_model_path and os.path.exists(peft_model_path):
            # Load existing LoRA weights
            self.model = PeftModel.from_pretrained(
                self.model, peft_model_path
            )
            self.lora_config = None  # Already loaded
        elif lora_config:
            # Create new LoRA with zero initialization
            self.model = get_peft_model(self.model, lora_config)
            self.lora_config = lora_config
        else:
            # Create default LoRA config
            default_lora_config = LoraConfig(
                r=16,
                lora_alpha=32,
                target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
                lora_dropout=0.1,
                bias="none",
                task_type="CAUSAL_LM",
            )
            self.model = get_peft_model(self.model, default_lora_config)
            self.lora_config = default_lora_config
        
        self.peft_model_path = peft_model_path
    
    def save_lora(self, output_path: str) -> None:
        """Save LoRA weights to disk."""
        if isinstance(self.model, PeftModel):
            self.model.save_pretrained(output_path)
        else:
            # If model has PEFT adapters
            self.model.save_pretrained(output_path)
    
    def train_mode(self) -> None:
        """Switch to training mode."""
        self.model.train()
    
    def eval_mode(self) -> None:
        """Switch to evaluation mode."""
        self.model.eval()
    
    def get_trainable_parameters(self) -> Sequence[torch.nn.Parameter]:
        """Get trainable parameters (LoRA parameters only)."""
        return [p for p in self.model.parameters() if p.requires_grad]
    
    def _inference_with_logprobs(
        self,
        batch_chat_history: Sequence[ChatHistory],
        inference_config_dict: Mapping[str, Any],
        system_prompt: str,
    ) -> tuple[Sequence[ChatHistoryItem], Sequence[torch.Tensor]]:
        """
        Inference with log probabilities for RL training.
        
        Returns:
            Tuple of (ChatHistoryItem list, logprobs tensor list)
        """
        # Set tokenizer attributes
        original_tokenizer_padding_side = self.tokenizer.padding_side
        original_tokenizer_pad_token = self.tokenizer.pad_token
        self.tokenizer.padding_side = "left"
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Construct batch_message_list
        message_list_prefix: list[Mapping[str, str]]
        if len(system_prompt) > 0:
            message_list_prefix = [{"role": "system", "content": system_prompt}]
        else:
            message_list_prefix = []
        batch_message_list: Sequence[Sequence[Mapping[str, str]]] = [
            message_list_prefix
            + self._convert_chat_history_to_message_list(chat_history)
            for chat_history in batch_chat_history
        ]
        
        # Convert to model input
        model_input_dict: Mapping[str, torch.Tensor] = (
            self._convert_message_list_to_model_input_dict(batch_message_list)
        )
        batch_input_ids, batch_attention_mask = (
            model_input_dict["batch_input_ids"],
            model_input_dict["batch_attention_mask"],
        )
        del model_input_dict
        
        # Check input length
        if batch_input_ids.shape[-1] >= self.model.config.max_position_embeddings:
            raise LanguageModelContextLimitException(
                f"Input length {batch_input_ids.shape[-1]} exceeds the model's max_position_embeddings "
                f"{self.model.config.max_position_embeddings}."
            )
        
        torch.cuda.synchronize()
        
        try:
            # Generate with return_dict_in_generate to get scores
            output = self.model.generate(
                batch_input_ids,
                attention_mask=batch_attention_mask,
                pad_token_id=self.tokenizer.eos_token_id,
                return_dict_in_generate=True,
                output_scores=True,
                **inference_config_dict,
            )
            
            # Extract generated tokens
            output_tensor: torch.Tensor = output.sequences
            generated_tokens = output_tensor[:, batch_input_ids.shape[1]:]
            
            # Calculate logprobs from scores
            total_logprobs_list: list[torch.Tensor] = []
            
            if output.scores and len(output.scores) > 0:
                # scores is a tuple of tensors, each of shape (batch_size, vocab_size)
                batch_size = generated_tokens.shape[0]
                seq_length = generated_tokens.shape[1]
                
                for batch_idx in range(batch_size):
                    sequence_logprobs = []
                    for step_idx in range(min(len(output.scores), seq_length)):
                        # Get logprobs for this step
                        step_scores = output.scores[step_idx]  # (batch_size, vocab_size)
                        step_logprobs = torch.nn.functional.log_softmax(
                            step_scores, dim=-1
                        )
                        
                        # Get the token that was actually generated
                        token_id = generated_tokens[batch_idx, step_idx].item()
                        
                        # Get logprob of this token
                        token_logprob = step_logprobs[batch_idx, token_id]
                        sequence_logprobs.append(token_logprob)
                    
                    # Sum logprobs for the entire sequence
                    if sequence_logprobs:
                        total_logprob = torch.stack(sequence_logprobs).sum()
                    else:
                        total_logprob = torch.tensor(0.0, device=self.model.device)
                    
                    total_logprobs_list.append(total_logprob)
            else:
                # Fallback: return zero logprobs
                batch_size = generated_tokens.shape[0]
                total_logprobs_list = [
                    torch.tensor(0.0, device=self.model.device)
                    for _ in range(batch_size)
                ]
            
        except Exception as e:
            if (
                isinstance(e, torch.cuda.OutOfMemoryError)
                or HuggingfaceLanguageModel._is_any_gpu_memory_high()
            ):
                torch.cuda.empty_cache()
                raise LanguageModelOutOfMemoryException(str(e)) from e
            else:
                raise e
        finally:
            torch.cuda.synchronize()
        
        # Convert output to ChatHistoryItem
        output_str_list: Sequence[str] = self.tokenizer.batch_decode(
            output_tensor[:, batch_input_ids.shape[1] :], skip_special_tokens=True
        )
        output_list: Sequence[ChatHistoryItem] = [
            ChatHistoryItem(role=Role.AGENT, content=output_str)
            for output_str in output_str_list
        ]
        
        # Reset tokenizer attributes
        self.tokenizer.padding_side = original_tokenizer_padding_side
        self.tokenizer.pad_token = original_tokenizer_pad_token
        
        return output_list, total_logprobs_list

