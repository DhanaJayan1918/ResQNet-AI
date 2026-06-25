"""
ResQNet AI - Pytest Configuration
Provides mocked database (MongoDB/Redis) and authentication fixtures for integration testing.
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator, Any
from datetime import datetime

# ==============================================================================
# Monkey Patching MongoDB (Motor) and Redis before importing app modules
# ==============================================================================
import motor.motor_asyncio
import redis.asyncio
from mongomock import MongoClient

class AsyncMockCursor:
    def __init__(self, sync_cursor):
        self.sync_cursor = sync_cursor
        
    def sort(self, *args, **kwargs):
        self.sync_cursor.sort(*args, **kwargs)
        return self
        
    def skip(self, *args, **kwargs):
        self.sync_cursor.skip(*args, **kwargs)
        return self
        
    def limit(self, *args, **kwargs):
        self.sync_cursor.limit(*args, **kwargs)
        return self
        
    async def to_list(self, length=None):
        return list(self.sync_cursor)

class AsyncMockCollection:
    def __init__(self, sync_collection):
        self.sync_collection = sync_collection
        
    async def find_one(self, *args, **kwargs):
        return self.sync_collection.find_one(*args, **kwargs)
        
    async def insert_one(self, *args, **kwargs):
        class InsertResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        res = self.sync_collection.insert_one(*args, **kwargs)
        return InsertResult(res.inserted_id)
        
    async def insert_many(self, *args, **kwargs):
        class InsertManyResult:
            def __init__(self, inserted_ids):
                self.inserted_ids = inserted_ids
        res = self.sync_collection.insert_many(*args, **kwargs)
        return InsertManyResult(res.inserted_ids)
        
    def find(self, *args, **kwargs):
        sync_cursor = self.sync_collection.find(*args, **kwargs)
        return AsyncMockCursor(sync_cursor)
        
    async def count_documents(self, *args, **kwargs):
        return self.sync_collection.count_documents(*args, **kwargs)
        
    async def update_one(self, *args, **kwargs):
        return self.sync_collection.update_one(*args, **kwargs)
        
    async def delete_many(self, *args, **kwargs):
        return self.sync_collection.delete_many(*args, **kwargs)
        
    async def create_indexes(self, *args, **kwargs):
        return []

class AsyncMockDatabase:
    def __init__(self, sync_db):
        self.sync_db = sync_db
        
    def __getattr__(self, name):
        return AsyncMockCollection(getattr(self.sync_db, name))
        
    def __getitem__(self, name):
        return AsyncMockCollection(self.sync_db[name])
        
    async def list_collection_names(self):
        return self.sync_db.list_collection_names()

class AsyncMockMotorClient:
    def __init__(self, *args, **kwargs):
        self.sync_client = MongoClient()
        
    def __getitem__(self, name):
        return AsyncMockDatabase(self.sync_client[name])
        
    def __getattr__(self, name):
        if name == "admin":
            class MockAdmin:
                async def command(self, *args, **kwargs):
                    return {"ok": 1}
            return MockAdmin()
        return AsyncMockDatabase(self.sync_client[name])
        
    def close(self):
        pass

class MockRedis:
    def __init__(self, *args, **kwargs):
        self.db = {}
        
    async def ping(self):
        return True
        
    async def set(self, key, value, ex=None):
        self.db[key] = str(value)
        
    async def get(self, key):
        return self.db.get(key)
        
    async def delete(self, key):
        self.db.pop(key, None)
        
    async def exists(self, key):
        return key in self.db
        
    async def flushdb(self):
        self.db.clear()
        
    async def close(self):
        pass
        
    def pipeline(self):
        return self
        
    async def incr(self, key):
        val = int(self.db.get(key, 0)) + 1
        self.db[key] = str(val)
        return val
        
    async def expire(self, key, seconds):
        pass
        
    async def execute(self):
        return []

# Apply monkey patches
motor.motor_asyncio.AsyncIOMotorClient = AsyncMockMotorClient
redis.asyncio.Redis = MockRedis
redis.asyncio.from_url = lambda *args, **kwargs: MockRedis()

# ==============================================================================
# Import Application modules after monkey patching has been applied
# ==============================================================================
from app.config import get_settings
from app.db.mongodb import connect_mongodb, get_database, close_mongodb
from app.db.redis_client import connect_redis, close_redis, get_redis
from app.main import app
from app.services.auth_service import hash_password, create_access_token
import httpx


@pytest.fixture(scope="session", autouse=True)
def test_settings():
    settings = get_settings()
    settings.MONGODB_DB_NAME = "resqnet_test"
    settings.REDIS_URL = "redis://localhost:6379/15"
    settings.JWT_SECRET_KEY = "test-jwt-secret-key-very-secure-indeed"
    return settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def init_databases(test_settings):
    """Connect to MongoDB and Redis once for the test session."""
    await connect_mongodb()
    await connect_redis()
    yield
    await close_mongodb()
    await close_redis()


@pytest.fixture(autouse=True)
async def clean_database(init_databases):
    """Clear database collections before each test to guarantee isolation."""
    db = get_database()
    collections = await db.list_collection_names()
    for col in collections:
        if not col.startswith("system."):
            await db[col].delete_many({})
            
    # Clear Redis
    redis_client = get_redis()
    await redis_client.flushdb()


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an async TestClient for making API requests."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def test_users(init_databases):
    """Seed test users into the test database and return their metadata."""
    db = get_database()
    
    users = [
        {
            "email": "test_citizen@resqnet.ai",
            "password_hash": hash_password("Citizen@123"),
            "full_name": "Citizen User",
            "role": "citizen",
            "phone": "+91-9999999901",
            "organization": None,
            "is_active": True,
            "permissions": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "email": "test_field@resqnet.ai",
            "password_hash": hash_password("Field@123"),
            "full_name": "Field Officer User",
            "role": "field_officer",
            "phone": "+91-9999999902",
            "organization": "NDRF",
            "is_active": True,
            "permissions": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "email": "test_coord@resqnet.ai",
            "password_hash": hash_password("Coordinator@123"),
            "full_name": "Coordinator User",
            "role": "coordinator",
            "phone": "+91-9999999903",
            "organization": "SDMA",
            "is_active": True,
            "permissions": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    ]
    
    for u in users:
        result = await db.users.insert_one(u)
        u["_id"] = str(result.inserted_id)
        
    return {u["role"]: u for u in users}


@pytest.fixture
async def citizen_headers(test_users) -> dict:
    """Authentication headers for a citizen user."""
    user = test_users["citizen"]
    token = create_access_token(user["_id"], user["role"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def field_officer_headers(test_users) -> dict:
    """Authentication headers for a field officer user."""
    user = test_users["field_officer"]
    token = create_access_token(user["_id"], user["role"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def coordinator_headers(test_users) -> dict:
    """Authentication headers for a coordinator user."""
    user = test_users["coordinator"]
    token = create_access_token(user["_id"], user["role"])
    return {"Authorization": f"Bearer {token}"}
