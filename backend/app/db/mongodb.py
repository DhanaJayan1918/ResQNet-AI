"""
ResQNet AI - MongoDB Connection Manager
Uses Motor (async MongoDB driver) for non-blocking database operations.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING, GEOSPHERE
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

try:
    import mongomock
except ImportError:
    mongomock = None

_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


# ---- Async Mock MongoDB Client for Local Development Fallback ----

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

    async def update_many(self, *args, **kwargs):
        return self.sync_collection.update_many(*args, **kwargs)
        
    async def delete_many(self, *args, **kwargs):
        return self.sync_collection.delete_many(*args, **kwargs)

    async def delete_one(self, *args, **kwargs):
        return self.sync_collection.delete_one(*args, **kwargs)
        
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
        if mongomock is None:
            raise RuntimeError("mongomock is not installed. Cannot fall back to in-memory database.")
        self.sync_client = mongomock.MongoClient()
        
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


async def connect_mongodb() -> None:
    """Initialize MongoDB connection and create indexes."""
    global _client, _database
    settings = get_settings()

    logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}...")
    try:
        _client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
        )
        _database = _client[settings.MONGODB_DB_NAME]

        # Verify connection
        await _client.admin.command("ping")
        logger.info(f"Connected to MongoDB database: {settings.MONGODB_DB_NAME}")

        # Create indexes
        await _create_indexes()
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        if mongomock is not None:
            logger.warning("⚠️  Falling back to in-memory Mock MongoDB database for local development.")
            _client = AsyncMockMotorClient()
            _database = _client[settings.MONGODB_DB_NAME]
            # Automatically seed mock database
            try:
                from app.db.seed import SAMPLE_USERS, SAMPLE_RESOURCES, SAMPLE_SHELTERS, SAMPLE_HOSPITALS, SAMPLE_INCIDENTS
                await _database.users.insert_many(SAMPLE_USERS)
                await _database.resources.insert_many(SAMPLE_RESOURCES)
                await _database.shelters.insert_many(SAMPLE_SHELTERS)
                await _database.hospitals.insert_many(SAMPLE_HOSPITALS)
                await _database.incidents.insert_many(SAMPLE_INCIDENTS)
                logger.info("🌱 Automatically seeded in-memory MongoDB database with mock data (including demo users).")
            except Exception as seed_err:
                logger.error(f"❌ Failed to seed in-memory MongoDB: {seed_err}")
        else:
            logger.error("❌ mongomock is not installed. Cannot fall back to in-memory MongoDB.")
            raise e



async def _create_indexes() -> None:
    """Create all required database indexes for performance."""
    db = get_database()

    # Users collection indexes
    await db.users.create_indexes([
        IndexModel([("email", ASCENDING)], unique=True),
        IndexModel([("role", ASCENDING)]),
    ])

    # Incidents collection indexes
    await db.incidents.create_indexes([
        IndexModel([("incident_id", ASCENDING)], unique=True),
        IndexModel([("status", ASCENDING)]),
        IndexModel([("priority.score", DESCENDING)]),
        IndexModel([("location", GEOSPHERE)]),
        IndexModel([("duplicate_group_id", ASCENDING)]),
        IndexModel([("created_at", DESCENDING)]),
        IndexModel([("status", ASCENDING), ("priority.score", DESCENDING)]),
        IndexModel([("source.reporter_id", ASCENDING)]),
    ])

    # Resources collection indexes
    await db.resources.create_indexes([
        IndexModel([("resource_id", ASCENDING)], unique=True),
        IndexModel([("type", ASCENDING)]),
        IndexModel([("status", ASCENDING)]),
        IndexModel([("location", GEOSPHERE)]),
        IndexModel([("type", ASCENDING), ("status", ASCENDING)]),
    ])

    # Shelters collection indexes
    await db.shelters.create_indexes([
        IndexModel([("shelter_id", ASCENDING)], unique=True),
        IndexModel([("location", GEOSPHERE)]),
        IndexModel([("status", ASCENDING)]),
    ])

    # Hospitals collection indexes
    await db.hospitals.create_indexes([
        IndexModel([("hospital_id", ASCENDING)], unique=True),
        IndexModel([("location", GEOSPHERE)]),
        IndexModel([("status", ASCENDING)]),
    ])

    # Audit logs - TTL index for auto-cleanup after 90 days
    await db.audit_logs.create_indexes([
        IndexModel([("timestamp", DESCENDING)]),
        IndexModel([("entity_type", ASCENDING), ("entity_id", ASCENDING)]),
        IndexModel([("actor_id", ASCENDING)]),
    ])

    # Command briefs
    await db.command_briefs.create_indexes([
        IndexModel([("brief_id", ASCENDING)], unique=True),
        IndexModel([("created_at", DESCENDING)]),
    ])

    logger.info("MongoDB indexes created successfully")


def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance. Raises if not connected."""
    if _database is None:
        raise RuntimeError("MongoDB is not connected. Call connect_mongodb() first.")
    return _database


def get_client() -> AsyncIOMotorClient:
    """Get the MongoDB client instance."""
    if _client is None:
        raise RuntimeError("MongoDB is not connected. Call connect_mongodb() first.")
    return _client


async def close_mongodb() -> None:
    """Close MongoDB connection."""
    global _client, _database
    if _client:
        _client.close()
        _client = None
        _database = None
        logger.info("MongoDB connection closed")
