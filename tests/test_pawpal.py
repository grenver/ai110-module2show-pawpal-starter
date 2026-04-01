"""
Unit tests for PawPal+ system logic.
Tests core behaviors of Task, Pet, and Owner classes.
"""

import pytest
from datetime import time
from pawpal_system import Owner, Pet, Task, Scheduler


class TestTaskCompletion:
    """Test task completion state management."""

    def test_mark_completed(self):
        """Verify that calling mark_completed() changes task status from False to True."""
        task = Task(
            task_id="task_001",
            pet_id="pet_001",
            description="Morning walk",
            category="exercise",
            duration_minutes=30,
            priority="high",
            completed=False,
        )
        # Before completion
        assert task.completed is False

        # Mark as completed
        task.mark_completed()

        # After completion
        assert task.completed is True

    def test_mark_incomplete(self):
        """Verify that mark_incomplete() resets task completed status."""
        task = Task(
            task_id="task_001",
            pet_id="pet_001",
            description="Morning walk",
            category="exercise",
            duration_minutes=30,
            priority="high",
            completed=True,
        )
        # Start as completed
        assert task.completed is True

        # Reset to incomplete
        task.mark_incomplete()

        # Should be incomplete now
        assert task.completed is False


class TestTaskAddition:
    """Test adding tasks to pets and tracking task counts."""

    def test_add_task_to_pet(self):
        """Verify that adding a task to a Pet increases that pet's task count."""
        pet = Pet(
            pet_id="pet_001",
            owner_id="owner_001",
            name="Mochi",
            species="dog",
            age_years=3,
        )
        # Initially no tasks
        assert len(pet.get_tasks()) == 0

        # Create and add a task
        task = Task(
            task_id="task_001",
            pet_id="pet_001",
            description="Morning walk",
            category="exercise",
            duration_minutes=30,
            priority="high",
        )
        pet.add_task(task)

        # Should now have 1 task
        assert len(pet.get_tasks()) == 1
        assert pet.get_tasks()[0].description == "Morning walk"

    def test_add_multiple_tasks_to_pet(self):
        """Verify that multiple tasks can be added and are tracked correctly."""
        pet = Pet(
            pet_id="pet_001",
            owner_id="owner_001",
            name="Whiskers",
            species="cat",
            age_years=5,
        )
        # Add three tasks
        for i in range(3):
            task = Task(
                task_id=f"task_{i:03d}",
                pet_id="pet_001",
                description=f"Task {i}",
                category="feeding",
                duration_minutes=10,
                priority="high",
            )
            pet.add_task(task)

        # Should have 3 tasks
        assert len(pet.get_tasks()) == 3

    def test_add_task_to_pet_validation(self):
        """Verify that adding a task with mismatched pet_id raises ValueError."""
        pet = Pet(
            pet_id="pet_001",
            owner_id="owner_001",
            name="Mochi",
            species="dog",
            age_years=3,
        )
        # Try to add a task with wrong pet_id
        task = Task(
            task_id="task_001",
            pet_id="pet_999",  # Wrong pet_id
            description="Morning walk",
            category="exercise",
            duration_minutes=30,
            priority="high",
        )
        # Should raise ValueError
        with pytest.raises(ValueError):
            pet.add_task(task)


