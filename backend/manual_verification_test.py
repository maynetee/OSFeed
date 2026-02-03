"""
Manual Verification Script for add_channel vs add_channels_bulk endpoints

This script verifies that both endpoints produce identical behavior for:
1. Same channel created
2. Same collections assigned
3. Same audit logs
4. Same error messages for edge cases
"""

import asyncio
import sys
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

# Add the backend directory to the path
sys.path.insert(0, '/Users/mendel/side_pro/OSFeed/.auto-claude/worktrees/tasks/029-deduplicate-channel-add-logic-shared-between-singl/backend')

from app.database import AsyncSessionLocal, engine
from app.models.user import User
from app.models.channel import Channel, user_channels
from app.models.collection import Collection, collection_channels
from app.models.audit_log import AuditLog
from app.api.channels import add_channel, add_channels_bulk
from app.schemas.channel import ChannelCreate, BulkChannelCreate
from app.auth.users import get_password_hash


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")


async def create_test_user(db: AsyncSession, email: str) -> User:
    """Create a test user for verification"""
    user = User(
        id=uuid4(),
        email=email,
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_test_collection(db: AsyncSession, user_id, name: str, **kwargs) -> Collection:
    """Create a test collection for verification"""
    collection = Collection(
        id=uuid4(),
        user_id=user_id,
        name=name,
        **kwargs
    )
    db.add(collection)
    await db.commit()
    await db.refresh(collection)
    return collection


async def cleanup_test_data(db: AsyncSession, user: User):
    """Clean up test data after verification"""
    # Delete user_channels links
    await db.execute(delete(user_channels).where(user_channels.c.user_id == user.id))

    # Delete collections
    await db.execute(delete(Collection).where(Collection.user_id == user.id))

    # Delete audit logs
    await db.execute(delete(AuditLog).where(AuditLog.user_id == user.id))

    # Delete user
    await db.delete(user)

    await db.commit()


async def get_user_channels(db: AsyncSession, user_id) -> list:
    """Get all channels for a user"""
    result = await db.execute(
        select(Channel)
        .join(user_channels, user_channels.c.channel_id == Channel.id)
        .where(user_channels.c.user_id == user_id)
    )
    return result.scalars().all()


async def get_channel_collections(db: AsyncSession, channel_id) -> list:
    """Get all collections for a channel"""
    result = await db.execute(
        select(Collection)
        .join(collection_channels, collection_channels.c.collection_id == Collection.id)
        .where(collection_channels.c.channel_id == channel_id)
    )
    return result.scalars().all()


async def get_audit_logs(db: AsyncSession, user_id, resource_id=None) -> list:
    """Get audit logs for a user"""
    query = select(AuditLog).where(AuditLog.user_id == user_id)
    if resource_id:
        query = query.where(AuditLog.resource_id == str(resource_id))
    result = await db.execute(query.order_by(AuditLog.created_at))
    return result.scalars().all()


async def test_valid_channel_addition():
    """Test Case 1: Add a valid channel through both endpoints"""
    print_info("\n=== Test Case 1: Valid Channel Addition ===")

    async with AsyncSessionLocal() as db:
        # Create two test users
        user1 = await create_test_user(db, f"test_user_1_{uuid4().hex[:8]}@example.com")
        user2 = await create_test_user(db, f"test_user_2_{uuid4().hex[:8]}@example.com")

        # Create test collections for both users
        coll1 = await create_test_collection(
            db, user1.id, "Test Collection 1",
            is_default=True, is_global=False
        )
        coll2 = await create_test_collection(
            db, user2.id, "Test Collection 2",
            is_default=True, is_global=False
        )

        try:
            # Test with a real Telegram channel username (adjust as needed)
            test_username = "telegram"  # Official Telegram channel

            # Test add_channel endpoint
            print_info(f"Testing add_channel with username: {test_username}")
            try:
                result1 = await add_channel(
                    channel_data=ChannelCreate(username=test_username),
                    user=user1,
                    db=db
                )
                print_success(f"add_channel succeeded: {result1.get('username', 'N/A')}")

                # Get channel and collections
                channels1 = await get_user_channels(db, user1.id)
                channel1 = channels1[0] if channels1 else None
                collections1 = await get_channel_collections(db, channel1.id) if channel1 else []
                audit_logs1 = await get_audit_logs(db, user1.id, channel1.id if channel1 else None)

                print_info(f"  - Channel ID: {channel1.id if channel1 else 'None'}")
                print_info(f"  - Collections assigned: {len(collections1)}")
                print_info(f"  - Audit logs created: {len(audit_logs1)}")

            except Exception as e:
                print_error(f"add_channel failed: {e}")
                return False

            # Test add_channels_bulk endpoint
            print_info(f"Testing add_channels_bulk with username: {test_username}")
            try:
                result2 = await add_channels_bulk(
                    bulk_data=BulkChannelCreate(usernames=[test_username]),
                    user=user2,
                    db=db
                )
                print_success(f"add_channels_bulk succeeded: {result2.success_count} succeeded, {result2.failure_count} failed")

                if result2.success_count > 0:
                    # Get channel and collections
                    channels2 = await get_user_channels(db, user2.id)
                    channel2 = channels2[0] if channels2 else None
                    collections2 = await get_channel_collections(db, channel2.id) if channel2 else []
                    audit_logs2 = await get_audit_logs(db, user2.id, channel2.id if channel2 else None)

                    print_info(f"  - Channel ID: {channel2.id if channel2 else 'None'}")
                    print_info(f"  - Collections assigned: {len(collections2)}")
                    print_info(f"  - Audit logs created: {len(audit_logs2)}")

                    # Compare results
                    if channel1 and channel2:
                        # Compare channel properties
                        if (channel1.username == channel2.username and
                            channel1.telegram_id == channel2.telegram_id and
                            channel1.title == channel2.title):
                            print_success("✓ Channels have identical properties")
                        else:
                            print_error("✗ Channels have different properties")
                            print_error(f"  Channel 1: {channel1.username}, {channel1.telegram_id}, {channel1.title}")
                            print_error(f"  Channel 2: {channel2.username}, {channel2.telegram_id}, {channel2.title}")
                            return False

                        # Compare collection assignments
                        if len(collections1) == len(collections2):
                            print_success(f"✓ Same number of collections assigned ({len(collections1)})")
                        else:
                            print_warning(f"⚠ Different collection counts: {len(collections1)} vs {len(collections2)}")

                        # Compare audit logs
                        if len(audit_logs1) == len(audit_logs2):
                            print_success(f"✓ Same number of audit logs created ({len(audit_logs1)})")
                        else:
                            print_warning(f"⚠ Different audit log counts: {len(audit_logs1)} vs {len(audit_logs2)}")

                        # Compare audit log actions
                        if audit_logs1 and audit_logs2:
                            action1 = audit_logs1[0].action
                            action2 = audit_logs2[0].action
                            if action1 == action2:
                                print_success(f"✓ Same audit log action: {action1}")
                            else:
                                print_error(f"✗ Different audit log actions: {action1} vs {action2}")
                                return False

                    return True
                else:
                    print_error("add_channels_bulk failed to add channel")
                    if result2.failed:
                        print_error(f"  Error: {result2.failed[0].error}")
                    return False

            except Exception as e:
                print_error(f"add_channels_bulk failed: {e}")
                return False

        finally:
            # Cleanup
            await cleanup_test_data(db, user1)
            await cleanup_test_data(db, user2)


async def test_invalid_username():
    """Test Case 2: Invalid username format"""
    print_info("\n=== Test Case 2: Invalid Username Format ===")

    async with AsyncSessionLocal() as db:
        user1 = await create_test_user(db, f"test_user_3_{uuid4().hex[:8]}@example.com")
        user2 = await create_test_user(db, f"test_user_4_{uuid4().hex[:8]}@example.com")

        try:
            invalid_username = "abc"  # Too short (< 5 chars)

            # Test add_channel endpoint
            print_info(f"Testing add_channel with invalid username: {invalid_username}")
            error1 = None
            try:
                await add_channel(
                    channel_data=ChannelCreate(username=invalid_username),
                    user=user1,
                    db=db
                )
                print_error("add_channel should have raised an error")
                return False
            except Exception as e:
                error1 = str(e)
                print_success(f"add_channel raised error: {error1}")

            # Test add_channels_bulk endpoint
            print_info(f"Testing add_channels_bulk with invalid username: {invalid_username}")
            error2 = None
            try:
                result = await add_channels_bulk(
                    bulk_data=BulkChannelCreate(usernames=[invalid_username]),
                    user=user2,
                    db=db
                )
                if result.failure_count > 0:
                    error2 = result.failed[0].error
                    print_success(f"add_channels_bulk reported error: {error2}")
                else:
                    print_error("add_channels_bulk should have reported a failure")
                    return False
            except Exception as e:
                print_error(f"add_channels_bulk should not raise exception: {e}")
                return False

            # Compare error messages
            if error1 and error2:
                # Both should mention invalid format
                if "Invalid Telegram username format" in error1 and "Invalid Telegram username format" in error2:
                    print_success("✓ Both endpoints report the same error type")
                    return True
                else:
                    print_warning(f"⚠ Different error messages:")
                    print_warning(f"  add_channel: {error1}")
                    print_warning(f"  add_channels_bulk: {error2}")
                    return False

            return False

        finally:
            await cleanup_test_data(db, user1)
            await cleanup_test_data(db, user2)


async def test_duplicate_channel():
    """Test Case 3: Adding duplicate channel"""
    print_info("\n=== Test Case 3: Duplicate Channel ===")

    async with AsyncSessionLocal() as db:
        user1 = await create_test_user(db, f"test_user_5_{uuid4().hex[:8]}@example.com")
        user2 = await create_test_user(db, f"test_user_6_{uuid4().hex[:8]}@example.com")

        try:
            test_username = "telegram"

            # First, add the channel successfully
            print_info(f"Adding channel first time with add_channel")
            try:
                await add_channel(
                    channel_data=ChannelCreate(username=test_username),
                    user=user1,
                    db=db
                )
                print_success("Channel added successfully")
            except Exception as e:
                print_error(f"Failed to add channel first time: {e}")
                return False

            # Try to add the same channel again with add_channel
            print_info(f"Attempting to add same channel again with add_channel")
            error1 = None
            try:
                await add_channel(
                    channel_data=ChannelCreate(username=test_username),
                    user=user1,
                    db=db
                )
                print_error("add_channel should have raised an error for duplicate")
                return False
            except Exception as e:
                error1 = str(e)
                print_success(f"add_channel raised error: {error1}")

            # Add channel first time with bulk endpoint
            print_info(f"Adding channel first time with add_channels_bulk")
            try:
                result = await add_channels_bulk(
                    bulk_data=BulkChannelCreate(usernames=[test_username]),
                    user=user2,
                    db=db
                )
                if result.success_count > 0:
                    print_success("Channel added successfully")
                else:
                    print_error(f"Failed to add channel first time: {result.failed[0].error if result.failed else 'Unknown error'}")
                    return False
            except Exception as e:
                print_error(f"add_channels_bulk failed: {e}")
                return False

            # Try to add the same channel again with bulk endpoint
            print_info(f"Attempting to add same channel again with add_channels_bulk")
            error2 = None
            try:
                result = await add_channels_bulk(
                    bulk_data=BulkChannelCreate(usernames=[test_username]),
                    user=user2,
                    db=db
                )
                if result.failure_count > 0:
                    error2 = result.failed[0].error
                    print_success(f"add_channels_bulk reported error: {error2}")
                else:
                    print_error("add_channels_bulk should have reported a failure for duplicate")
                    return False
            except Exception as e:
                print_error(f"add_channels_bulk should not raise exception: {e}")
                return False

            # Compare error messages
            if error1 and error2:
                # Both should mention already exists
                if "already exists" in error1.lower() and "already exists" in error2.lower():
                    print_success("✓ Both endpoints report the same error type for duplicates")
                    return True
                else:
                    print_warning(f"⚠ Different error messages:")
                    print_warning(f"  add_channel: {error1}")
                    print_warning(f"  add_channels_bulk: {error2}")
                    return False

            return False

        finally:
            await cleanup_test_data(db, user1)
            await cleanup_test_data(db, user2)


async def run_all_tests():
    """Run all verification tests"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}Manual Verification Test Suite{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    results = []

    # Test 1: Valid channel addition
    try:
        result = await test_valid_channel_addition()
        results.append(("Valid Channel Addition", result))
    except Exception as e:
        print_error(f"Test 1 crashed: {e}")
        results.append(("Valid Channel Addition", False))

    # Test 2: Invalid username
    try:
        result = await test_invalid_username()
        results.append(("Invalid Username Format", result))
    except Exception as e:
        print_error(f"Test 2 crashed: {e}")
        results.append(("Invalid Username Format", False))

    # Test 3: Duplicate channel
    try:
        result = await test_duplicate_channel()
        results.append(("Duplicate Channel", result))
    except Exception as e:
        print_error(f"Test 3 crashed: {e}")
        results.append(("Duplicate Channel", False))

    # Print summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}Test Summary{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")

    print(f"\n{Colors.BLUE}Results: {passed}/{total} tests passed{Colors.RESET}\n")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
