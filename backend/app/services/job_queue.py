from queue import Queue
from threading import Thread


class LocalJobQueue:
    def __init__(self, worker, callback):
        self.queue = Queue()
        self.worker = worker
        self.callback = callback

        thread = Thread(
            target=self._process_jobs,
            daemon=True,
        )

        thread.start()

    def _process_jobs(self):
        while True:
            job = self.queue.get()

            try:
                result = self.worker.process(job)
                self.callback(result)

            except Exception as error:
                print(f"Worker error: {error}")

            finally:
                self.queue.task_done()

    def submit(self, job):
        self.queue.put(job)
