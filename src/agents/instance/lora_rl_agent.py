from typing import Any, Optional, Mapping
from typing_extensions import override

from src.agents.agent import Agent
from src.typings import (
    ChatHistoryItem,
    ChatHistory,
    LanguageModelContextLimitException,
    AgentContextLimitException,
    LanguageModelOutOfMemoryException,
    AgentOutOfMemoryException,
    LanguageModelUnknownException,
    AgentUnknownException,
    Role,
)
from src.language_models.instance.huggingface_lora_language_model import (
    HuggingfaceLoRALanguageModel,
)


class LoRARLAgent(Agent):
    """
    Agent that supports RL training with LoRA.
    Records logprobs during inference for RL callback.
    """

    def __init__(
        self,
        language_model: HuggingfaceLoRALanguageModel,
        system_prompt: str = "You are a helpful assistant.",
        inference_config_dict: Optional[Mapping[str, Any]] = None,
        rl_callback=None,  # RLTrainingCallback instance
    ):
        """
        Args:
            language_model: LoRA-enabled language model
            system_prompt: System prompt
            inference_config_dict: Inference configuration
            rl_callback: RLTrainingCallback instance for recording logprobs
        """
        if not isinstance(language_model, HuggingfaceLoRALanguageModel):
            raise ValueError(
                "LoRARLAgent requires HuggingfaceLoRALanguageModel"
            )
        self._language_model = language_model
        self._system_prompt = system_prompt
        self._inference_config_dict = inference_config_dict
        self._rl_callback = rl_callback

    def _inference(self, chat_history: ChatHistory) -> ChatHistoryItem:
        try:
            # Use inference with logprobs if RL callback is available
            if self._rl_callback is not None:
                result, logprobs = self._language_model._inference_with_logprobs(
                    [chat_history],
                    self._inference_config_dict or {},
                    self._system_prompt,
                )
                # Store logprob in callback for RL training
                if len(logprobs) > 0:
                    self._rl_callback.set_session_logprob(logprobs[0])
                return result[0]
            else:
                # Fallback to normal inference
                return self._language_model.inference(
                    [chat_history], self._inference_config_dict, self._system_prompt
                )[0]
        except LanguageModelContextLimitException as e:
            raise AgentContextLimitException(str(e)) from e
        except LanguageModelOutOfMemoryException as e:
            raise AgentOutOfMemoryException(str(e)) from e
        except LanguageModelUnknownException as e:
            raise AgentUnknownException(str(e)) from e

    @override
    def get_role_dict(self) -> Mapping[Role, str]:
        return self._language_model.role_dict

    def set_rl_callback(self, rl_callback) -> None:
        """Set RL callback for recording logprobs."""
        self._rl_callback = rl_callback

