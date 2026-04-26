from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Group, User, UserRole, Child
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse
from app.routers.auth import get_current_user_from_token

router = APIRouter(prefix="/groups", tags=["Группы"])

# ПОЛУЧИТЬ МОИ ГРУППЫ
@router.get("/me", response_model=List[GroupResponse])
async def get_my_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Возвращает группы текущего пользователя"""
    
    # ADMIN и ACCOUNTANT видят все группы
    if current_user.role in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        groups = db.query(Group).all()
    else:
        # TEACHER видит ТОЛЬКО группы, где он teacher_id
        groups = db.query(Group).filter(Group.teacher_id == current_user.id).all()
    
    return groups

# ПОЛУЧИТЬ ВСЕ ГРУППЫ
@router.get("/", response_model=List[GroupResponse])
async def get_all_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Получить все группы (с фильтрацией по роли)"""
    
    if current_user.role in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        groups = db.query(Group).all()
    else:
        # TEACHER видит только свои группы
        groups = db.query(Group).filter(Group.teacher_id == current_user.id).all()
    
    return groups

# ПОЛУЧИТЬ ГРУППУ ПО ID (с детьми)
@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Получить группу по ID с проверкой доступа"""
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    # Проверка доступа для TEACHER
    if current_user.role == UserRole.TEACHER and group.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой группе")
    
    # Для ADMIN и ACCOUNTANT - доступ разрешен
    
    # Подгружаем детей
    children = db.query(Child).filter(
        Child.group_id == group_id, 
        Child.is_active == True
    ).all()
    
    # Добавляем детей в объект группы (Pydantic сам обработает)
    group.children = children
    
    return group

# СОЗДАНИЕ ГРУППЫ
@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Только администратор может создавать группы")
    
    new_group = Group(
        name=group_data.name,
        age_range=group_data.age_range,
        teacher_id=group_data.teacher_id
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group

# ОБНОВЛЕНИЕ ГРУППЫ
@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    group_data: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Только администратор может редактировать группы")
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    if group_data.name is not None:
        group.name = group_data.name
    if group_data.age_range is not None:
        group.age_range = group_data.age_range
    if group_data.teacher_id is not None:
        group.teacher_id = group_data.teacher_id
    
    db.commit()
    db.refresh(group)
    return group

# УДАЛЕНИЕ ГРУППЫ
@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Только администратор может удалять группы")
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    db.delete(group)
    db.commit()
    return None