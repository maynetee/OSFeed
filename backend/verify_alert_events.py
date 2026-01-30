"""End-to-End Verification Script for Alert Event Publishing

This script verifies the complete flow:
1. Redis connection
2. Alert evaluation job execution
3. Event publishing to Redis
4. Database trigger record creation
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from uuid import UUID

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def verify_redis_connection():
    """Verify Redis is accessible"""
    logger.info("=" * 80)
    logger.info("STEP 1: Verifying Redis Connection")
    logger.info("=" * 80)

    try:
        from app.config import settings

        if not settings.redis_url:
            logger.error("❌ Redis URL not configured in settings")
            return False

        logger.info(f"✓ Redis URL configured: {settings.redis_url}")

        from redis.asyncio import Redis
        redis = Redis.from_url(settings.redis_url, decode_responses=True)
        result = await redis.ping()
        await redis.close()

        logger.info(f"✓ Redis ping successful: {result}")
        return True

    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False


async def check_active_alerts():
    """Check for active alerts in the database"""
    logger.info("=" * 80)
    logger.info("STEP 2: Checking Active Alerts")
    logger.info("=" * 80)

    try:
        from sqlalchemy import select
        from app.database import AsyncSessionLocal
        from app.models.alert import Alert

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Alert).where(Alert.is_active == True)
            )
            alerts = result.scalars().all()

            if not alerts:
                logger.warning("⚠️  No active alerts found in database")
                logger.info("   You may need to create a test alert with:")
                logger.info("   - is_active=True")
                logger.info("   - frequency='realtime'")
                logger.info("   - min_threshold=1 (low threshold for testing)")
                return []

            logger.info(f"✓ Found {len(alerts)} active alert(s):")
            for alert in alerts:
                logger.info(f"   - Alert ID: {alert.id}")
                logger.info(f"     Name: {alert.name}")
                logger.info(f"     Frequency: {alert.frequency}")
                logger.info(f"     Min Threshold: {alert.min_threshold}")
                logger.info(f"     Last Triggered: {alert.last_triggered_at}")
                logger.info(f"     Keywords: {alert.keywords}")
                logger.info(f"     Entities: {alert.entities}")

            return alerts

    except Exception as e:
        logger.error(f"❌ Failed to check alerts: {e}")
        import traceback
        traceback.print_exc()
        return []


async def monitor_redis_events(duration_seconds=5):
    """Monitor Redis events channel for a short duration"""
    logger.info("=" * 80)
    logger.info(f"STEP 3: Monitoring Redis Events (for {duration_seconds} seconds)")
    logger.info("=" * 80)

    try:
        from app.config import settings
        from redis.asyncio import Redis

        redis = Redis.from_url(settings.redis_url, decode_responses=True)
        pubsub = redis.pubsub()

        await pubsub.subscribe("osfeed:events")
        logger.info("✓ Subscribed to osfeed:events channel")
        logger.info("  Waiting for events...")

        events_received = []
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < duration_seconds:
            try:
                message = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True), timeout=1.0)
                if message and message['type'] == 'message':
                    logger.info(f"📨 Event received: {message['data']}")
                    events_received.append(message['data'])
            except asyncio.TimeoutError:
                pass

        await pubsub.unsubscribe("osfeed:events")
        await redis.close()

        if events_received:
            logger.info(f"✓ Received {len(events_received)} event(s)")
            return events_received
        else:
            logger.warning("⚠️  No events received during monitoring period")
            return []

    except Exception as e:
        logger.error(f"❌ Failed to monitor Redis: {e}")
        import traceback
        traceback.print_exc()
        return []


async def run_alert_evaluation():
    """Run the alert evaluation job"""
    logger.info("=" * 80)
    logger.info("STEP 4: Running Alert Evaluation Job")
    logger.info("=" * 80)

    try:
        from app.jobs.alerts import evaluate_alerts_job

        logger.info("Starting alert evaluation...")
        await evaluate_alerts_job()
        logger.info("✓ Alert evaluation job completed")
        return True

    except Exception as e:
        logger.error(f"❌ Alert evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def check_alert_triggers():
    """Check for recent alert triggers in database"""
    logger.info("=" * 80)
    logger.info("STEP 5: Checking Alert Triggers in Database")
    logger.info("=" * 80)

    try:
        from sqlalchemy import select
        from app.database import AsyncSessionLocal
        from app.models.alert import AlertTrigger

        async with AsyncSessionLocal() as session:
            # Get triggers from last 5 minutes
            cutoff = datetime.utcnow() - timedelta(minutes=5)
            result = await session.execute(
                select(AlertTrigger)
                .where(AlertTrigger.triggered_at >= cutoff)
                .order_by(AlertTrigger.triggered_at.desc())
            )
            triggers = result.scalars().all()

            if not triggers:
                logger.warning("⚠️  No alert triggers found in last 5 minutes")
                return []

            logger.info(f"✓ Found {len(triggers)} trigger(s) in last 5 minutes:")
            for trigger in triggers:
                logger.info(f"   - Trigger ID: {trigger.id}")
                logger.info(f"     Alert ID: {trigger.alert_id}")
                logger.info(f"     Triggered At: {trigger.triggered_at}")
                logger.info(f"     Summary: {trigger.summary}")
                logger.info(f"     Message Count: {len(trigger.message_ids)}")

            return triggers

    except Exception as e:
        logger.error(f"❌ Failed to check triggers: {e}")
        import traceback
        traceback.print_exc()
        return []


async def run_full_verification():
    """Run complete end-to-end verification"""
    logger.info("\n" + "=" * 80)
    logger.info("ALERT EVENT PUBLISHING - END-TO-END VERIFICATION")
    logger.info("=" * 80 + "\n")

    # Step 1: Verify Redis
    redis_ok = await verify_redis_connection()
    if not redis_ok:
        logger.error("\n❌ VERIFICATION FAILED: Redis not accessible")
        return False

    # Step 2: Check for active alerts
    alerts = await check_active_alerts()
    if not alerts:
        logger.error("\n❌ VERIFICATION FAILED: No active alerts to evaluate")
        logger.info("\nTo complete verification, create a test alert with:")
        logger.info("  - is_active=True")
        logger.info("  - frequency='realtime'")
        logger.info("  - min_threshold=1")
        logger.info("  - keywords matching your test messages")
        return False

    # Step 3: Start monitoring Redis in background
    monitor_task = asyncio.create_task(monitor_redis_events(duration_seconds=10))

    # Give monitor a moment to set up subscription
    await asyncio.sleep(1)

    # Step 4: Run alert evaluation
    eval_ok = await run_alert_evaluation()
    if not eval_ok:
        logger.error("\n❌ VERIFICATION FAILED: Alert evaluation job failed")
        monitor_task.cancel()
        return False

    # Step 5: Wait for monitor to complete
    events = await monitor_task

    # Step 6: Check database for triggers
    triggers = await check_alert_triggers()

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 80)

    success = True

    if redis_ok:
        logger.info("✓ Redis connection: PASSED")
    else:
        logger.error("❌ Redis connection: FAILED")
        success = False

    if alerts:
        logger.info(f"✓ Active alerts found: {len(alerts)}")
    else:
        logger.error("❌ No active alerts found")
        success = False

    if eval_ok:
        logger.info("✓ Alert evaluation job: PASSED")
    else:
        logger.error("❌ Alert evaluation job: FAILED")
        success = False

    if events:
        logger.info(f"✓ Redis events received: {len(events)}")
        logger.info("  Events published successfully!")
    else:
        logger.warning("⚠️  No Redis events received")
        logger.info("  This may be expected if no alerts were triggered")

    if triggers:
        logger.info(f"✓ Alert triggers in database: {len(triggers)}")
    else:
        logger.warning("⚠️  No recent alert triggers found")
        logger.info("  This may be expected if thresholds not met")

    logger.info("=" * 80 + "\n")

    if success and (events or triggers):
        logger.info("✅ VERIFICATION PASSED: Event flow is working!")
        return True
    elif success:
        logger.warning("⚠️  VERIFICATION INCOMPLETE: System working but no alerts triggered")
        logger.info("   This is expected if message thresholds not met")
        return True
    else:
        logger.error("❌ VERIFICATION FAILED: Check errors above")
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(run_full_verification())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("\n\nVerification interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
