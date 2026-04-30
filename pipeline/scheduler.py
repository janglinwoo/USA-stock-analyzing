from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import Callable, Optional
from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PredictionScheduler:
    """Manage scheduled prediction updates using APScheduler."""

    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = BackgroundScheduler()
        self.is_running = False

    def start(self) -> None:
        """Start the scheduler."""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Scheduler started")
        else:
            logger.warning("Scheduler already running")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler stopped")

    def add_hourly_job(
        self, func: Callable, job_id: str = "hourly_prediction"
    ) -> None:
        """
        Add a job to run every hour during market hours.

        Args:
            func: Function to execute
            job_id: Unique job identifier
        """
        try:
            # Run every hour, Monday-Friday, 9:30 AM - 4:00 PM EST
            self.scheduler.add_job(
                func,
                "cron",
                hour="9-16",  # 9 AM to 4 PM (exclusive of 4)
                minute="0",  # Every hour
                day_of_week="0-4",  # Monday to Friday
                id=job_id,
                name="Hourly Prediction Update",
                replace_existing=True,
            )

            logger.info(f"Added hourly job: {job_id}")

        except Exception as e:
            logger.error(f"Error adding hourly job: {e}")

    def add_daily_job(
        self, func: Callable, hour: int = 9, minute: int = 30, job_id: str = "daily_prediction"
    ) -> None:
        """
        Add a daily job at specified time.

        Args:
            func: Function to execute
            hour: Hour to run (24-hour format)
            minute: Minute to run
            job_id: Unique job identifier
        """
        try:
            self.scheduler.add_job(
                func,
                "cron",
                hour=hour,
                minute=minute,
                day_of_week="0-4",  # Monday to Friday
                id=job_id,
                name=f"Daily Prediction Update ({hour}:{minute:02d})",
                replace_existing=True,
            )

            logger.info(f"Added daily job: {job_id}")

        except Exception as e:
            logger.error(f"Error adding daily job: {e}")

    def add_interval_job(
        self,
        func: Callable,
        minutes: int = 60,
        job_id: str = "interval_prediction",
    ) -> None:
        """
        Add a job to run at regular intervals.

        Args:
            func: Function to execute
            minutes: Interval in minutes
            job_id: Unique job identifier
        """
        try:
            self.scheduler.add_job(
                func,
                "interval",
                minutes=minutes,
                id=job_id,
                name=f"Interval Prediction Update ({minutes}m)",
                replace_existing=True,
            )

            logger.info(f"Added interval job: {job_id} (every {minutes} minutes)")

        except Exception as e:
            logger.error(f"Error adding interval job: {e}")

    def remove_job(self, job_id: str) -> bool:
        """
        Remove a scheduled job.

        Args:
            job_id: Job identifier

        Returns:
            True if job was removed
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing job: {e}")
            return False

    def get_jobs(self) -> list:
        """Get all scheduled jobs."""
        return self.scheduler.get_jobs()

    def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job."""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.pause()
                logger.info(f"Paused job: {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error pausing job: {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.resume()
                logger.info(f"Resumed job: {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error resuming job: {e}")
            return False

    def get_next_run_time(self, job_id: str) -> Optional[datetime]:
        """Get next run time for a job."""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                return job.next_run_time
            return None
        except Exception as e:
            logger.error(f"Error getting next run time: {e}")
            return None

    def print_jobs(self) -> None:
        """Print all scheduled jobs."""
        jobs = self.get_jobs()
        if not jobs:
            logger.info("No scheduled jobs")
            return

        logger.info("\n" + "=" * 60)
        logger.info("Scheduled Jobs:")
        logger.info("=" * 60)

        for job in jobs:
            logger.info(f"\nID: {job.id}")
            logger.info(f"Name: {job.name}")
            logger.info(f"Trigger: {job.trigger}")
            logger.info(f"Next Run: {job.next_run_time}")

        logger.info("=" * 60 + "\n")
