import threading
import queue
import logging
from typing import Dict, Optional, Callable
import time

logger = logging.getLogger(__name__)


class ExperimentQueue:

    def __init__(self, max_concurrent_experiments: int = 4):
        self.max_concurrent_experiments = max_concurrent_experiments
        self._queue = queue.Queue()
        self._running_experiments: Dict[str, dict] = {}  # {exp_id: {"thread": thread, "cancel_flag": Event}}
        self._lock = threading.Lock()
        self._dispatcher_thread = None
        self._shutdown = threading.Event()
        logger.info(f"ExperimentQueue initialized with max_concurrent_experiments={max_concurrent_experiments}")

    def start(self):
        """Start the queue dispatcher thread."""
        if self._dispatcher_thread is None or not self._dispatcher_thread.is_alive():
            self._shutdown.clear()
            self._dispatcher_thread = threading.Thread(
                target=self._dispatch_experiments,
                name="experiment-queue-dispatcher",
                daemon=True
            )
            self._dispatcher_thread.start()
            logger.info("Experiment queue dispatcher started")

    def stop(self):
        """Stop the queue dispatcher and wait for it to finish."""
        logger.info("Stopping experiment queue dispatcher...")
        self._shutdown.set()
        if self._dispatcher_thread:
            self._dispatcher_thread.join(timeout=5)
        logger.info("Experiment queue dispatcher stopped")

    def enqueue(self, exp_id: str, execute_fn: Callable, cancel_flag: threading.Event):
        """
        Add an experiment to the queue.

        Args:
            exp_id: Unique experiment identifier
            execute_fn: Function to execute the experiment (no arguments)
            cancel_flag: Threading event for cancellation
        """
        with self._lock:
            queue_position = self._queue.qsize() + 1
            logger.info(f"Enqueuing experiment {exp_id} (queue position: {queue_position})")
            self._queue.put({
                "exp_id": exp_id,
                "execute_fn": execute_fn,
                "cancel_flag": cancel_flag,
                "enqueued_at": time.time()
            })

    def get_queue_status(self) -> dict:
        """
        Get current queue status.

        Returns: 
            Dictionary with queue statistics
        """
        with self._lock:
            return {
                "running_experiments": len(self._running_experiments),
                "queued_experiments": self._queue.qsize(),
                "max_concurrent_experiments": self.max_concurrent_experiments,
                "running_experiment_ids": list(self._running_experiments.keys())
            }

    def get_experiment_position(self, exp_id: str) -> Optional[int]:
        """
        Get position of experiment in queue.

        Args:
           exp_id = Experiment identifier

        Returns:
            Queue position (1-indexed) or None if not in queue, 0 if running
        """
        with self._lock:
            # Check if running
            if exp_id in self._running_experiments:
                return 0  # 0 means currently running

            # Check queue position
            queue_items = list(self._queue.queue)
            for i, item in enumerate(queue_items):
                if item["exp_id"] == exp_id:
                    return i + 1

            return None

    def _dispatch_experiments(self):
        """Background thread that dispatches queued experiments when slots are available."""
        logger.info("Experiment dispatcher thread started")
        while not self._shutdown.is_set():
            try:
                # Clean up completed experiments
                self._cleanup_completed_experiments()

                # Check if we can run more experiments
                with self._lock:
                    running_count = len(self._running_experiments)
                    available_slots = self.max_concurrent_experiments - running_count

                if available_slots > 0 and not self._queue.empty():
                    try:
                        # Get next experiment from queue (with timeout to allow shutdown check)
                        experiment_item = self._queue.get(timeout=1)
                        exp_id = experiment_item["exp_id"]
                        execute_fn = experiment_item["execute_fn"]
                        cancel_flag = experiment_item["cancel_flag"]

                        # Check if experiment was cancelled while in queue
                        if cancel_flag.is_set():
                            logger.info(f"Experiment {exp_id} was cancelled while in queue, skipping")
                            self._queue.task_done()
                            continue

                        # Start the experiment
                        wait_time = time.time() - experiment_item["enqueued_at"]
                        logger.info(f"Starting experiment {exp_id} (waited {wait_time:.2f}s in queue)")

                        thread = threading.Thread(
                            target=self._execute_experiment,
                            args=(exp_id, execute_fn),
                            name=f"exp-run-{exp_id}",
                            daemon=False
                        )

                        with self._lock:
                            self._running_experiments[exp_id] = {
                                "thread": thread,
                                "cancel_flag": cancel_flag,
                                "started_at": time.time()
                            }

                        thread.start()
                        self._queue.task_done()

                    except queue.Empty:
                        # Timeout on queue.get, continue loop
                        pass
                else:
                    # No available slots or empty queue, wait a bit
                    time.sleep(0.5)

            except Exception as e:
                logger.exception(f"Error in experiment dispatcher: {e}")
                time.sleep(1)

        logger.info("Experiment dispatcher thread stopped")

    def _execute_experiment(self, exp_id: str, execute_fn: Callable):
        """
        Execute an experiment and clean up after completion.

        Args:
            exp_id: Experiment identifier
            execute_fn: Function to execute
        """
        try:
            execute_fn()
        except Exception as e:
            logger.exception(f"Experiment {exp_id} execution failed: {e}")
        finally:
            # Clean up from running experiments
            with self._lock:
                if exp_id in self._running_experiments:
                    runtime = time.time() - self._running_experiments[exp_id]["started_at"]
                    del self._running_experiments[exp_id]
                    logger.info(f"Experiment {exp_id} completed (runtime: {runtime:.2f}s)")

    def _cleanup_completed_experiments(self):
        """Remove completed experiments from running registry."""
        with self._lock:
            completed_exp_ids = []
            for exp_id, exp_info in self._running_experiments.items():
                thread = exp_info["thread"]
                if not thread.is_alive():
                    completed_exp_ids.append(exp_id)

            for exp_id in completed_exp_ids:
                runtime = time.time() - self._running_experiments[exp_id]["started_at"]
                del self._running_experiments[exp_id]
                logger.info(f"Cleaned up completed experiment {exp_id} (runtime: {runtime:.2f}s)")

    def cancel_experiment(self, exp_id: str) -> bool:
        """
        Cancel an experiment (sets its cancel flag).

        Args:
            exp_id: Experiment identifier

        Returns:
            True if experiment was found and cancelled, False otherwise
        """
        with self._lock:
            if exp_id in self._running_experiments:
                logger.info(f"Cancelling running experiment {exp_id}")
                self._running_experiments[exp_id]["cancel_flag"].set()
                return True

            # Check if it's in the queue
            queue_items = list(self._queue.queue)
            for item in queue_items:
                if item["exp_id"] == exp_id:
                    logger.info(f"Cancelling queued experiment {exp_id}")
                    item["cancel_flag"].set()
                    return True

        logger.warning(f"Experiment {exp_id} not found in queue or running experiments")
        return False


# Global experiment queue instance
_experiment_queue: Optional[ExperimentQueue] = None


def get_experiment_queue(max_concurrent: int = 4) -> ExperimentQueue:
    """
    Get or create the global experiment queue instance.

    Args:
        max_concurrent: Maximum concurrent experiments (only used on first call)

    Returns:
        ExperimentQueue instance
    """
    global _experiment_queue
    if _experiment_queue is None:
        _experiment_queue = ExperimentQueue(max_concurrent_experiments=max_concurrent)
        _experiment_queue.start()
    return _experiment_queue
