from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from app.db_models import Setting

async def get_setting(db: AsyncSession, key: str) -> Setting | None:
    """
    Asynchronously retrieve a setting from the database by its key.

    Args:
        db: The SQLAlchemy async session.
        key: The key of the setting to retrieve.

    Returns:
        The Setting object if found, otherwise None.
    """
    result = await db.execute(select(Setting).filter(Setting.key == key))
    return result.scalars().first()

async def set_setting(db: AsyncSession, key: str, value: str) -> Setting:
    """
    Asynchronously create or update a setting in the database (upsert).

    Args:
        db: The SQLAlchemy async session.
        key: The key of the setting to set.
        value: The new value for the setting.

    Returns:
        The created or updated Setting object.
    """
    # First, try to get the existing setting.
    existing_setting = await get_setting(db, key)

    if existing_setting:
        # If it exists, update its value.
        existing_setting.value = value
        db_setting = existing_setting
    else:
        # If it does not exist, create a new Setting instance.
        db_setting = Setting(key=key, value=value)
        db.add(db_setting)

    # Commit the transaction to save the changes to the database.
    await db.commit()
    # Refresh the instance to get the updated state from the DB.
    await db.refresh(db_setting)

    return db_setting
