"""
Runs the pipeline daily at the configured time.
Usage: python scheduler.py
Keep this running (e.g. via screen/tmux or as a system service).
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from config import DIGEST_HOUR, DIGEST_MINUTE
import pipeline

scheduler = BlockingScheduler(timezone="UTC")


@scheduler.scheduled_job("cron", hour=DIGEST_HOUR, minute=DIGEST_MINUTE)
def daily_run():
    pipeline.run(send_email=True)


if __name__ == "__main__":
    print(f"[scheduler] running daily at {DIGEST_HOUR:02d}:{DIGEST_MINUTE:02d} UTC")
    print("[scheduler] press Ctrl+C to stop")
    scheduler.start()
