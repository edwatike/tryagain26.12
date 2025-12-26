"""Router for attachments (placeholder)."""
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_attachments():
    """List attachments (placeholder)."""
    return {"attachments": []}

