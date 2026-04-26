from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.schemas.child import ChildResponse

# Схема для создания группы
class GroupCreate(BaseModel):
    name: str
    age_range: Optional[str] = None
    teacher_id: Optional[int] = None

# Схема для обновления группы
class GroupUpdate(BaseModel):
    name: Optional[str] = None
    age_range: Optional[str] = None
    teacher_id: Optional[int] = None

# Схема ответа (данные группы) - С ДЕТЬМИ
class GroupResponse(BaseModel):
    id: int
    name: str
    age_range: Optional[str] = None
    teacher_id: Optional[int] = None
    children: List[ChildResponse] = []  # ⬅️ ДОБАВЛЕНО ПОЛЕ children

    class Config:
        from_attributes = True