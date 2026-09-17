"""Background worker."""

from __future__ import annotations


class Worker:
    def __init__(self, queue):
        self.queue = queue
        self.running = False

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def process(self):
        job = self.queue.dequeue()
        if job:
            return job
        return None
