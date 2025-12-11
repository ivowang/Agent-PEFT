import os
import json
import torch
import torch.nn.functional as F
from typing import Optional, Any
from src.callbacks.callback import Callback, CallbackArguments
from src.typings import (
    SessionEvaluationOutcome,
    SampleStatus,
    Role,
)
from src.language_models.instance.huggingface_lora_language_model import (
    HuggingfaceLoRALanguageModel,
)
from src.utils import SafeLogger


class RLTrainingCallback(Callback):
    """
    Reinforcement Learning Callback for training LoRA with reward signals.
    Uses REINFORCE algorithm to update LoRA parameters based on task outcomes.
    """

    def __init__(
        self,
        reward_weight: float = 1.0,
        learning_rate: float = 1e-5,
        optimizer_class: str = "AdamW",
        gradient_accumulation_steps: int = 1,
        reward_correct: float = 1.0,
        reward_incorrect: float = -0.1,
        reward_timeout: float = -0.3,
    ):
        """
        Args:
            reward_weight: Weight for reward signal
            learning_rate: Learning rate for optimizer
            optimizer_class: Optimizer class name ("AdamW" or "Adam")
            gradient_accumulation_steps: Number of steps to accumulate gradients
            reward_correct: Reward for correct answer
            reward_incorrect: Reward for incorrect answer
            reward_timeout: Reward for timeout/limit reached
        """
        super().__init__()
        self.reward_weight = reward_weight
        self.learning_rate = learning_rate
        self.optimizer_class_name = optimizer_class
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.reward_correct = reward_correct
        self.reward_incorrect = reward_incorrect
        self.reward_timeout = reward_timeout

        self.optimizer: Optional[torch.optim.Optimizer] = None
        self.current_session_logprob: Optional[torch.Tensor] = None
        self.gradient_accumulation_counter = 0
        self.training_step = 0

    @classmethod
    def is_unique(cls) -> bool:
        return True

    def _get_optimizer_state_path(self) -> str:
        return os.path.join(self.get_state_dir(), "optimizer_state.pt")

    def _get_training_step_path(self) -> str:
        return os.path.join(self.get_state_dir(), "training_step.json")

    def restore_state(self) -> None:
        """Restore optimizer state and training step."""
        language_model = self._get_language_model()
        if language_model is None:
            return

        if self.optimizer is None:
            self._initialize_optimizer(language_model)

        optimizer_state_path = self._get_optimizer_state_path()
        training_step_path = self._get_training_step_path()

        if os.path.exists(optimizer_state_path) and self.optimizer is not None:
            try:
                state_dict = torch.load(optimizer_state_path, map_location="cpu")
                self.optimizer.load_state_dict(state_dict)
                SafeLogger.info(
                    f"[RLTrainingCallback] Loaded optimizer state from {optimizer_state_path}"
                )
            except Exception as e:
                SafeLogger.warning(
                    f"[RLTrainingCallback] Failed to load optimizer state: {e}"
                )

        if os.path.exists(training_step_path):
            try:
                with open(training_step_path, "r") as f:
                    data = json.load(f)
                    self.training_step = data.get("training_step", 0)
            except Exception as e:
                SafeLogger.warning(
                    f"[RLTrainingCallback] Failed to load training step: {e}"
                )

    def _get_language_model(self) -> Optional[HuggingfaceLoRALanguageModel]:
        """Get LoRA language model from callback args (will be set in on_session_create)."""
        # This is a workaround - we'll store it when we have access to callback_args
        if hasattr(self, "_cached_language_model"):
            return self._cached_language_model
        return None

    def _initialize_optimizer(
        self, language_model: HuggingfaceLoRALanguageModel
    ) -> None:
        """Initialize optimizer for LoRA parameters."""
        trainable_params = language_model.get_trainable_parameters()
        if len(trainable_params) == 0:
            SafeLogger.warning(
                "[RLTrainingCallback] No trainable parameters found in LoRA model"
            )
            return

        if self.optimizer_class_name == "AdamW":
            self.optimizer = torch.optim.AdamW(
                trainable_params, lr=self.learning_rate
            )
        elif self.optimizer_class_name == "Adam":
            self.optimizer = torch.optim.Adam(
                trainable_params, lr=self.learning_rate
            )
        else:
            raise ValueError(
                f"Unknown optimizer class: {self.optimizer_class_name}"
            )

        SafeLogger.info(
            f"[RLTrainingCallback] Initialized {self.optimizer_class_name} optimizer "
            f"with {len(trainable_params)} trainable parameters"
        )

    def on_session_create(self, callback_args: CallbackArguments) -> None:
        """Initialize optimizer and switch model to training mode."""
        language_model = callback_args.session_context.agent._language_model
        if not isinstance(language_model, HuggingfaceLoRALanguageModel):
            SafeLogger.warning(
                "[RLTrainingCallback] Language model is not HuggingfaceLoRALanguageModel, "
                "RL training will be skipped"
            )
            return

        # Cache language model for later use
        self._cached_language_model = language_model

        # Initialize optimizer if not already done
        if self.optimizer is None:
            self._initialize_optimizer(language_model)

        # Switch to training mode
        language_model.train_mode()
        self.current_session_logprob = None
        self.gradient_accumulation_counter = 0

    def on_agent_inference(self, callback_args: CallbackArguments) -> None:
        """
        Record logprobs for RL training.
        Note: This requires modifying the agent to use _inference_with_logprobs.
        For now, we'll store a placeholder that will be filled by the agent.
        """
        # The actual logprob recording will be done by a modified agent
        # that calls _inference_with_logprobs and stores the result here
        pass

    def _calculate_reward(
        self, callback_args: CallbackArguments
    ) -> float:
        """Calculate reward based on task outcome."""
        current_session = callback_args.current_session

        if (
            current_session.evaluation_record.outcome
            == SessionEvaluationOutcome.CORRECT
            and current_session.sample_status == SampleStatus.COMPLETED
        ):
            return self.reward_correct
        elif current_session.sample_status == SampleStatus.TASK_LIMIT_REACHED:
            return self.reward_timeout
        elif (
            current_session.evaluation_record.outcome
            == SessionEvaluationOutcome.INCORRECT
        ):
            return self.reward_incorrect
        else:
            # Other error cases
            return self.reward_incorrect

    def on_task_complete(self, callback_args: CallbackArguments) -> None:
        """Update LoRA parameters based on reward signal."""
        language_model = self._get_language_model()
        if language_model is None or self.optimizer is None:
            return

        # Calculate reward
        reward = self._calculate_reward(callback_args)

        # Get logprob (should be set by agent during inference)
        if self.current_session_logprob is None:
            SafeLogger.warning(
                "[RLTrainingCallback] No logprob recorded for this session, skipping RL update"
            )
            language_model.eval_mode()
            return

        # REINFORCE algorithm: loss = -logprob * reward
        # We want to maximize reward, so we minimize -logprob * reward
        loss = -self.current_session_logprob * reward * self.reward_weight

        # Accumulate gradients
        loss = loss / self.gradient_accumulation_steps
        loss.backward()

        self.gradient_accumulation_counter += 1

        # Update parameters if accumulation is complete
        if (
            self.gradient_accumulation_counter >= self.gradient_accumulation_steps
        ):
            self.optimizer.step()
            self.optimizer.zero_grad()
            self.gradient_accumulation_counter = 0
            self.training_step += 1

            SafeLogger.info(
                f"[RLTrainingCallback] Updated LoRA parameters (step {self.training_step}, "
                f"reward: {reward:.3f}, loss: {loss.item() * self.gradient_accumulation_steps:.6f})"
            )

        # Reset for next session
        self.current_session_logprob = None
        language_model.eval_mode()

    def on_state_save(self, callback_args: CallbackArguments) -> None:
        """Save LoRA weights, optimizer state, and training step."""
        language_model = self._get_language_model()
        if language_model is None:
            return

        # Save LoRA weights
        lora_save_path = os.path.join(self.get_state_dir(), "lora_weights")
        language_model.save_lora(lora_save_path)

        # Save optimizer state
        if self.optimizer is not None:
            optimizer_state_path = self._get_optimizer_state_path()
            torch.save(self.optimizer.state_dict(), optimizer_state_path)

        # Save training step
        training_step_path = self._get_training_step_path()
        with open(training_step_path, "w") as f:
            json.dump({"training_step": self.training_step}, f, indent=2)

    def set_session_logprob(self, logprob: torch.Tensor) -> None:
        """Set logprob for current session (called by agent)."""
        self.current_session_logprob = logprob.detach().requires_grad_(True)

