"""
app/schemas/user.py
Pydantic схемы для пользователей
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum
from typing import Optional


# ✅ ВАЖНО: Роль должна совпадать с БД (заглавные буквы!)
class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    ACCOUNTANT = "accountant"
    


# Данные для регистрации
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.TEACHER


# Данные для входа
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ✅ НОВОЕ: Данные для обновления пользователя
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    group_id: Optional[int] = None
    is_active: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "Обновлённое Имя",
                "role": "ADMIN"
            }
        }


# Данные о пользователе (без пароля)
class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    group_id: Optional[int] = None  # ✅ Добавлено
    is_active: bool
    created_at: Optional[datetime] = None  # ✅ Добавлено
    updated_at: Optional[datetime] = None  # ✅ Добавлено

    class Config:
        from_attributes = True


# Токен доступа
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"