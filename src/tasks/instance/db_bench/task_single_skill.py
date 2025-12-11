import random
import json
from typing import Optional
from src.tasks.instance.db_bench.task import DBBench, DBBenchDatasetItem
from src.tasks.instance.db_bench.single_skill_task_generator import (
    SingleSkillTaskGenerator,
)
from src.typings import Session, SampleIndex, TaskName, SampleStatus
from src.factories.chat_history_item import ChatHistoryItemFactory
from src.tasks.task import Task
from src.typings import (
    ContinualAgentBenchException,
    TaskEnvironmentException,
    TaskUnknownException,
)


class DBBenchSingleSkill(DBBench):
    """
    DBBench variant that dynamically generates single-skill tasks.
    Each reset generates a new random single-skill task.
    """

    def __init__(
        self,
        task_name: TaskName,
        chat_history_item_factory: ChatHistoryItemFactory,
        single_skill_task_generator: SingleSkillTaskGenerator,
        max_round: int,
        random_seed: Optional[int] = None,
    ):
        """
        Args:
            task_name: Task name
            chat_history_item_factory: Chat history item factory
            single_skill_task_generator: Generator for single-skill tasks
            max_round: Maximum number of interaction rounds
            random_seed: Random seed for task generation
        """
        # Create a dummy data file with empty dict for parent initialization
        # We'll override the dataset behavior
        import tempfile
        import os
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump({}, temp_file)
        temp_file.close()
        dummy_data_path = temp_file.name
        
        try:
            super().__init__(
                task_name=task_name,
                chat_history_item_factory=chat_history_item_factory,
                data_file_path=dummy_data_path,
                max_round=max_round,
            )
        finally:
            # Clean up temp file
            if os.path.exists(dummy_data_path):
                os.unlink(dummy_data_path)
        
        # Override dataset with empty dict (tasks generated dynamically)
        self._set_dataset({})
        
        self.single_skill_task_generator = single_skill_task_generator
        self.random_seed = random_seed
        self.current_generated_task: Optional[DBBenchDatasetItem] = None

    def get_sample_index_list(self) -> list[SampleIndex]:
        """
        Return a dummy sample index list.
        In single-skill mode, we generate tasks dynamically, so we return a placeholder.
        """
        # Return a list with a single dummy index
        # The actual task will be generated in reset()
        return ["single_skill_task"]

    def reset(self, session: Session) -> None:
        """
        Reset and generate a new single-skill task.
        """
        # Do Validation and manage the state of the task
        assert session.sample_status == SampleStatus.INITIAL
        assert session.task_name == self.task_name
        assert self.current_sample_index is None
        assert self.__current_dataset_item is None
        
        # Generate a new single-skill task
        # Use session.sample_index as seed if it's numeric, otherwise use random_seed
        seed = None
        if isinstance(session.sample_index, (int, str)) and str(session.sample_index).isdigit():
            seed = int(session.sample_index)
        elif self.random_seed is not None:
            seed = self.random_seed
        
        # Generate task with random skill
        self.current_generated_task = self.single_skill_task_generator.generate_task(
            skill=None, random_seed=seed
        )
        
        self.current_sample_index = session.sample_index
        self.current_round = 0
        self.__current_dataset_item = self.current_generated_task
        session.sample_status = SampleStatus.RUNNING
        
        try:
            self._reset(session)
        except ContinualAgentBenchException as e:
            session.finish_reason = str(e)
            if isinstance(e, TaskEnvironmentException):
                session.sample_status = SampleStatus.TASK_ENVIRONMENT_ERROR
            else:
                raise TypeError(
                    f"Please handle {e.__class__.__name__} in Task.reset()."
                )
        except Exception as e:
            _ = TaskUnknownException(str(e))  # Record the exception
            session.sample_status = SampleStatus.TASK_UNKNOWN_ERROR
            session.finish_reason = str(TaskUnknownException.from_exception(e))

