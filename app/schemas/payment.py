from pydantic import BaseModel, Field, ConfigDict, field_serializer
from datetime import date, datetime
from typing import Optional, List
from enum import Enum

class PaymentStatusEnum(str, Enum):
    PENDING = "pending"    # Ожидает оплаты
    PAID = "paid"          # Оплачено
    OVERDUE = "overdue"    # Просрочено

# Схема для создания платежа
class PaymentCreate(BaseModel):
    child_id: int
    month: date  # Первое число месяца
    amount: float  # Сумма к оплате
    paid_amount: Optional[float] = 0.0  # Фактически оплачено
    status: PaymentStatusEnum = PaymentStatusEnum.PENDING
    comment: Optional[str] = None

# Схема для обновления платежа
class PaymentUpdate(BaseModel):
    paid_amount: Optional[float] = None
    status: Optional[PaymentStatusEnum] = None
    comment: Optional[str] = None

# Схема ответа (данные платежа)
class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    child_id: int
    child_name: Optional[str] = None
    month: date
    amount: float
    paid_amount: float
    status: PaymentStatusEnum
    comment: Optional[str] = None
    balance: float  # Задолженность
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @field_serializer('month')
    def serialize_month(self, value: date) -> str:
        return value.strftime("%d.%m.%Y") if value else None
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> str:
        return value.strftime("%d.%m.%Y %H:%M") if value else None

# Схема для отчета по оплатам
class PaymentReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    month: date
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    total_children: int
    total_amount: float  # Общая сумма к оплате
    total_paid: float  # Общая сумма оплачено
    total_balance: float  # Общая задолженность
    paid_count: int  # Количество оплативших
    pending_count: int  # Количество ожидающих
    overdue_count: int  # Количество просроченных
    payments: List[PaymentResponse]
    
    @field_serializer('month')
    def serialize_month(self, value: date) -> str:
        return value.strftime("%d.%m.%Y") if value else None