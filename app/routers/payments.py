from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import date, datetime, timedelta
from app.database import get_db
from app.models import Payment, Child, Group, User, Attendance, AttendanceStatus
from app.schemas.payment import (
    PaymentCreate, 
    PaymentUpdate, 
    PaymentResponse,
    PaymentReportResponse
)
from app.routers.auth import get_current_user_from_token

router = APIRouter(prefix="/payments", tags=["Бухгалтерия и отчеты"])

# === ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: Проверка прав ===
async def check_accountant_or_admin(current_user: User):
    """Проверяет, что пользователь - админ или бухгалтер"""
    if current_user.role.value not in ["admin", "accountant"]:
        raise HTTPException(status_code=403, detail="Только администратор или бухгалтер могут управлять платежами")
    return current_user

# === РАСЧЕТ СТОИМОСТИ НА ОСНОВЕ ПОСЕЩАЕМОСТИ ===
def calculate_fee_based_on_attendance(
    child_id: int,
    month: date,
    db: Session,
    base_rate: float = 500.0
) -> float:
    """Расчет суммы на основе дней присутствия"""
    month_start = month.replace(day=1)
    if month.month == 12:
        month_end = date(month.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(month.year, month.month + 1, 1) - timedelta(days=1)
    
    present_days = db.query(func.count(Attendance.id)).filter(
        and_(
            Attendance.child_id == child_id,
            Attendance.date >= month_start,
            Attendance.date <= month_end,
            Attendance.status == AttendanceStatus.PRESENT
        )
    ).scalar()
    
    return present_days * base_rate

# === СОЗДАНИЕ ПЛАТЕЖА ===
@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Создать новый платеж (админ или бухгалтер)"""
    await check_accountant_or_admin(current_user)
    
    child = db.query(Child).filter(Child.id == payment_data.child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Ребенок не найден")
    
    existing = db.query(Payment).filter(
        and_(
            Payment.child_id == payment_data.child_id,
            Payment.month == payment_data.month
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Платеж за этот месяц уже существует")
    
    new_payment = Payment(
        child_id=payment_data.child_id,
        month=payment_data.month,
        amount=payment_data.amount,
        paid_amount=payment_data.paid_amount or 0.0,
        status=payment_data.status,
        comment=payment_data.comment
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    
    child_name = child.full_name
    balance = new_payment.amount - new_payment.paid_amount
    
    return PaymentResponse(
        id=new_payment.id,
        child_id=new_payment.child_id,
        child_name=child_name,
        month=new_payment.month,
        amount=new_payment.amount,
        paid_amount=new_payment.paid_amount,
        status=new_payment.status,
        comment=new_payment.comment,
        balance=balance,
        created_at=new_payment.created_at,
        updated_at=new_payment.updated_at
    )

# === АВТОМАТИЧЕСКИЙ РАСЧЕТ ПЛАТЕЖЕЙ ===
@router.post("/auto-calculate/{target_month}", response_model=List[PaymentResponse])
async def auto_calculate_payments(
    target_month: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Автоматический расчет платежей на основе посещаемости"""
    await check_accountant_or_admin(current_user)
    
    children = db.query(Child).filter(Child.is_active == True).all()
    results = []
    base_rate = 500.0
    
    for child in children:
        existing = db.query(Payment).filter(
            and_(
                Payment.child_id == child.id,
                Payment.month == target_month
            )
        ).first()
        if existing:
            continue
        
        amount = calculate_fee_based_on_attendance(child.id, target_month, db, base_rate)
        if amount == 0:
            continue
        
        new_payment = Payment(
            child_id=child.id,
            month=target_month,
            amount=amount,
            paid_amount=0.0,
            status="pending",
            comment=f"Расчет на основе посещаемости ({base_rate} руб/день)"
        )
        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)
        
        results.append(PaymentResponse(
            id=new_payment.id,
            child_id=new_payment.child_id,
            child_name=child.full_name,
            month=new_payment.month,
            amount=new_payment.amount,
            paid_amount=new_payment.paid_amount,
            status=new_payment.status,
            comment=new_payment.comment,
            balance=new_payment.amount,
            created_at=new_payment.created_at,
            updated_at=new_payment.updated_at
        ))
    
    return results

