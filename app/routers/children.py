from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.child_service import ChildService
from app.schemas.child import ChildCreate, ChildResponse
from app.models import User
from app.routers.auth import get_current_user_from_token

router = APIRouter(prefix="/children", tags=["Дети"])

@router.post("/", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
async def create_child(
    child_data: ChildCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Создание ребенка - использует Service Layer"""
    service = ChildService(db)
    return service.create_child(child_data)

@router.get("/", response_model=List[ChildResponse])
async def get_children(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Получить всех детей - использует Service Layer"""
    service = ChildService(db)
    return service.get_children_by_group(1)  # Или логика по группам