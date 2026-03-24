from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from typing import Optional, List
from enum import Enum

class AttendanceStatusEnum(str, Enum):
    PRESENT = "present"        # Присутствовал
    ABSENT = "absent"          # Отсутствовал
    SICK = "sick"              # Заболевание
    NOT_MARKED = "not_marked"  # Не отмечен

# Схема для создания записи посещаемости
class AttendanceCreate(BaseModel):
    child_id: int
    date: date  # Ввод: YYYY-MM-DD (стандарт ISO)
    status: AttendanceStatusEnum = AttendanceStatusEnum.NOT_MARKED
    comment: Optional[str] = None

# Схема для обновления записи посещаемости
class AttendanceUpdate(BaseModel):
    status: Optional[AttendanceStatusEnum] = None
    comment: Optional[str] = None

# Схема для массовой отметки
class BulkAttendanceCreate(BaseModel):
    group_id: int
    date: date
    attendance_data: dict[int, AttendanceStatusEnum] = Field(default_factory=dict)
    default_status: AttendanceStatusEnum = AttendanceStatusEnum.PRESENT

# Схема ответа (данные записи посещаемости)
class AttendanceResponse(BaseModel):
    # ✅ Единый стиль конфигурации для Pydantic v2
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    child_id: int
    child_name: Optional[str] = None
    teacher_id: int
    date: date  # Формат: YYYY-MM-DD (стандарт API)
    status: AttendanceStatusEnum
    comment: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

# Схема для просмотра журнала группы за дату
class DailyJournalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    date: date
    group_id: int
    group_name: str
    teacher_id: int
    records: List[AttendanceResponse]
    total_children: int
    marked_count: int
    unmarked_count: int