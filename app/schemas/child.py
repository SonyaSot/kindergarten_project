from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import Optional

# Схема для создания ребенка
class ChildCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)  # ФИО ребенка
    date_of_birth: date  # Дата рождения
    group_id: int  # ID группы
    parent_name: str = Field(..., min_length=2, max_length=100)  # ФИО родителя
    parent_phone: Optional[str] = None  # Телефон родителя
    parent_email: Optional[EmailStr] = None  # Email родителя
    has_discount: bool = False  # Есть ли льготы
    discount_reason: Optional[str] = None  # Причина льготы

# Схема для обновления ребенка
class ChildUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    group_id: Optional[int] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    parent_email: Optional[EmailStr] = None
    has_discount: Optional[bool] = None
    discount_reason: Optional[str] = None

# Схема ответа (данные ребенка)
class ChildResponse(BaseModel):
    id: int
    full_name: str
    date_of_birth: date
    group_id: int
    parent_name: str
    parent_phone: Optional[str] = None
    parent_email: Optional[str] = None
    has_discount: bool = False
    discount_reason: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True