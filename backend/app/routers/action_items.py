"""Action-item completion toggle."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..models import ActionItem

router = APIRouter(prefix="/api/action-items", tags=["action-items"])


@router.patch("/{item_id}", response_model=schemas.ActionItemOut)
def toggle_action_item(
    item_id: int, body: schemas.ToggleActionItemRequest, db: Session = Depends(get_db)
):
    item = db.get(ActionItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    item.completed = body.completed
    db.commit()
    return schemas.ActionItemOut.model_validate(item)
