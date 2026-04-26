"""
app/routers/users.py
Управление пользователями (только для админа)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import User, UserRole, Group
from app.routers.auth import get_current_user_from_token 
from app.utils.security import get_password_hash 
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.utils.audit import log_action

router = APIRouter(prefix="/users", tags=["Пользователи"])


# ============================================
# ПОЛУЧИТЬ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ
# ============================================

@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Получить список всех пользователей (только админ)"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут управлять пользователями"
        )
    
    query = db.query(User)
    
    if role:
        try:
            role_enum = UserRole[role.upper()]
            query = query.filter(User.role == role_enum)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неверная роль. Допустимые: {[r.name for r in UserRole]}"
            )
    
    users = query.offset(skip).limit(limit).all()
    
    return users


# ============================================
# ПОЛУЧИТЬ НЕАКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ (ЗАЯВКИ)
# ============================================

@router.get("/pending", response_model=List[UserResponse])
async def get_pending_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Получить список пользователей, ожидающих подтверждения (только админ)"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут просматривать заявки"
        )
    
    users = db.query(User).filter(User.is_active == False).all()
    return users


# ============================================
# ПОДТВЕРДИТЬ ЗАЯВКУ (активировать)
# ============================================

@router.put("/{user_id}/approve", response_model=UserResponse)
async def approve_user(
    user_id: int,
    group_id: Optional[int] = Query(None, description="ID группы для учителя"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Подтвердить заявку - активировать пользователя (только админ)"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут подтверждать заявки"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user.is_active:
        raise HTTPException(status_code=400, detail="Пользователь уже активирован")
    
    user.is_active = True
    
    # Если это учитель - назначаем группу
    if user.role == UserRole.TEACHER and group_id:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Группа не найдена")
        group.teacher_id = user.id
    
    db.commit()
    db.refresh(user)
    
    log_action(
        db=db,
        user_id=current_user.id,
        action="APPROVE",
        resource="users",
        resource_id=user.id,
        details=f"Активирован пользователь: {user.email}, роль: {user.role.value}",
        ip_address=request.client.host if request.client else None
    )
    
    return user


# ============================================
# ОТКЛОНИТЬ ЗАЯВКУ (удалить)
# ============================================

@router.delete("/{user_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def reject_user(
    user_id: int,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Отклонить заявку - удалить пользователя (только админ)"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут отклонять заявки"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    log_action(
        db=db,
        user_id=current_user.id,
        action="REJECT",
        resource="users",
        resource_id=user.id,
        details=f"Отклонена заявка пользователя: {user.email}",
        ip_address=request.client.host if request.client else None
    )
    
    db.delete(user)
    db.commit()
    
    return None


# ============================================
# ПОЛУЧИТЬ ОДНОГО ПОЛЬЗОВАТЕЛЯ ПО ID
# ============================================

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Получить пользователя по ID (только админ)"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут просматривать пользователей"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return user


# ============================================
# ОБНОВИТЬ ПОЛЬЗОВАТЕЛЯ
# ============================================

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Обновить данные пользователя (только админ)"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут редактировать пользователей"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя изменить свои данные через этот эндпоинт"
        )
    
    update_data = user_update.dict(exclude_unset=True)
    
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    if "role" in update_data and update_data["role"]:
        try:
            update_data["role"] = UserRole[update_data["role"].upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неверная роль. Допустимые: {[r.name for r in UserRole]}"
            )
    
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    log_action(
        db=db,
        user_id=current_user.id,
        action="UPDATE",
        resource="users",
        resource_id=user.id,
        details=f"Обновлён пользователь: {user.email}",
        ip_address=request.client.host if request.client else None
    )
    
    return user


# ============================================
# УДАЛИТЬ ПОЛЬЗОВАТЕЛЯ
# ============================================

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Удалить пользователя (только админ)"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут удалять пользователей"
        )
    
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить самого себя"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    user_email = user.email
    user_role = user.role
    
    db.delete(user)
    db.commit()
    
    log_action(
        db=db,
        user_id=current_user.id,
        action="DELETE",
        resource="users",
        resource_id=user_id,
        details=f"Удалён пользователь: {user_email} (роль: {user_role})",
        ip_address=request.client.host if request.client else None
    )
    
    return None


# ============================================
# НАЗНАЧИТЬ ГРУППУ УЧИТЕЛЮ
# ============================================

@router.put("/{user_id}/assign-group")
async def assign_group_to_teacher(
    user_id: int,
    group_id: int,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Назначить группу учителю (только админ)"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Только администратор")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user.role != UserRole.TEACHER:
        raise HTTPException(status_code=400, detail="Пользователь не является учителем")
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    group.teacher_id = user.id
    db.commit()
    
    log_action(
        db=db,
        user_id=current_user.id,
        action="ASSIGN_GROUP",
        resource="groups",
        resource_id=group.id,
        details=f"Учителю {user.email} назначена группа {group.name}",
        ip_address=request.client.host if request.client else None
    )
    
    return {"message": f"Группа '{group.name}' назначена учителю {user.full_name}"}