class TestOwnerPetManagement:
    """Test owner management of multiple pets."""

    def test_owner_add_pet(self):
        """Verify that Owner can add pets and track them."""
        owner = Owner(
            owner_id="owner_001",
            name="Jordan",
            available_minutes_per_day=120,
        )
        pet = Pet(
            pet_id="pet_001",
            owner_id="owner_001",
            name="Mochi",
            species="dog",
            age_years=3,
        )
        # Initially no pets
        assert len(owner.pet_ids) == 0

        # Add pet
        owner.add_pet(pet)

        # Should now have 1 pet
        assert len(owner.pet_ids) == 1
        assert owner.get_pet("pet_001").name == "Mochi"

    def test_owner_get_all_tasks(self):
        """Verify that Owner aggregates tasks across all pets."""
        owner = Owner(
            owner_id="owner_001",
            name="Jordan",
            available_minutes_per_day=120,
        )
        # Create two pets
        dog = Pet(
            pet_id="pet_001",
            owner_id="owner_001",
            name="Mochi",
            species="dog",
            age_years=3,
        )
        cat = Pet(
            pet_id="pet_002",
            owner_id="owner_001",
            name="Whiskers",
            species="cat",
            age_years=5,
        )
        owner.add_pet(dog)
        owner.add_pet(cat)

        # Add tasks to each pet
        dog_task = Task(
            task_id="task_001",
            pet_id="pet_001",
            description="Dog walk",
            category="exercise",
            duration_minutes=30,
            priority="high",
        )
        cat_task = Task(
            task_id="task_002",
            pet_id="pet_002",
            description="Cat play",
            category="enrichment",
            duration_minutes=20,
            priority="high",
        )
        owner.add_task_to_pet("pet_001", dog_task)
        owner.add_task_to_pet("pet_002", cat_task)

        # Get all tasks
        all_tasks = owner.get_all_tasks()

        # Should have 2 tasks total from both pets
        assert len(all_tasks) == 2
        descriptions = [task.description for task in all_tasks]
        assert "Dog walk" in descriptions
        assert "Cat play" in descriptions


