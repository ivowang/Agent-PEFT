import random
import json
from typing import Optional, Mapping, Any
from src.tasks.instance.db_bench.task import (
    DBBenchDatasetItem,
    DBBenchSkillUtility,
    AnswerInfo,
    AnswerType,
    TableInfo,
    ColumnInfo,
    DBBenchType,
)
from src.typings import SampleIndex


class SingleSkillTaskGenerator:
    """
    Generator for single-skill tasks in DB environment.
    Each task focuses on one specific skill.
    """

    def __init__(
        self,
        skill_to_tasks_path: Optional[str] = None,
        skill_to_tasks_dict: Optional[Mapping[str, list[dict[str, Any]]]] = None,
    ):
        """
        Args:
            skill_to_tasks_path: Path to JSON file mapping skills to task templates
            skill_to_tasks_dict: Direct dictionary mapping skills to task templates
        """
        if skill_to_tasks_path:
            with open(skill_to_tasks_path, "r") as f:
                self.skill_to_tasks = json.load(f)
        elif skill_to_tasks_dict:
            self.skill_to_tasks = skill_to_tasks_dict
        else:
            # Create empty dict - will be populated by load_from_existing_data
            self.skill_to_tasks = {}

        # Validate skills
        for skill in self.skill_to_tasks.keys():
            if not DBBenchSkillUtility.is_valid_skill(skill):
                raise ValueError(f"Invalid skill: {skill}")

    @classmethod
    def load_from_existing_data(
        cls, data_file_path: str
    ) -> "SingleSkillTaskGenerator":
        """
        Load single-skill tasks from existing DB benchmark data.
        Filters tasks to only include single-skill tasks.
        """
        with open(data_file_path, "r") as f:
            data = json.load(f)

        skill_to_tasks: dict[str, list[dict[str, Any]]] = {}
        for key, entry in data.items():
            skill_list = entry.get("skill_list", [])
            # Only include single-skill tasks
            if len(skill_list) == 1:
                skill = skill_list[0]
                if skill not in skill_to_tasks:
                    skill_to_tasks[skill] = []
                skill_to_tasks[skill].append(entry)

        return cls(skill_to_tasks_dict=skill_to_tasks)

    def get_available_skills(self) -> list[str]:
        """Get list of available skills."""
        return list(self.skill_to_tasks.keys())

    def generate_task(
        self, skill: Optional[str] = None, random_seed: Optional[int] = None
    ) -> DBBenchDatasetItem:
        """
        Generate a single-skill task.

        Args:
            skill: Specific skill to generate task for. If None, randomly selects a skill.
            random_seed: Random seed for reproducibility.

        Returns:
            DBBenchDatasetItem with single skill
        """
        if random_seed is not None:
            random.seed(random_seed)

        # Select skill
        if skill is None:
            available_skills = self.get_available_skills()
            if len(available_skills) == 0:
                raise ValueError("No skills available for task generation")
            skill = random.choice(available_skills)

        if skill not in self.skill_to_tasks:
            raise ValueError(f"Skill {skill} not found in available skills")

        # Select random task template for this skill
        task_templates = self.skill_to_tasks[skill]
        if len(task_templates) == 0:
            raise ValueError(f"No task templates available for skill {skill}")

        task_template = random.choice(task_templates)

        # Construct DBBenchDatasetItem
        return self._construct_dataset_item(task_template, skill)

    def _construct_dataset_item(
        self, entry: dict[str, Any], skill: str
    ) -> DBBenchDatasetItem:
        """Construct DBBenchDatasetItem from entry dict."""
        # Construct answer_info
        answer_md5: Optional[str] = entry["answer_info"]["md5"]
        raw_answer_direct = entry["answer_info"]["direct"]
        answer_direct: Optional[list[DBBenchType.Row]]
        if raw_answer_direct is not None:
            answer_direct = []
            for answer_item in raw_answer_direct:
                assert isinstance(answer_item, list)
                answer_direct.append(tuple(answer_item))
        else:
            answer_direct = None

        if answer_md5 is not None:
            answer_type = AnswerType.MD5
        else:
            answer_type = AnswerType.DIRECT

        ground_truth_sql = entry["answer_info"]["sql"].strip()
        answer_info = AnswerInfo(
            answer_type=answer_type,
            answer_md5=answer_md5,
            answer_direct=answer_direct,
            ground_truth_sql=ground_truth_sql,
        )

        # Get database_name (same as table name)
        database_name = entry["table_info"]["name"]

        # Get table_info
        name = entry["table_info"]["name"]
        row_list = entry["table_info"]["row_list"]
        column_info_list: list[ColumnInfo] = []
        for column in entry["table_info"]["column_info_list"]:
            column_info_list.append(ColumnInfo(**column))
        table_info = TableInfo(
            name=name, row_list=row_list, column_info_list=column_info_list
        )

        # Get instruction
        question_prefix = entry["instruction"]
        question_suffix = (
            f"The name of this table is {table_info.name}, and the headers of this table are "
            f"{', '.join([column_info.name for column_info in column_info_list])}."
        )
        instruction = f"{question_prefix}\n{question_suffix}"

        # Construct DatasetItem with single skill
        dataset_item = DBBenchDatasetItem(
            instruction=instruction,
            answer_info=answer_info,
            database_name=database_name,
            table_info=table_info,
            skill_list=[skill],  # Single skill only
        )

        return dataset_item

