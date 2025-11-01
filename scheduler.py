from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import traceback

class ScraperScheduler:
    def __init__(self, db=None, worker_fn=None):
        self.scheduler = BackgroundScheduler()
        self.jobs = {}
        self.db = db
        self.worker_fn = worker_fn

    def start(self):
        try:
            self.scheduler.start()
            print("Scheduler started")
        except Exception as e:
            print("Failed to start scheduler:", e)

    def stop(self):
        try:
            self.scheduler.shutdown(wait=False)
            print("Scheduler stopped")
        except Exception as e:
            print("Failed to stop scheduler:", e)

    def add_task(self, task_id: int, url: str, frequency: str):
        try:
            if frequency == "يومي":
                trigger = CronTrigger(hour=0, minute=0)
            elif frequency == "كل 12 ساعة":
                trigger = IntervalTrigger(hours=12)
            elif frequency == "كل 6 ساعات":
                trigger = IntervalTrigger(hours=6)
            elif frequency == "كل ساعة":
                trigger = IntervalTrigger(hours=1)
            else:
                trigger = CronTrigger(hour=0, minute=0)

            job = self.scheduler.add_job(
                self._execute_scraping_task,
                trigger,
                args=[task_id, url],
                id=str(task_id),
                name=f"Scraping_{task_id}",
                replace_existing=True
            )
            self.jobs[task_id] = job
            print(f"Added task {task_id}")
        except Exception as e:
            print("Add task failed:", e)

    def remove_task(self, task_id: int):
        try:
            job_id = str(task_id)
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                self.jobs.pop(task_id, None)
                print(f"Removed task {task_id}")
        except Exception as e:
            print("Remove task failed:", e)

    def _execute_scraping_task(self, task_id: int, url: str):
        try:
            start = datetime.utcnow()
            print(f"Running task {task_id} for {url} at {start.isoformat()}")
            items_count = 0
            if callable(self.worker_fn):
                items = self.worker_fn(url)
                items_count = len(items) if items else 0
            duration = (datetime.utcnow() - start).total_seconds()
            if self.db:
                self.db.add_scrape_history(url, "success", items_count=items_count, duration=duration)
            print(f"Finished task {task_id}, items={items_count}, duration={duration}s")
        except Exception as e:
            print("Task execution error:", e)
            if self.db:
                self.db.add_scrape_history(url, "failed", items_count=0, duration=0, error_message=str(e))
            traceback.print_exc()

    def get_scheduled_jobs(self):
        jobs_info = {}
        for job in self.scheduler.get_jobs():
            jobs_info[job.id] = {
                "name": job.name,
                "next_run": str(job.next_run_time),
                "trigger": str(job.trigger)
            }
        return jobs_info

    def pause_task(self, task_id: int):
        try:
            job = self.scheduler.get_job(str(task_id))
            if job:
                job.pause()
                print(f"Paused {task_id}")
        except Exception as e:
            print("Pause failed:", e)

    def resume_task(self, task_id: int):
        try:
            job = self.scheduler.get_job(str(task_id))
            if job:
                job.resume()
                print(f"Resumed {task_id}")
        except Exception as e:
            print("Resume failed:", e)
