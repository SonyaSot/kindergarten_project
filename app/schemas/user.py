from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum

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

# Данные о пользователе (без пароля)
class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True

# Токен доступа
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"