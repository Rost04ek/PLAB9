from __future__ import annotations
import math
import random
from functools import cache
import numpy as np
from task_manager.models import Task, TaskStatus

ASSIGNEES = ["Alice", "Bob", "Charlie", "Diana", "Evan", "Fiona", "George", "Hannah"]
STATUSES: list[TaskStatus] = ["todo", "in_progress", "done"]


def generate_tasks(count: int, seed: int = 42) -> list[Task]:
    """Генерація тестового набору завдань заданого розміру."""
    rng = random.Random(seed)
    tasks: list[Task] = []
    for i in range(1, count + 1):
        status = STATUSES[i % 3]
        priority = (i % 10) + 1
        assignee = ASSIGNEES[i % len(ASSIGNEES)]
        hours = round(rng.uniform(0.5, 40.0), 2)
        days_due = rng.randint(-15, 30)
        tasks.append(
            Task(
                id=i,
                title=f"Task #{i}: Implement module {i % 100}",
                description=f"Detailed specification and acceptance criteria for task {i}",
                priority=priority,
                status=status,
                assignee=assignee,
                estimated_hours=hours,
                days_until_due=days_due,
            )
        )
    return tasks


def extract_numeric_arrays(tasks: list[Task]) -> tuple[list[int], list[float], list[int]]:
    """Виділяє числові списки (priorities, estimated_hours, days_until_due) для числових бенчмарків."""
    priorities = [t.priority for t in tasks]
    hours = [t.estimated_hours for t in tasks]
    days_due = [t.days_until_due for t in tasks]
    return priorities, hours, days_due


def task_complexity_score(
    priority: int,
    estimated_hours: float,
    days_until_due: int,
    iterations: int = 40,
) -> float:
    """Важка CPU-bound функція оцінки складності та ризику завдання."""
    val = float(priority) * 1.5 + estimated_hours * 0.8 - float(days_until_due) * 0.3
    for _ in range(iterations):
        val = (
            math.sin(val) ** 2
            + math.cos(val) ** 2
            + math.sqrt(abs(val) + float(priority))
        )
    return val


def task_tuple_score(item: tuple[int, float, int]) -> float:
    """Обгортка для зручного виклику у map() для кортежу (priority, hours, days_due)."""
    return task_complexity_score(item[0], item[1], item[2], iterations=40)


def calculate_complexity_sequential(
    items: list[tuple[int, float, int]],
) -> list[float]:
    """Baseline: послідовний розрахунок складності для списку параметрів завдань."""
    return [task_tuple_score(item) for item in items]


def statistics_python(
    priorities: list[int],
    hours: list[float],
    days_due: list[int],
    statuses: list[str] | None = None,
) -> dict[str, float]:
    """Baseline: обчислення числових агрегатів за допомогою стандартних циклів Python."""
    n = len(priorities)
    if n == 0:
        return {
            "avg_priority": 0.0,
            "std_priority": 0.0,
            "avg_hours": 0.0,
            "std_hours": 0.0,
            "min_hours": 0.0,
            "max_hours": 0.0,
            "total_hours": 0.0,
            "urgency_index": 0.0,
        }

    sum_p = 0.0
    sum_h = 0.0
    min_h = hours[0]
    max_h = hours[0]
    urgency_sum = 0.0

    for i in range(n):
        p = float(priorities[i])
        h = hours[i]
        d = float(days_due[i])
        sum_p += p
        sum_h += h
        if h < min_h:
            min_h = h
        if h > max_h:
            max_h = h
        urgency_sum += (p * h) / (abs(d) + 1.0)

    avg_p = sum_p / n
    avg_h = sum_h / n

    var_p = 0.0
    var_h = 0.0
    for i in range(n):
        dp = float(priorities[i]) - avg_p
        dh = hours[i] - avg_h
        var_p += dp * dp
        var_h += dh * dh

    return {
        "avg_priority": avg_p,
        "std_priority": math.sqrt(var_p / n),
        "avg_hours": avg_h,
        "std_hours": math.sqrt(var_h / n),
        "min_hours": min_h,
        "max_hours": max_h,
        "total_hours": sum_h,
        "urgency_index": urgency_sum / n,
    }


def statistics_numpy(
    priorities: list[int] | np.ndarray,
    hours: list[float] | np.ndarray,
    days_due: list[int] | np.ndarray,
) -> dict[str, float]:
    """Векторизоване обчислення числових агрегатів за допомогою NumPy."""
    p_arr = np.asarray(priorities, dtype=np.float64)
    h_arr = np.asarray(hours, dtype=np.float64)
    d_arr = np.asarray(days_due, dtype=np.float64)

    if p_arr.size == 0:
        return {
            "avg_priority": 0.0,
            "std_priority": 0.0,
            "avg_hours": 0.0,
            "std_hours": 0.0,
            "min_hours": 0.0,
            "max_hours": 0.0,
            "total_hours": 0.0,
            "urgency_index": 0.0,
        }

    urgency = (p_arr * h_arr) / (np.abs(d_arr) + 1.0)

    return {
        "avg_priority": float(p_arr.mean()),
        "std_priority": float(p_arr.std()),
        "avg_hours": float(h_arr.mean()),
        "std_hours": float(h_arr.std()),
        "min_hours": float(h_arr.min()),
        "max_hours": float(h_arr.max()),
        "total_hours": float(h_arr.sum()),
        "urgency_index": float(urgency.mean()),
    }


def full_task_analytics_baseline(tasks: list[Task]) -> dict[str, object]:
    """Повна аналітика завдань для профілювання cProfile (фільтрація, сортування,
    підрахунок статусів, пошук overdue, статистика виконавців, числові метрики).
    """
    status_counts = {"todo": 0, "in_progress": 0, "done": 0}
    for t in tasks:
        status_counts[t.status] = status_counts.get(t.status, 0) + 1

    overdue_tasks = [t for t in tasks if t.is_overdue]
    high_priority = [t for t in tasks if t.priority >= 8]

    sorted_tasks = sorted(
        tasks,
        key=lambda x: (-x.priority, x.days_until_due, -x.estimated_hours),
    )

    assignee_stats: dict[str, dict[str, float]] = {}
    for t in tasks:
        st = assignee_stats.setdefault(
            t.assignee, {"count": 0.0, "hours": 0.0, "overdue": 0.0}
        )
        st["count"] += 1.0
        st["hours"] += t.estimated_hours
        if t.is_overdue:
            st["overdue"] += 1.0

    priorities, hours, days_due = extract_numeric_arrays(tasks)
    num_stats = statistics_python(priorities, hours, days_due)

    # Обчислення CPU-bound складності для підвибірки топ-5000 пріоритетних завдань
    sample_items = [
        (t.priority, t.estimated_hours, t.days_until_due)
        for t in sorted_tasks[: min(5000, len(sorted_tasks))]
    ]
    complexity_scores = calculate_complexity_sequential(sample_items)

    return {
        "status_counts": status_counts,
        "overdue_count": len(overdue_tasks),
        "high_priority_count": len(high_priority),
        "top_task_id": sorted_tasks[0].id if sorted_tasks else None,
        "assignee_stats": assignee_stats,
        "numeric_stats": num_stats,
        "avg_complexity": sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0.0,
    }


@cache
def cached_priority_weight(priority: int, days_until_due: int) -> float:
    """Кешований розрахунок ваги завдання за допомогою @cache."""
    return task_complexity_score(priority, 8.0, days_until_due, iterations=60)
