from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

TaskStatus = Literal["todo", "in_progress", "done"]


@dataclass
class Task:
    """Модель завдання (Варіант 14)."""
    id: int
    title: str
    description: str
    priority: int          # 1..10
    status: TaskStatus     # 'todo', 'in_progress', 'done'
    assignee: str
    estimated_hours: float
    days_until_due: int    # < 0 означає прострочене (overdue) завдання

    @property
    def is_overdue(self) -> bool:
        return self.days_until_due < 0 and self.status != "done"
