from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.models import SystemPrompt

router = APIRouter()

# Define a constant for the database key to avoid magic strings.
SYSTEM_PROMPT_KEY = "system_prompt"

@router.get("/prompts/system", response_model=SystemPrompt)
async def get_system_prompt(db: AsyncSession = Depends(get_db)):
    """
    Retrieve the currently active system prompt from the database.
    """
    db_setting = await crud.get_setting(db, key=SYSTEM_PROMPT_KEY)

    if not db_setting:
        # If the prompt has never been set, return a 404 error.
        raise HTTPException(status_code=404, detail="System prompt not set.")

    return SystemPrompt(prompt=db_setting.value)

@router.post("/prompts/system", response_model=SystemPrompt)
async def set_system_prompt(
    prompt_in: SystemPrompt, db: AsyncSession = Depends(get_db)
):
    """
    Set or update the system prompt in the database.
    """
    # Use the CRUD function to create or update the setting.
    db_setting = await crud.set_setting(
        db, key=SYSTEM_PROMPT_KEY, value=prompt_in.prompt
    )

    return SystemPrompt(prompt=db_setting.value)
