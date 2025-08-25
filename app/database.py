from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Define the SQLite database URL.
# The database file 'app.db' will be created in the project's root directory.
DATABASE_URL = "sqlite+aiosqlite:///./app.db"

# Create the async engine. `echo=True` logs SQL statements, which is useful for debugging.
engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True)

# Create a configured "Session" class.
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

# Create a base class for our declarative database models to inherit from.
Base = declarative_base()

# Dependency to get a DB session in API endpoints.
# This ensures that the database session is always closed after the request is finished.
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
