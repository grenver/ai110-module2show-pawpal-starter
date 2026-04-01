from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import time
from typing import Any, Optional


def _default_preferences() -> dict[str, Any]:
    """Return a default preferences dictionary."""
    return {}


def _default_pet_ids() -> list[str]:
    """Return a default empty list of pet IDs."""
    return []


def _default_pets() -> dict[str, Pet]:
    """Return a default pet registry mapping."""
    return {}


def _default_care_notes() -> list[str]:
    """Return a default empty list of pet care notes."""
    return []


def _default_tasks() -> list[Task]:
    """Return a default empty list of tasks."""
    return []


@dataclass
class Owner:
    owner_id: str
    name: str
    available_minutes_per_day: int = 60
    preferences: dict[str, Any] = field(default_factory=_default_preferences)
    pet_ids: list[str] = field(default_factory=_default_pet_ids)
    pets: dict[str, Pet] = field(default_factory=_default_pets)

    def update_preferences(self, preferences: dict[str, Any]) -> None:
        """Merge new preference values into the owner's preferences."""
        self.preferences.update(preferences)

    def set_daily_availability(self, minutes: int) -> None:
        """Update how many minutes the owner can spend on pet care each day."""
        if minutes <= 0:
            raise ValueError("available minutes must be positive")
        self.available_minutes_per_day = minutes

    def add_pet(self, pet: Pet) -> None:
        """Attach a pet to this owner and keep owner/pet linkage consistent."""
        if pet.owner_id != self.owner_id:
            raise ValueError("pet owner_id does not match owner")
        self.pets[pet.pet_id] = pet
        if pet.pet_id not in self.pet_ids:
            self.pet_ids.append(pet.pet_id)

    def get_pet(self, pet_id: str) -> Pet:
        """Fetch one pet by ID."""
        if pet_id not in self.pets:
            raise KeyError(f"pet '{pet_id}' not found")
        return self.pets[pet_id]

    def add_task_to_pet(self, pet_id: str, task: Task) -> None:
        """Add a task to a specific pet."""
        pet = self.get_pet(pet_id)
        pet.add_task(task)

    def get_all_tasks(self, include_completed: bool = True) -> list[Task]:
        """Return tasks across all pets owned by this owner."""
        all_tasks: list[Task] = []
        for pet in self.pets.values():
            all_tasks.extend(pet.get_tasks(include_completed=include_completed))
        return all_tasks


@dataclass
class Pet:
    pet_id: str
    owner_id: str
    name: str
    species: str
    age_years: int
    care_notes: list[str] = field(default_factory=_default_care_notes)
    tasks: list[Task] = field(default_factory=_default_tasks)

    def add_care_note(self, note: str) -> None:
        """Store a new care note for this pet."""
        if note.strip():
            self.care_notes.append(note.strip())

    def get_profile_summary(self) -> str:
        """Return a concise profile summary for display in the UI."""
        return f"{self.name} ({self.species}, {self.age_years}y)"

    def add_task(self, task: Task) -> None:
        """Assign a task to this pet."""
        if task.pet_id != self.pet_id:
            raise ValueError("task pet_id does not match pet")
        self.tasks.append(task)

    def get_tasks(self, include_completed: bool = True) -> list[Task]:
        """Return this pet's tasks with optional completion filtering."""
        if include_completed:
            return list(self.tasks)
        return [task for task in self.tasks if not task.completed]


