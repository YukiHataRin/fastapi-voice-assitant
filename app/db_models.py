from sqlalchemy import Column, String
from app.database import Base

class Setting(Base):
    __tablename__ = "settings"

    # Use 'key' as the primary identifier for the setting (e.g., 'system_prompt')
    key = Column(String, primary_key=True, index=True)

    # The value of the setting
    value = Column(String, nullable=False)
