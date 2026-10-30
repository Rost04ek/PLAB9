from __future__ import annotations
from task_manager.models import Task, TaskStatus


class TaskRepository:
    """Репозиторій для зберігання та керування завданнями в пам'яті."""

    def __init__(self, initial_tasks: list[Task] | None = None) -> None:
        self._tasks: dict[int, Task] = {}
        self._next_id: int = 1
        if initial_tasks:
            for t in initial_tasks:
                self._tasks[t.id] = t
                if t.id >= self._next_id:
                    self._next_id = t.id + 1

    def add(
        self,
        title: str,
        description: str,
        priority: int,
        status: TaskStatus = "todo",
        assignee: str = "Unassigned",
        estimated_hours: float = 1.0,
        days_until_due: int = 7,
    ) -> Task:
        task = Task(
            id=self._next_id,
            title=title,
            description=description,
            priority=priority,
            status=status,
            assignee=assignee,
            estimated_hours=estimated_hours,
            days_until_due=days_until_due,
        )
        self._tasks[task.id] = task
        self._next_id += 1
        return task

    def get_by_id(self, task_id: int) -> Task | None:
        return self._tasks.get(task_id)

    def get_all(self) -> list[Task]:
        return list(self._tasks.values())

    def update_status(self, task_id: int, new_status: TaskStatus) -> Task:
        if task_id not in self._tasks:
            raise KeyError(f"Task #{task_id} not found")
        self._tasks[task_id].status = new_status
        return self._tasks[task_id]

    def update_priority(self, task_id: int, new_priority: int) -> Task:
        if task_id not in self._tasks:
            raise KeyError(f"Task #{task_id} not found")
        self._tasks[task_id].priority = new_priority
        return self._tasks[task_id]

    def update_assignee(self, task_id: int, new_assignee: str) -> Task:
        if task_id not in self._tasks:
            raise KeyError(f"Task #{task_id} not found")
        self._tasks[task_id].assignee = new_assignee
        return self._tasks[task_id]
