import threading
from queue import Queue, Empty
import time, uuid
from typing import Optional, Dict
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger('uvicorn.error')
class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"

class TaskResult:
    def __init__(self, task_id, user_id=None, details=None):
        self.task_id = task_id
        self.status = TaskStatus.PENDING
        self.result: Optional[str] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.user_id = user_id
        self.details = details

TASK_CACHE = {}

def create_task(task_id, user_id=None, details=None):
    TASK_CACHE[task_id] = TaskResult(task_id, user_id,details)
    logger.info(f"Task {task_id} created for user {user_id}")
    return TASK_CACHE[task_id]

def update_task(task_id, **kwargs):
    task = TASK_CACHE.get(task_id)
    if not task:
        return
    for key, value in kwargs.items():
        setattr(task, key, value)
    task.updated_at = datetime.now()

def get_task(task_id):
    return TASK_CACHE.get(task_id)

class TaskManager:
    def __init__(self, num_workers=2):
        self.queue = Queue()
        self.running = True
        self.workers = {}
        self.num_workers = num_workers

    def worker(self, worker_id):
        while self.running:
            try:
                task = self.queue.get(timeout=1.0)
                print(f"[{worker_id}] Running task...")
                if asyncio.iscoroutinefunction(task):
                    asyncio.run(task())
                elif asyncio.iscoroutine(task):
                    asyncio.run(task)
                else:
                    task()
                self.queue.task_done()
            except Empty:
                continue
            except Exception as e:
                print(f"[{worker_id}] Error:", e)
        print(f"[{worker_id}] Shutting down.")

    def start_workers(self):
        for i in range(self.num_workers):
            thread = threading.Thread(target=self.worker, args=(f"worker_{i}",), daemon=True)
            thread.start()
            self.workers[f"worker_{i}"] = thread
            print(f"Started worker_{i}")

    def add_task(self, task):
        self.queue.put(task)

    def shutdown(self):
        self.running = False
        for thread in self.workers.values():
            thread.join(timeout=1)