class TestScheduler:
    """Test scheduling logic."""

    def test_scheduler_builds_plan(self):
        """Verify that Scheduler can build a daily plan from owner's tasks."""
        owner = Owner(
            owner_id="owner_001",
            name="Jordan",
            available_minutes_per_day=100,
        )
        pet = Pet(
            pet_id="pet_001",
            owner_id="owner_001",
            name="Mochi",
            species="dog",
            age_years=3,
        )
        owner.add_pet(pet)

        # Add tasks
        task1 = Task(
            task_id="task_001",
            pet_id="pet_001",
            description="Walk",
            category="exercise",
            duration_minutes=30,
            priority="high",
        )
        task2 = Task(
            task_id="task_002",
            pet_id="pet_001",
            description="Feed",
            category="feeding",
            duration_minutes=10,
            priority="high",
        )
        owner.add_task_to_pet("pet_001", task1)
        owner.add_task_to_pet("pet_001", task2)

        # Create scheduler and build plan
        scheduler = Scheduler(owner)
        plan = scheduler.build_daily_plan()

        # Should have a plan with both tasks (40 min total fits in 100 min)
        assert len(plan) == 2
        assert sum(t.duration_minutes for t in plan) == 40

    def test_scheduler_respects_time_constraints(self):
        """Verify that Scheduler respects owner's available time."""
        owner = Owner(
            owner_id="owner_001",
            name="Jordan",
            available_minutes_per_day=30,  # Only 30 minutes
        )
        pet = Pet(
            pet_id="pet_001",
            owner_id="owner_001",
            name="Mochi",
            species="dog",
            age_years=3,
        )
        owner.add_pet(pet)

        # Add three tasks (30, 20, 20 min) = 70 min total needed
        task1 = Task(
            task_id="task_001",
            pet_id="pet_001",
            description="Long walk",
            category="exercise",
            duration_minutes=30,
            priority="high",
            is_mandatory=False,
        )
        task2 = Task(
            task_id="task_002",
            pet_id="pet_001",
            description="Play",
            category="enrichment",
            duration_minutes=20,
            priority="high",
            is_mandatory=False,
        )
        task3 = Task(
            task_id="task_003",
            pet_id="pet_001",
            description="Feed",
            category="feeding",
            duration_minutes=20,
            priority="high",
            is_mandatory=False,
        )
        owner.add_task_to_pet("pet_001", task1)
        owner.add_task_to_pet("pet_001", task2)
        owner.add_task_to_pet("pet_001", task3)

        # Build plan with only 30 minutes available
        scheduler = Scheduler(owner)
        plan = scheduler.build_daily_plan()

        # Should fit only one 30-minute task
        assert len(plan) == 1
        assert plan[0].duration_minutes == 30

    def test_sorting_correctness_chronological_order(self):
        """Verify tasks are sorted in chronological order by due_time."""
        owner = Owner(owner_id="owner_001", name="Jordan", available_minutes_per_day=120)
        pet = Pet(
            pet_id="pet_001",
            owner_id="owner_001",
            name="Mochi",
            species="dog",
            age_years=3,
        )
        owner.add_pet(pet)

        t1 = Task(
            task_id="task_001",
            pet_id="pet_001",
            description="Lunch feeding",
            category="feeding",
            duration_minutes=15,
            priority="medium",
            due_time=time(12, 0),
        )
        t2 = Task(
            task_id="task_002",
            pet_id="pet_001",
            description="Morning walk",
            category="exercise",
            duration_minutes=20,
            priority="high",
            due_time=time(8, 0),
        )
        t3 = Task(
            task_id="task_003",
            pet_id="pet_001",
            description="Evening meds",
            category="medical",
            duration_minutes=10,
            priority="high",
            due_time=time(18, 30),
        )

        owner.add_task_to_pet("pet_001", t1)
        owner.add_task_to_pet("pet_001", t2)
        owner.add_task_to_pet("pet_001", t3)

        scheduler = Scheduler(owner)
        sorted_tasks = scheduler.sort_by_time()

        assert [task.task_id for task in sorted_tasks] == ["task_002", "task_001", "task_003"]

    def test_recurrence_logic_daily_completion_creates_next_task(self):
        """Verify completing a daily task creates a new incomplete occurrence."""
        owner = Owner(owner_id="owner_001", name="Jordan", available_minutes_per_day=120)
        pet = Pet(
            pet_id="pet_001",
            owner_id="owner_001",
            name="Mochi",
            species="dog",
            age_years=3,
        )
        owner.add_pet(pet)

        daily_task = Task(
            task_id="task_daily",
            pet_id="pet_001",
            description="Daily walk",
            category="exercise",
            duration_minutes=30,
            priority="high",
            frequency="daily",
            due_time=time(9, 0),
        )
        owner.add_task_to_pet("pet_001", daily_task)

        scheduler = Scheduler(owner)
        next_task = scheduler.complete_task("task_daily")

        all_tasks = owner.get_all_tasks(include_completed=True)
        assert daily_task.completed is True
        assert next_task is not None
        assert next_task.task_id != "task_daily"
        assert next_task.description == "Daily walk"
        assert next_task.completed is False
        assert len(all_tasks) == 2

    def test_conflict_detection_flags_duplicate_times(self):
        """Verify scheduler detects duplicate due times and returns warnings."""
        owner = Owner(owner_id="owner_001", name="Jordan", available_minutes_per_day=120)
        dog = Pet(
            pet_id="pet_001",
            owner_id="owner_001",
            name="Mochi",
            species="dog",
            age_years=3,
        )
        cat = Pet(
            pet_id="pet_002",
            owner_id="owner_001",
            name="Whiskers",
            species="cat",
            age_years=5,
        )
        owner.add_pet(dog)
        owner.add_pet(cat)

        dog_task = Task(
            task_id="task_001",
            pet_id="pet_001",
            description="Walk",
            category="exercise",
            duration_minutes=20,
            priority="high",
            due_time=time(8, 0),
        )
        cat_task = Task(
            task_id="task_002",
            pet_id="pet_002",
            description="Feed",
            category="feeding",
            duration_minutes=10,
            priority="medium",
            due_time=time(8, 0),
        )
        owner.add_task_to_pet("pet_001", dog_task)
        owner.add_task_to_pet("pet_002", cat_task)

        scheduler = Scheduler(owner)
        warnings = scheduler.detect_time_conflicts()

        assert len(warnings) == 1
        assert "08:00" in warnings[0]
        assert "Mochi: Walk" in warnings[0]
        assert "Whiskers: Feed" in warnings[0]
