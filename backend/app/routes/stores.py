"""Store creation routes. A store's first member is its owner."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies import get_current_user_id, get_db
from app.schemas.auth import StoreCreateRequest, StoreResponse

router = APIRouter(prefix="/stores", tags=["stores"])


@router.post("", response_model=StoreResponse, status_code=201)
def create_store(
    payload: StoreCreateRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Require a valid login, then atomically add store and owner membership."""
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Store name cannot be blank")
    store = db.execute(text("""
        SELECT * FROM public.provision_store_for_user(
            :user_id, :store_name, :store_address
        )
    """), {"user_id": str(user_id), "store_name": name,
          "store_address": payload.address}).one()
    db.commit()
    return StoreResponse(id=str(store.created_store_id), name=name,
                         address=payload.address, role="owner")
