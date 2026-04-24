"""
app/routers/users.py
Управление пользователями (только для админа)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import User, UserRole  # ← UserRole из models!
from app.routers.auth import get_current_user_from_token 
from app.utils.security import get_password_hash 
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.utils.audit import log_action  # ← Импортируй функцию!

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
    
    # Проверка прав
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут управлять пользователями"
        )
    
    # Формируем запрос
    query = db.query(User)
    
    # Фильтр по роли
    if role:
        try:
            role_enum = UserRole[role.upper()]
            query = query.filter(User.role == role_enum)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неверная роль. Допустимые: {[r.name for r in UserRole]}"
            )
    
    # Пагинация
    users = query.offset(skip).limit(limit).all()
    
    return users


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
    
    # Найти пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Нельзя удалить самого себя
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя изменить свои данные через этот эндпоинт"
        )
    
    # Обновляем поля
    update_data = user_update.dict(exclude_unset=True)
    
    # Если меняем пароль — хэшируем
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_hash_password(update_data.pop("password"))
    
    # Если меняем роль — валидируем
    if "role" in update_data and update_data["role"]:
        try:
            update_data["role"] = UserRole[update_data["role"].upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неверная роль. Допустимые: {[r.name for r in UserRole]}"
            )
    
    # Применяем обновления
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Аудит
    from app.utils.audit import log_action
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
    
    # Нельзя удалить самого себя
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить самого себя"
        )
    
    # Найти пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Сохраняем данные для аудита перед удалением
    user_email = user.email
    user_role = user.role
    
    # Удаляем (CASCADE удалит связанные записи)
    db.delete(user)
    db.commit()
    
    # Аудит
    from app.utils.audit import log_action
    log_action(
        db=db,
        user_id=current_user.id,
        action="DELETE",
        resource="users",
        resource_id=user_id,
        details=f"Удалён пользователь: {user_email} (роль: {user_role})",
        ip_address=request.client.host if request.client else None
    )
    
    return None  # 204 No Content