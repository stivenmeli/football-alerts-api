"""Scheduled jobs for monitoring football matches."""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.services.monitor_service import MonitorService

scheduler = AsyncIOScheduler()
monitor_service = MonitorService()


async def fetch_fixtures_job() -> None:
    """Job to fetch fixtures for today."""
    print("🔄 Running: Fetch fixtures job...")
    db = monitor_service.get_db()
    try:
        count = await monitor_service.fetch_and_store_fixtures(db)
        print(f"✅ Fetched {count} fixtures")
    except Exception as e:
        print(f"❌ Error in fetch_fixtures_job: {e}")
    finally:
        db.close()


async def fetch_odds_job() -> None:
    """Job to fetch odds for matches."""
    print("🔄 Running: Fetch odds job...")
    db = monitor_service.get_db()
    try:
        count = await monitor_service.fetch_and_store_odds(db)
        print(f"✅ Processed odds for {count} matches")
    except Exception as e:
        print(f"❌ Error in fetch_odds_job: {e}")
    finally:
        db.close()


async def monitor_matches_job() -> None:
    """Job to monitor live matches and send alerts."""
    print("🔄 Running: Monitor matches job...")
    db = monitor_service.get_db()
    try:
        alerts = await monitor_service.monitor_live_matches(db)
        if alerts > 0:
            print(f"🚨 Sent {alerts} alerts")
        else:
            print("✅ No alerts to send")
    except Exception as e:
        print(f"❌ Error in monitor_matches_job: {e}")
    finally:
        db.close()


def start_scheduler() -> None:
    """Start the scheduler with all jobs."""
    print("🚀 Starting scheduler...")

    # Job 1: Fetch fixtures with odds daily at 7:00 AM UTC (2:00 AM Colombia)
    # Searches for matches in the next 20 hours - covers most of the day
    scheduler.add_job(
        fetch_fixtures_job,
        trigger=CronTrigger(hour=7, minute=0),
        id="fetch_fixtures",
        name="Fetch daily fixtures with odds",
        replace_existing=True,
    )
    print("📅 Scheduled: Fetch fixtures daily at 7:00 AM UTC (2:00 AM Colombia)")

    # Job 3: Monitor live matches every minute
    scheduler.add_job(
        monitor_matches_job,
        trigger=IntervalTrigger(seconds=settings.UPDATE_INTERVAL_SECONDS),
        id="monitor_matches",
        name="Monitor live matches",
        replace_existing=True,
    )
    print(f"👁️  Scheduled: Monitor matches every {settings.UPDATE_INTERVAL_SECONDS} seconds")

    # Start scheduler
    scheduler.start()
    print("✅ Scheduler started successfully!")


def shutdown_scheduler() -> None:
    """Shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        print("🛑 Scheduler stopped")

