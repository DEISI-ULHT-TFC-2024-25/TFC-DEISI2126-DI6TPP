import pytest
from httpx import AsyncClient, ASGITransport
from webapp import app  # importa a tua FastAPI app corretamente

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
