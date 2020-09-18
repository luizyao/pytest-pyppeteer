import pytest


async def test_none_asyncio_marker():
    assert True


@pytest.mark.asyncio
async def test_with_asyncio_marker():
    assert True
