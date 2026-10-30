from __future__ import annotations
import json
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import Process, Queue
from pathlib import Path
from threading import Lock, Thread
from task_manager.analytics import task_tuple_score
from task_manager.models import Task


# =====================================================================
# 1. Низькорівневі потоки (threading.Thread) та процеси (multiprocessing.Process)
# =====================================================================

def _thread_worker(
    chunk: list[tuple[int, float, int]],
    output: list[float],
    lock: Lock,
) -> None:
    local_res = [task_tuple_score(item) for item in chunk]
    with lock:
        output.extend(local_res)


def run_manual_threads(
    items: list[tuple[int, float, int]],
    num_threads: int = 4,
) -> list[float]:
    """Демонстрація створення та запуску потоків через threading.Thread."""
    if not items:
        return []
    chunk_size = max(1, (len(items) + num_threads - 1) // num_threads)
    threads: list[Thread] = []
    output: list[float] = []
    lock = Lock()

    for i in range(0, len(items), chunk_size):
        chunk = items[i : i + chunk_size]
        t = Thread(target=_thread_worker, args=(chunk, output, lock))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return output


def _process_worker(chunk: list[tuple[int, float, int]], queue: Queue) -> None:
    queue.put([task_tuple_score(item) for item in chunk])


def run_manual_processes(
    items: list[tuple[int, float, int]],
    num_processes: int = 2,
) -> list[float]:
    """Демонстрація створення окремих процесів через multiprocessing.Process."""
    if not items:
        return []
    chunk_size = max(1, (len(items) + num_processes - 1) // num_processes)
    processes: list[Process] = []
    queue: Queue = Queue()

    for i in range(0, len(items), chunk_size):
        chunk = items[i : i + chunk_size]
        p = Process(target=_process_worker, args=(chunk, queue))
        processes.append(p)
        p.start()

    results: list[float] = []
    for _ in processes:
        results.extend(queue.get())

    for p in processes:
        p.join()

    return results


# =====================================================================
# 2. Високорівневі виконавці: ThreadPoolExecutor та ProcessPoolExecutor
# =====================================================================

def calculate_complexity_threads(
    items: list[tuple[int, float, int]],
    workers: int = 4,
) -> list[float]:
    """Обчислення CPU-bound задачі за допомогою ThreadPoolExecutor."""
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(task_tuple_score, items))


def calculate_complexity_processes(
    items: list[tuple[int, float, int]],
    workers: int = 4,
    chunksize: int = 250,
) -> list[float]:
    """Обчислення CPU-bound задачі за допомогою ProcessPoolExecutor."""
    with ProcessPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(task_tuple_score, items, chunksize=chunksize))


# =====================================================================
# 3. I/O-bound експеримент: читання та запис батчів завдань із JSON-файлів
# =====================================================================

def save_tasks_to_files(
    tasks: list[Task],
    directory: Path,
    num_files: int = 16,
) -> list[Path]:
    """Зберігає каталог завдань у декілька JSON-файлів для I/O-bound тестування."""
    directory.mkdir(parents=True, exist_ok=True)
    chunk_size = max(1, (len(tasks) + num_files - 1) // num_files)
    paths: list[Path] = []

    for idx, start in enumerate(range(0, len(tasks), chunk_size)):
        chunk = tasks[start : start + chunk_size]
        file_path = directory / f"tasks_part_{idx:02d}.json"
        payload = [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "priority": t.priority,
                "status": t.status,
                "assignee": t.assignee,
                "estimated_hours": t.estimated_hours,
                "days_until_due": t.days_until_due,
            }
            for t in chunk
        ]
        file_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        paths.append(file_path)

    return paths


def load_tasks_from_file(path: Path) -> list[Task]:
    """Завантажує список завдань із одного JSON-файлу."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        Task(
            id=item["id"],
            title=item["title"],
            description=item["description"],
            priority=item["priority"],
            status=item["status"],
            assignee=item["assignee"],
            estimated_hours=item["estimated_hours"],
            days_until_due=item["days_until_due"],
        )
        for item in raw
    ]


def load_tasks_sequential(paths: list[Path]) -> list[Task]:
    """Послідовне завантаження завдань із набору файлів."""
    all_tasks: list[Task] = []
    for p in paths:
        all_tasks.extend(load_tasks_from_file(p))
    return all_tasks


def load_tasks_threaded(paths: list[Path], workers: int = 8) -> list[Task]:
    """Паралельне завантаження завдань із декількох джерел через ThreadPoolExecutor."""
    all_tasks: list[Task] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for batch in executor.map(load_tasks_from_file, paths):
            all_tasks.extend(batch)
    return all_tasks


# =====================================================================
# 4. Демонстрація Race Condition та її виправлення за допомогою Lock
# =====================================================================

class SharedTaskCounter:
    """Спільний лічильник виконаних завдань для демонстрації race condition та Lock."""

    def __init__(self) -> None:
        self.completed_count: int = 0
        self.lock = Lock()

    def increment_unsafe(self, iterations: int) -> None:
        """Небезпечне оновлення стану без синхронізації (спричиняє race condition)."""
        for _ in range(iterations):
            current = self.completed_count
            # Штучне перемикання контексту або мікро-затримка в циклі Python
            self.completed_count = current + 1

    def increment_safe(self, iterations: int) -> None:
        """Безпечне оновлення спільного стану з використанням Lock."""
        for _ in range(iterations):
            with self.lock:
                self.completed_count += 1


def simulate_race_condition(num_threads: int = 8, increments_per_thread: int = 25_000) -> tuple[int, int]:
    """Запускає потоки без Lock та з Lock, повертаючи (unsafe_result, safe_result)."""
    unsafe_counter = SharedTaskCounter()
    safe_counter = SharedTaskCounter()

    def unsafe_worker() -> None:
        for _ in range(increments_per_thread):
            val = unsafe_counter.completed_count
            val += 1
            unsafe_counter.completed_count = val

    threads_unsafe = [Thread(target=unsafe_worker) for _ in range(num_threads)]
    for t in threads_unsafe:
        t.start()
    for t in threads_unsafe:
        t.join()

    threads_safe = [
        Thread(target=safe_counter.increment_safe, args=(increments_per_thread,))
        for _ in range(num_threads)
    ]
    for t in threads_safe:
        t.start()
    for t in threads_safe:
        t.join()

    return unsafe_counter.completed_count, safe_counter.completed_count