@dataclass
class Task:
    task_id: str
    pet_id: str
    description: str
    category: str
    duration_minutes: int
    priority: str
    frequency: str = "daily"
    due_time: Optional[time] = None
    time_window: Optional[tuple[time, time]] = None
    is_mandatory: bool = False
    completed: bool = False

    def mark_completed(self) -> None:
        """Mark the task as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Reset completion state for the task."""
        self.completed = False

    def is_feasible(self, available_minutes: int) -> bool:
        """Return True when this task can fit in the available time."""
        return self.duration_minutes <= available_minutes

    def priority_score(self) -> int:
        """Convert textual priority into a numeric score for sorting tasks."""
        priority_to_score = {"low": 1, "medium": 2, "high": 3}
        return priority_to_score.get(self.priority.lower(), 0)


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        """Initialize a scheduler bound to a specific owner."""
        self.owner = owner
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add one task to the scheduler pool."""
        self.owner.add_task_to_pet(task.pet_id, task)
        self.tasks.append(task)

    def retrieve_tasks_from_owner(self, include_completed: bool = False) -> list[Task]:
        """Pull all tasks from the owner's pets into scheduler memory."""
        self.tasks = self.owner.get_all_tasks(include_completed=include_completed)
        return list(self.tasks)

    @staticmethod
    def _coerce_time_value(value: Any) -> time:
        """Convert mixed time inputs into a comparable ``datetime.time`` value.

        Accepts native ``time`` objects and ``"HH:MM"`` strings. Invalid or
        missing values are mapped to ``time.max`` so they naturally sort last.
        """
        if value is None:
            return time.max
        if isinstance(value, time):
            return value
        if isinstance(value, str):
            try:
                hour_str, minute_str = value.split(":", maxsplit=1)
                return time(int(hour_str), int(minute_str))
            except (ValueError, TypeError):
                return time.max
        return time.max

    def sort_by_time(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Return tasks ordered by due time with deterministic tie-breaks.

        The method supports due times stored as ``time`` objects or ``HH:MM``
        strings and then applies tie-breakers in this order:
        1) higher priority first, 2) task_id ascending.

        Args:
            tasks: Optional subset of tasks to sort. When omitted, scheduler
                memory is used; if empty, tasks are retrieved from the owner.

        Returns:
            A new list of tasks sorted from earliest to latest due time.
        """
        selected_tasks = list(tasks) if tasks is not None else list(self.tasks)
        if not selected_tasks:
            selected_tasks = self.retrieve_tasks_from_owner(include_completed=False)

        return sorted(
            selected_tasks,
            key=lambda task: (
                self._coerce_time_value(task.due_time),
                -task.priority_score(),
                task.task_id,
            ),
        )

    def filter_tasks(
        self,
        tasks: Optional[list[Task]] = None,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> list[Task]:
        """Filter tasks by completion state and/or pet name.

        Args:
            tasks: Optional source tasks. Falls back to scheduler memory and
                then owner tasks when no tasks are currently loaded.
            completed: If provided, keeps only tasks whose completed flag
                matches this value.
            pet_name: If provided, keeps only tasks assigned to a pet with an
                exact case-insensitive name match.

        Returns:
            A filtered task list preserving the original order.
        """
        selected_tasks = list(tasks) if tasks is not None else list(self.tasks)
        if not selected_tasks:
            selected_tasks = self.retrieve_tasks_from_owner(include_completed=True)

        filtered = selected_tasks

        if completed is not None:
            filtered = [task for task in filtered if task.completed is completed]

        if pet_name is not None:
            target = pet_name.strip().lower()
            filtered = [
                task
                for task in filtered
                if self.owner.get_pet(task.pet_id).name.lower() == target
            ]

        return filtered

    def detect_time_conflicts(self, tasks: Optional[list[Task]] = None) -> list[str]:
        """Detect exact due-time collisions and return warning messages.

        This is a lightweight conflict check: it only flags tasks that share
        the exact same due time and intentionally does not model duration
        overlaps or interval arithmetic.

        Args:
            tasks: Optional source tasks. Falls back to scheduler memory and
                then owner tasks when none are loaded.

        Returns:
            A list of human-readable warning strings. The list is empty when
            no exact-time conflicts are found.
        """
        selected_tasks = list(tasks) if tasks is not None else list(self.tasks)
        if not selected_tasks:
            selected_tasks = self.retrieve_tasks_from_owner(include_completed=False)

        tasks_by_time: dict[time, list[Task]] = defaultdict(list)
        for task in selected_tasks:
            due = task.due_time
            if due is None:
                continue
            tasks_by_time[due].append(task)

        warnings: list[str] = []
        for due, grouped_tasks in sorted(tasks_by_time.items(), key=lambda item: item[0]):
            if len(grouped_tasks) < 2:
                continue

            task_labels = [
                f"{self.owner.get_pet(task.pet_id).name}: {task.description}"
                for task in grouped_tasks
            ]
            warnings.append(
                (
                    f"Warning: {len(grouped_tasks)} tasks are scheduled at "
                    f"{due.strftime('%H:%M')} -> "
                    f"{'; '.join(task_labels)}"
                )
            )

        return warnings

    def rank_tasks(self) -> list[Task]:
        """Return tasks sorted by urgency/priority and constraints."""
        if not self.tasks:
            self.retrieve_tasks_from_owner(include_completed=False)

        def due_time_key(task: Task) -> time:
            # Keep tasks without a due time toward the end.
            return task.due_time if task.due_time is not None else time.max

        return sorted(
            self.tasks,
            key=lambda task: (
                not task.is_mandatory,
                -task.priority_score(),
                due_time_key(task),
            ),
        )

    def build_daily_plan(self) -> list[Task]:
        """Select and order tasks that fit the owner's daily constraints."""
        remaining_minutes = self.owner.available_minutes_per_day
        selected: list[Task] = []

        for task in self.rank_tasks():
            if task.completed:
                continue
            if task.is_feasible(remaining_minutes):
                selected.append(task)
                remaining_minutes -= task.duration_minutes

        return selected

    def explain_plan(self, plan: list[Task]) -> str:
        """Describe why each task was included and how ordering was decided."""
        if not plan:
            return "No tasks were scheduled."

        lines: list[str] = ["Today's plan was built by priority, required status, and available time:"]
        for index, task in enumerate(plan, start=1):
            required_tag = "mandatory" if task.is_mandatory else "optional"
            lines.append(
                (
                    f"{index}. {task.description} "
                    f"({task.duration_minutes} min, {task.priority} priority, {required_tag})"
                )
            )
        return "\n".join(lines)


class DailyScheduler(Scheduler):
    """Compatibility alias while transitioning naming to Scheduler."""

    pass