# === ПОЛУЧЕНИЕ ПЛАТЕЖЕЙ РЕБЕНКА ===
@router.get("/child/{child_id}", response_model=List[PaymentResponse])
async def get_child_payments(
    child_id: int,
    start_month: Optional[date] = None,
    end_month: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Получить историю платежей ребенка"""
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Ребенок не найден")
    
    if current_user.role.value == "teacher":
        group = db.query(Group).filter(Group.id == child.group_id).first()
        if group and group.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет доступа к этому ребенку")
    
    query = db.query(Payment).filter(Payment.child_id == child_id)
    if start_month:
        query = query.filter(Payment.month >= start_month)
    if end_month:
        query = query.filter(Payment.month <= end_month)
    
    payments = query.order_by(Payment.month.desc()).all()
    
    return [
        PaymentResponse(
            id=p.id,
            child_id=p.child_id,
            child_name=child.full_name,
            month=p.month,
            amount=p.amount,
            paid_amount=p.paid_amount,
            status=p.status,
            comment=p.comment,
            balance=p.amount - p.paid_amount,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in payments
    ]

# === ОТЧЕТ ПО ГРУППЕ ===
@router.get("/report/group/{group_id}", response_model=PaymentReportResponse)
async def get_group_payment_report(
    group_id: int,
    month: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Получить финансовый отчет по группе за месяц"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    if current_user.role.value == "teacher":
        if group.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет доступа к этой группе")
    
    children = db.query(Child).filter(
        Child.group_id == group_id,
        Child.is_active == True
    ).all()
    child_ids = [c.id for c in children]
    
    payments = db.query(Payment).filter(
        and_(
            Payment.child_id.in_(child_ids),
            Payment.month == month
        )
    ).all()
    
    total_amount = sum(p.amount for p in payments)
    total_paid = sum(p.paid_amount for p in payments)
    total_balance = total_amount - total_paid
    paid_count = sum(1 for p in payments if p.status == "paid")
    pending_count = sum(1 for p in payments if p.status == "pending")
    overdue_count = sum(1 for p in payments if p.status == "overdue")
    
    payment_responses = [
        PaymentResponse(
            id=p.id,
            child_id=p.child_id,
            child_name=next((c.full_name for c in children if c.id == p.child_id), None),
            month=p.month,
            amount=p.amount,
            paid_amount=p.paid_amount,
            status=p.status,
            comment=p.comment,
            balance=p.amount - p.paid_amount,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in payments
    ]
    
    return PaymentReportResponse(
        month=month,
        group_id=group_id,
        group_name=group.name,
        total_children=len(children),
        total_amount=total_amount,
        total_paid=total_paid,
        total_balance=total_balance,
        paid_count=paid_count,
        pending_count=pending_count,
        overdue_count=overdue_count,
        payments=payment_responses
    )

# === ОБНОВЛЕНИЕ ПЛАТЕЖА ===
@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Обновить платеж (админ или бухгалтер)"""
    await check_accountant_or_admin(current_user)
    
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Платеж не найден")
    
    if payment_data.paid_amount is not None:
        payment.paid_amount = payment_data.paid_amount
    if payment_data.status is not None:
        payment.status = payment_data.status
    if payment_data.comment is not None:
        payment.comment = payment_data.comment
    
    payment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(payment)
    
    child = db.query(Child).filter(Child.id == payment.child_id).first()
    child_name = child.full_name if child else None
    balance = payment.amount - payment.paid_amount
    
    return PaymentResponse(
        id=payment.id,
        child_id=payment.child_id,
        child_name=child_name,
        month=payment.month,
        amount=payment.amount,
        paid_amount=payment.paid_amount,
        status=payment.status,
        comment=payment.comment,
        balance=balance,
        created_at=payment.created_at,
        updated_at=payment.updated_at
    )

# === УДАЛЕНИЕ ПЛАТЕЖА ===
@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Удалить платеж (только админ)"""
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Только администратор может удалять платежи")
    
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Платеж не найден")
    
    db.delete(payment)
    db.commit()
    return None