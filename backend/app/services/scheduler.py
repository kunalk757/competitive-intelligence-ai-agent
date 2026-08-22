import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Dict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.gnews_service import gnews_service
from app.database.supabase_client import news_repository

logger = logging.getLogger("news_scheduler")

# Timezone constant
IST_TIMEZONE = ZoneInfo("Asia/Kolkata")

# Global scheduler instance
news_scheduler = AsyncIOScheduler()

# In-memory tracking of scheduler runs
_scheduler_status: Dict[str, Any] = {
    "is_running": False,
    "last_run_timestamp": None,
    "last_run_status": "Not run yet",
    "last_articles_added": 0,
    "timezone": "Asia/Kolkata",
    "schedule": "10:00 AM & 10:00 PM IST",
}


async def sync_news_job() -> Dict[str, Any]:
    """
    Execute news synchronization job:
    1. Fetch latest real tech & AI news from GNews.
    2. Deduplicate articles against Supabase/local store.
    3. Save new articles.
    4. Keep all existing articles if GNews fails or returns empty.
    """
    now_ist = datetime.now(IST_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S %Z")
    logger.info(f"[{now_ist}] Starting scheduled news sync job...")

    try:
        # Step 1: Fetch from GNews
        fetched_articles = await gnews_service.fetch_latest_news(max_results=10)

        if not fetched_articles:
            logger.info("No new articles retrieved from GNews (or key not configured/empty). Retaining existing database articles.")
            _scheduler_status["last_run_timestamp"] = now_ist
            _scheduler_status["last_run_status"] = "Completed (0 new articles or API skipped; preserved existing news)"
            _scheduler_status["last_articles_added"] = 0
            return {
                "success": True,
                "articles_fetched": 0,
                "articles_inserted": 0,
                "status": _scheduler_status["last_run_status"],
            }

        # Step 2: Save to Supabase (with deduplication on source_url)
        upsert_res = await news_repository.upsert_articles(fetched_articles)
        inserted_count = upsert_res.get("inserted", 0)

        _scheduler_status["last_run_timestamp"] = now_ist
        _scheduler_status["last_run_status"] = f"Success: {inserted_count} new articles added"
        _scheduler_status["last_articles_added"] = inserted_count

        logger.info(
            f"Scheduled news sync completed. {inserted_count} articles added. Total saved: {upsert_res.get('total')}"
        )
        return {
            "success": True,
            "articles_fetched": len(fetched_articles),
            "articles_inserted": inserted_count,
            "total_saved": upsert_res.get("total"),
            "status": "Success",
        }

    except Exception as exc:
        logger.error(f"Error during news sync job: {exc}", exc_info=True)
        _scheduler_status["last_run_timestamp"] = now_ist
        _scheduler_status["last_run_status"] = f"Failed: {str(exc)} (Existing news preserved)"
        return {
            "success": False,
            "error": str(exc),
            "status": "Failed (Preserved existing news)",
        }


def start_scheduler():
    """
    Start the APScheduler for 10:00 AM and 10:00 PM IST (Asia/Kolkata).
    """
    if news_scheduler.running:
        logger.info("News scheduler is already running.")
        return

    # Trigger at 10:00 AM (10) and 10:00 PM (22) IST
    trigger = CronTrigger(hour="10,22", minute="0", timezone=IST_TIMEZONE)
    news_scheduler.add_job(
        sync_news_job,
        trigger=trigger,
        id="daily_news_sync_ist",
        name="Sync Latest News at 10:00 AM and 10:00 PM IST",
        replace_existing=True,
    )

    news_scheduler.start()
    _scheduler_status["is_running"] = True
    logger.info("News scheduler started successfully with schedule: 10:00 AM and 10:00 PM Asia/Kolkata.")


def stop_scheduler():
    """Gracefully shutdown the scheduler."""
    if news_scheduler.running:
        news_scheduler.shutdown(wait=False)
        _scheduler_status["is_running"] = False
        logger.info("News scheduler stopped.")


def get_scheduler_status() -> Dict[str, Any]:
    """Retrieve current scheduler runtime status and next run time."""
    next_run_time = None
    if news_scheduler.running:
        job = news_scheduler.get_job("daily_news_sync_ist")
        if job and job.next_run_time:
            next_run_time = job.next_run_time.astimezone(IST_TIMEZONE).strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            )

    return {
        **_scheduler_status,
        "is_running": news_scheduler.running,
        "next_run_ist": next_run_time,
    }
