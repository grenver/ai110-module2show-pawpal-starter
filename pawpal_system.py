from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from typing import Any, Optional


@dataclass
class Owner:
    owner_id: str
    name: str
    available_minutes_per_day: int = 60
    preferences: dict[str, Any] = field(default_factory=dict)
    pet_ids: list[str] = field(default_factory=list)

    def update_preferences(self, preferences: dict[str, Any]) -> None:
        """Merge new preference values into the owner's preferences."""
        raise NotImplementedError

    def set_daily_availability(self, minutes: int) -> None:
        """Update how many minutes the owner can spend on pet care each day."""
        raise NotImplementedError


@dataclass
class Pet:
    pet_id: str
    owner_id: str
    name: str
    species: str
    age_years: int
    care_notes: list[str] = field(default_factory=list)

    def add_care_note(self, note: str) -> None:
        """Store a new care note for this pet."""
        raise NotImplementedError

    def get_profile_summary(self) -> str:
        """Return a concise profile summary for display in the UI."""
        raise NotImplementedError


@dataclass
class Task:
    task_id: str
    pet_id: str
    title: str
    category: str
    duration_minutes: int
    priority: str
    time_window: Optional[tuple[time, time]] = None
    is_mandatory: bool = False

    def is_feasible(self, available_minutes: int) -> bool:
        """Return True when this task can fit in the available time."""
        raise NotImplementedError

    def priority_score(self) -> int:
        """Convert textual priority into a numeric score for sorting tasks."""
        raise NotImplementedError


class DailyScheduler:
    def __init__(self, owner: Owner, pet: Pet) -> None:
        self.owner = owner
        self.pet = pet
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add one task to the scheduler pool."""
        raise NotImplementedError

    def rank_tasks(self) -> list[Task]:
        """Return tasks sorted by urgency/priority and constraints."""
        raise NotImplementedError

    def build_daily_plan(self) -> list[Task]:
        """Select and order tasks that fit the owner's daily constraints."""
        raise NotImplementedError

    def explain_plan(self, plan: list[Task]) -> str:
        """Describe why each task was included and how ordering was decided."""
        raise NotImplementedError
