from __future__ import annotations
from task_manager.analytics import generate_tasks
from task_manager.profiling import run_cprofile_analysis, run_memory_analysis
from task_manager.repositories import TaskRepository
from task_manager.services import TaskService


def main() -> None:
    print("Ініціалізація системи керування завданнями (Варіант 14)...")
    initial_tasks = generate_tasks(100_000)
    repo = TaskRepository(initial_tasks)
    service = TaskService(repo)

    stats = service.get_dashboard_statistics()
    print(f"Усього завдань: {stats['total']}, виконано: {stats['completed']}, прострочено: {stats['overdue']}")

    print("\nЗапуск cProfile...")
    print(run_cprofile_analysis(100_000))

    print("\nЗапуск tracemalloc...")
    mem = run_memory_analysis(100_000)
    print(f"Peak memory (Python objects): {mem['python_peak_mb']:.2f} MB")


if __name__ == "__main__":
    main()
