from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.child_service import ChildService
from app.schemas.child import ChildCreate, ChildResponse
from app.models import User, UserRole
from app.routers.auth import get_current_user_from_token
from app.utils.logger import log_action

router = APIRouter(prefix="/children", tags=["Дети"])

#Создание ребенка - использует Service Layer
@router.post("/", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
async def create_child(
    request: Request,
    child: ChildCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
        
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    service = ChildService(db)
    new_child = service.create_child(child_data)
    
    log_action(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        resource="children",
        resource_id=new_child.id,
        details=f"Создан ребёнок: {new_child.full_name}",
        ip_address=request.client.host
    )
    
    return new_child

#Получить всех детей - использует Service Layer
@router.get("/", response_model=List[ChildResponse])
async def get_children(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    service = ChildService(db)
    
    # Админ/бухгалтер видит всех
    if current_user.role.value in ["admin", "accountant"]:
        return service.get_all_children()
    
    # Учитель видит только свою группу
    elif current_user.role.value == "teacher":
        if not current_user.group_id:
            raise HTTPException(status_code=403, detail="Учитель не привязан к группе")
        return service.get_children_by_group(current_user.group_id)
    
    else:
        raise HTTPException(status_code=403, detail="Нет доступа")