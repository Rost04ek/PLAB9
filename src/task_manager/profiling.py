from __future__ import annotations
import cProfile
import io
import pstats
import tracemalloc
from pathlib import Path
import numpy as np
from task_manager.analytics import (
    extract_numeric_arrays,
    full_task_analytics_baseline,
    generate_tasks,
    statistics_numpy,
    statistics_python,
)


def run_cprofile_analysis(
    task_count: int = 100_000,
    profile_output_path: Path | None = None,
) -> str:
    """Виконує профілювання базової аналітики через cProfile і повертає текстовий звіт."""
    tasks = generate_tasks(task_count)
    profiler = cProfile.Profile()

    profiler.enable()
    full_task_analytics_baseline(tasks)
    profiler.disable()

    if profile_output_path is not None:
        profile_output_path.parent.mkdir(parents=True, exist_ok=True)
        profiler.dump_stats(str(profile_output_path))

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats("cumulative")
    stats.print_stats(15)
    return stream.getvalue()


def run_memory_analysis(task_count: int = 100_000) -> dict[str, float | list[str]]:
    """Аналізує використання пам'яті через tracemalloc для списку об'єктів Task та масивів NumPy."""
    tracemalloc.start()
    tasks = generate_tasks(task_count)
    priorities, hours, days_due = extract_numeric_arrays(tasks)
    _ = statistics_python(priorities, hours, days_due)

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")
    top_lines = [str(stat) for stat in top_stats[:5]]

    current_py, peak_py = tracemalloc.get_traced_memory()
    del tasks, priorities, hours, days_due
    tracemalloc.stop()

    tracemalloc.start()
    tasks_np = generate_tasks(task_count)
    p_arr = np.array([t.priority for t in tasks_np], dtype=np.float64)
    h_arr = np.array([t.estimated_hours for t in tasks_np], dtype=np.float64)
    d_arr = np.array([t.days_until_due for t in tasks_np], dtype=np.float64)
    del tasks_np
    _ = statistics_numpy(p_arr, h_arr, d_arr)
    current_np, peak_np = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "python_current_mb": current_py / (1024 * 1024),
        "python_peak_mb": peak_py / (1024 * 1024),
        "numpy_current_mb": current_np / (1024 * 1024),
        "numpy_peak_mb": peak_np / (1024 * 1024),
        "top_allocations": top_lines,
    }


if __name__ == "__main__":
    print("=== cProfile Report (100,000 tasks) ===")
    print(run_cprofile_analysis(100_000))
    print("=== tracemalloc Memory Report (100,000 tasks) ===")
    mem = run_memory_analysis(100_000)
    for k, v in mem.items():
        print(f"{k}: {v}")
