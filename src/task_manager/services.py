from __future__ import annotations
from functools import lru_cache
from task_manager.models import Task, TaskStatus
from task_manager.repositories import TaskRepository


class TaskService:
    """Сервіс керування завданнями з підтримкою кешування dashboard statistics
    та автоматичною інвалідацією кешу після мутації даних.
    """

    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository
        self._version: int = 1

        @lru_cache(maxsize=128)
        def _cached_dashboard(version: int, status_filter: str | None = None) -> dict[str, object]:
            return self._compute_dashboard_stats(status_filter)

        self._cached_dashboard = _cached_dashboard

    @property
    def version(self) -> int:
        return self._version

    def _invalidate_cache(self) -> None:
        """Інвалідація кешу шляхом інкременту версії та очищення lru_cache."""
        self._version += 1
        self._cached_dashboard.cache_clear()

    def create_task(
        self,
        title: str,
        description: str,
        priority: int,
        status: TaskStatus = "todo",
        assignee: str = "Unassigned",
        estimated_hours: float = 1.0,
        days_until_due: int = 7,
    ) -> Task:
        task = self.repository.add(
            title=title,
            description=description,
            priority=priority,
            status=status,
            assignee=assignee,
            estimated_hours=estimated_hours,
            days_until_due=days_until_due,
        )
        self._invalidate_cache()
        return task

    def change_status(self, task_id: int, new_status: TaskStatus) -> Task:
        task = self.repository.update_status(task_id, new_status)
        self._invalidate_cache()
        return task

    def change_priority(self, task_id: int, new_priority: int) -> Task:
        task = self.repository.update_priority(task_id, new_priority)
        self._invalidate_cache()
        return task

    def change_assignee(self, task_id: int, new_assignee: str) -> Task:
        task = self.repository.update_assignee(task_id, new_assignee)
        self._invalidate_cache()
        return task

    def filter_by_status(self, status: TaskStatus) -> list[Task]:
        return [t for t in self.repository.get_all() if t.status == status]

    def filter_by_priority(self, min_priority: int) -> list[Task]:
        return [t for t in self.repository.get_all() if t.priority >= min_priority]

    def search(self, query: str) -> list[Task]:
        q = query.lower()
        return [
            t for t in self.repository.get_all()
            if q in t.title.lower() or q in t.description.lower()
        ]

    def find_overdue_tasks(self) -> list[Task]:
        return [t for t in self.repository.get_all() if t.is_overdue]

    def count_completed_and_pending(self) -> dict[str, int]:
        tasks = self.repository.get_all()
        completed = sum(1 for t in tasks if t.status == "done")
        pending = len(tasks) - completed
        return {"completed": completed, "pending": pending, "total": len(tasks)}

    def _compute_dashboard_stats(self, status_filter: str | None = None) -> dict[str, object]:
        tasks = self.repository.get_all()
        if status_filter is not None:
            tasks = [t for t in tasks if t.status == status_filter]

        total = len(tasks)
        if total == 0:
            return {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "todo": 0,
                "overdue": 0,
                "avg_priority": 0.0,
                "total_hours": 0.0,
                "assignees": {},
            }

        completed = 0
        in_progress = 0
        todo = 0
        overdue = 0
        priority_sum = 0
        hours_sum = 0.0
        assignee_counts: dict[str, int] = {}

        for t in tasks:
            if t.status == "done":
                completed += 1
            elif t.status == "in_progress":
                in_progress += 1
            else:
                todo += 1
            if t.is_overdue:
                overdue += 1
            priority_sum += t.priority
            hours_sum += t.estimated_hours
            assignee_counts[t.assignee] = assignee_counts.get(t.assignee, 0) + 1

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "todo": todo,
            "overdue": overdue,
            "avg_priority": priority_sum / total,
            "total_hours": hours_sum,
            "assignees": assignee_counts,
        }

    def get_dashboard_statistics(self, status_filter: str | None = None) -> dict[str, object]:
        """Повертає кешовану статистику дашборду."""
        return self._cached_dashboard(self._version, status_filter)

    def cache_info(self):
        return self._cached_dashboard.cache_info()
