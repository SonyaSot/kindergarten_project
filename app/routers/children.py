from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.services.child_service import ChildService
from app.schemas.child import ChildCreate, ChildUpdate, ChildResponse
from app.models import User, UserRole, Group, Child
from app.routers.auth import get_current_user_from_token
from app.utils.logger import log_action

router = APIRouter(prefix="/children", tags=["Дети"])

# ПОЛУЧИТЬ ВСЕХ ДЕТЕЙ (с фильтрацией по правам)
@router.get("/", response_model=List[ChildResponse])
async def get_children(
    group_id: Optional[int] = Query(None, description="Фильтр по группе"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Получить список детей с фильтрацией по правам доступа"""
    
    # 1. ADMIN и ACCOUNTANT видят всех детей
    if current_user.role in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        if group_id:
            group = db.query(Group).filter(Group.id == group_id).first()
            if not group:
                raise HTTPException(status_code=404, detail="Группа не найдена")
            children = db.query(Child).filter(
                Child.group_id == group_id, 
                Child.is_active == True
            ).all()
        else:
            children = db.query(Child).filter(Child.is_active == True).all()
    
    # 2. TEACHER видит только детей из СВОИХ групп
    elif current_user.role == UserRole.TEACHER:
        my_groups = db.query(Group).filter(Group.teacher_id == current_user.id).all()
        my_group_ids = [g.id for g in my_groups]
        
        if not my_group_ids:
            return []
        
        if group_id:
            if group_id not in my_group_ids:
                raise HTTPException(status_code=403, detail="Нет доступа к этой группе")
            children = db.query(Child).filter(
                Child.group_id == group_id, 
                Child.is_active == True
            ).all()
        else:
            children = db.query(Child).filter(
                Child.group_id.in_(my_group_ids),
                Child.is_active == True
            ).all()
    
    else:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    return children

# ПОЛУЧИТЬ ДЕТЕЙ ПО ГРУППЕ
@router.get("/by-group/{group_id}", response_model=List[ChildResponse])
async def get_children_by_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Получить детей конкретной группы (с проверкой доступа)"""
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    if current_user.role == UserRole.TEACHER and group.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой группе")
    
    children = db.query(Child).filter(
        Child.group_id == group_id, 
        Child.is_active == True
    ).all()
    
    return children

# СОЗДАНИЕ РЕБЕНКА
@router.post("/", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
async def create_child(
    request: Request,
    child: ChildCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Создать нового ребенка (доступно ADMIN и TEACHER)"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    group = db.query(Group).filter(Group.id == child.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    if current_user.role == UserRole.TEACHER and group.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой группе")
    
    service = ChildService(db)
    new_child = service.create_child(child)
    
    log_action(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        resource="children",
        resource_id=new_child.id,
        details=f"Создан ребёнок: {new_child.full_name}",
        ip_address=request.client.host if request.client else None
    )
    
    return new_child

# ОБНОВЛЕНИЕ РЕБЕНКА
@router.put("/{child_id}", response_model=ChildResponse)
async def update_child(
    child_id: int,
    child_data: ChildUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Обновить данные ребенка"""
    
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Ребенок не найден")
    
    group = db.query(Group).filter(Group.id == child.group_id).first()
    
    if current_user.role == UserRole.TEACHER:
        if not group or group.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет доступа к этому ребенку")
    elif current_user.role not in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    update_data = child_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(child, field, value)
    
    db.commit()
    db.refresh(child)
    
    log_action(
        db=db,
        user_id=current_user.id,
        action="UPDATE",
        resource="children",
        resource_id=child.id,
        details=f"Обновлён ребёнок: {child.full_name}",
        ip_address=request.client.host if request.client else None
    )
    
    return child

# УДАЛЕНИЕ РЕБЕНКА
@router.delete("/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_child(
    child_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Удалить ребенка (только ADMIN)"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Только администратор может удалять детей")
    
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Ребенок не найден")
    
    log_action(
        db=db,
        user_id=current_user.id,
        action="DELETE",
        resource="children",
        resource_id=child.id,
        details=f"Удалён ребёнок: {child.full_name}",
        ip_address=request.client.host if request.client else None
    )
    
    db.delete(child)
    db.commit()
    return None