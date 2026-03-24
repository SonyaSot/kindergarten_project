from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Схема для создания группы
class GroupCreate(BaseModel):
    name: str  # Название группы (например, "Солнышко")
    age_range: Optional[str] = None  # Возрастной диапазон (например, "3-4 года")
    teacher_id: Optional[int] = None  # ID воспитателя

# Схема для обновления группы
class GroupUpdate(BaseModel):
    name: Optional[str] = None
    age_range: Optional[str] = None
    teacher_id: Optional[int] = None

# Схема ответа (данные группы)
class GroupResponse(BaseModel):
    id: int
    name: str
    age_range: Optional[str] = None
    teacher_id: Optional[int] = None

    class Config:
        from_attributes = True