from __future__ import annotations
from task_manager.services import TaskService


class TaskAPI:
    """Фасад REST-подібного API для взаємодії з TaskService."""

    def __init__(self, service: TaskService) -> None:
        self.service = service

    def get_dashboard(self, status_filter: str | None = None) -> dict[str, object]:
        return {
            "status": 200,
            "data": self.service.get_dashboard_statistics(status_filter),
        }

    def post_task(self, payload: dict[str, object]) -> dict[str, object]:
        task = self.service.create_task(
            title=str(payload["title"]),
            description=str(payload.get("description", "")),
            priority=int(payload.get("priority", 5)),
            status=str(payload.get("status", "todo")),  # type: ignore[arg-type]
            assignee=str(payload.get("assignee", "Unassigned")),
            estimated_hours=float(payload.get("estimated_hours", 1.0)),
            days_until_due=int(payload.get("days_until_due", 7)),
        )
        return {"status": 201, "task_id": task.id}
