""" Test the raw emcache library exptime behavior.

Contrary to the documentation of emcache, the exptime argument seems to be generally interpreted
as a relative time delta. It also seems that this delta cannot be larger than 30 days (in seconds),
otherwise, conflicting behavior emerges, possibly due to memcached itself.

This test is just meant to show that a short exptime is definitely interpreted as a delta in seconds.
"""
import pytest
import asyncio


@pytest.mark.asyncio
async def test_emcache_exptime_behavior():
    """Test emcache exptime parameter behavior"""

    try:
        import emcache
    except ImportError:
        pytest.skip("emcache library not installed")

    try:
        client = await emcache.create_client(
            node_addresses=[emcache.MemcachedHostAddress("127.0.0.1", 11211)],
            timeout=1.0
        )
    except Exception:
        pytest.skip("Could not connect to memcached server")

    # Test 1: Small relative timeout
    await client.set(b"test1", b"value1", exptime=1)
    result = await client.get(b"test1")
    assert result is not None, "Should set successfully with relative timeout"

    await asyncio.sleep(2)
    result = await client.get(b"test1")
    assert result is None, "Should expire after relative timeout"

    # Test 2: Small absolute timeout (this case should succeed but fails)
    # import time
    # await client.set(b"test1", b"value1", exptime=int(time.time()) + 1)
    # result = await client.get(b"test1")
    # assert result is not None, "Should set successfully with now+1s timeout"

    # await asyncio.sleep(2)
    # result = await client.get(b"test1")
    # assert result is None, "Should expire after 1s"

    # Test 3: Absolute time in the past (30 days + 1 second)
    await client.set(b"test1", b"value1", exptime=300 * 24 * 3600 + 1)
    result = await client.get(b"test1")
    assert result is None, "Should not succeed with a expiration time in the past"

    await client.close()
