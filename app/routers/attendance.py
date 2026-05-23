from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date, datetime
from app.database import get_db
from app.models import User, UserRole, Group, Child, Attendance, AttendanceStatus
from app.schemas.attendance import (
    AttendanceCreate, 
    AttendanceUpdate, 
    AttendanceResponse,
    BulkAttendanceCreate,
    DailyJournalResponse
)
from app.routers.auth import get_current_user_from_token


router = APIRouter(prefix="/attendance", tags=["Электронный журнал"])

async def check_teacher_access_to_group(
    group_id: int,
    current_user: User,
    db: Session
):
    """Проверка доступа учителя к группе"""
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    # ADMIN и ACCOUNTANT имеют доступ ко всем группам
    if current_user.role in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        return group
    
    # TEACHER имеет доступ ТОЛЬКО к своим группам
    if current_user.role == UserRole.TEACHER:
        if group.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет доступа к этой группе")
        return group
    
    # Другие роли (если появятся) - запрещаем
    raise HTTPException(status_code=403, detail="Недостаточно прав")

#  ПОЛУЧЕНИЕ ЖУРНАЛА ГРУППЫ ЗА ДАТУ
@router.get("/group/{group_id}/date/{target_date}", response_model=DailyJournalResponse)
async def get_daily_journal(
    group_id: int,
    target_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    
    # Проверка доступа
    group = await check_teacher_access_to_group(group_id, current_user, db)
    
    # Получаем всех активных детей группы
    children = db.query(Child).filter(
        Child.group_id == group_id,
        Child.is_active == True
    ).all()
    
    # Получаем существующие записи посещаемости
    existing_records = db.query(Attendance).filter(
        and_(
            Attendance.child_id.in_([c.id for c in children]),
            Attendance.date == target_date
        )
    ).all()
    
    # Создаем словарь существующих записей
    records_dict = {r.child_id: r for r in existing_records}
    
    # Формируем ответ
    attendance_records = []
    marked_count = 0
    unmarked_count = 0
    
    for child in children:
        if child.id in records_dict:
            record = records_dict[child.id]
            attendance_records.append(AttendanceResponse(
                id=record.id,
                child_id=record.child_id,
                child_name=child.full_name,
                teacher_id=record.teacher_id,
                date=record.date,
                status=record.status.value if hasattr(record.status, 'value') else record.status,
                comment=record.comment,
                created_at=record.created_at,
                updated_at=record.updated_at
            ))
            if record.status != AttendanceStatus.NOT_MARKED:
                marked_count += 1
            else:
                unmarked_count += 1
        else:
            # Записи нет - создаем временную с статусом NOT_MARKED
            attendance_records.append(AttendanceResponse(
                id=0,
                child_id=child.id,
                child_name=child.full_name,
                teacher_id=current_user.id,
                date=target_date,
                status="not_marked",
                comment=None,
                created_at=datetime.utcnow(),
                updated_at=None
            ))
            unmarked_count += 1
    
    return DailyJournalResponse(
        date=target_date,
        group_id=group_id,
        group_name=group.name,
        teacher_id=current_user.id if hasattr(current_user, 'id') else None,
        records=attendance_records,
        total_children=len(children),
        marked_count=marked_count,
        unmarked_count=unmarked_count
    )

# СОЗДАНИЕ/ОБНОВЛЕНИЕ ЗАПИСИ ПОСЕЩАЕМОСТИ 
@router.post("/", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def create_attendance(
    attendance_data: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):

    # Проверка доступа к группе ребенка
    child = db.query(Child).filter(Child.id == attendance_data.child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Ребенок не найден")
    
    await check_teacher_access_to_group(child.group_id, current_user, db)
    
    # Проверяем, есть ли уже запись за эту дату
    existing = db.query(Attendance).filter(
        and_(
            Attendance.child_id == attendance_data.child_id,
            Attendance.date == attendance_data.date
        )
    ).first()
    
    if existing:
        # Обновляем существующую запись
        existing.status = attendance_data.status
        existing.comment = attendance_data.comment
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return AttendanceResponse(
            id=existing.id,
            child_id=existing.child_id,
            child_name=child.full_name,
            teacher_id=existing.teacher_id,
            date=existing.date,
            status=existing.status.value if hasattr(existing.status, 'value') else existing.status,
            comment=existing.comment,
            created_at=existing.created_at,
            updated_at=existing.updated_at
        )
    else:
        # Создаем новую запись
        new_attendance = Attendance(
            child_id=attendance_data.child_id,
            teacher_id=current_user.id,
            date=attendance_data.date,
            status=attendance_data.status,
            comment=attendance_data.comment
        )
        db.add(new_attendance)
        db.commit()
        db.refresh(new_attendance)
        return AttendanceResponse(
            id=new_attendance.id,
            child_id=new_attendance.child_id,
            child_name=child.full_name,
            teacher_id=new_attendance.teacher_id,
            date=new_attendance.date,
            status=new_attendance.status.value if hasattr(new_attendance.status, 'value') else new_attendance.status,
            comment=new_attendance.comment,
            created_at=new_attendance.created_at,
            updated_at=new_attendance.updated_at
        )

#  МАССОВАЯ ОТМЕТКА ПОСЕЩАЕМОСТИ 
@router.post("/bulk", response_model=List[AttendanceResponse])
async def bulk_mark_attendance(
    bulk_data: BulkAttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    
    # Проверка доступа
    group = await check_teacher_access_to_group(bulk_data.group_id, current_user, db)
    
    # Получаем всех активных детей группы
    children = db.query(Child).filter(
        Child.group_id == bulk_data.group_id,
        Child.is_active == True
    ).all()
    
    results = []
    
    for child in children:
        # Определяем статус: из данных или по умолчанию
        status = bulk_data.attendance_data.get(child.id, bulk_data.default_status)
        
        # Проверяем, есть ли уже запись
        existing = db.query(Attendance).filter(
            and_(
                Attendance.child_id == child.id,
                Attendance.date == bulk_data.date
            )
        ).first()
        
        if existing:
            existing.status = status
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            results.append(AttendanceResponse(
                id=existing.id,
                child_id=existing.child_id,
                child_name=child.full_name,
                teacher_id=existing.teacher_id,
                date=existing.date,
                status=existing.status.value if hasattr(existing.status, 'value') else existing.status,
                comment=existing.comment,
                created_at=existing.created_at,
                updated_at=existing.updated_at
            ))
        else:
            new_attendance = Attendance(
                child_id=child.id,
                teacher_id=current_user.id,
                date=bulk_data.date,
                status=status,
                comment=None
            )
            db.add(new_attendance)
            db.commit()
            db.refresh(new_attendance)
            results.append(AttendanceResponse(
                id=new_attendance.id,
                child_id=new_attendance.child_id,
                child_name=child.full_name,
                teacher_id=new_attendance.teacher_id,
                date=new_attendance.date,
                status=new_attendance.status.value if hasattr(new_attendance.status, 'value') else new_attendance.status,
                comment=new_attendance.comment,
                created_at=new_attendance.created_at,
                updated_at=new_attendance.updated_at
            ))
    
    return results

#  ОБНОВЛЕНИЕ ЗАПИСИ ПОСЕЩАЕМОСТИ 
@router.put("/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
    attendance_id: int,
    attendance_data: AttendanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    
    record = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    
    # Проверка доступа к группе
    child = db.query(Child).filter(Child.id == record.child_id).first()
    if child:
        await check_teacher_access_to_group(child.group_id, current_user, db)
    
    # Обновляем поля
    if attendance_data.status is not None:
        record.status = attendance_data.status
    if attendance_data.comment is not None:
        record.comment = attendance_data.comment
    
    record.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    
    child_name = child.full_name if child else None
    return AttendanceResponse(
        id=record.id,
        child_id=record.child_id,
        child_name=child_name,
        teacher_id=record.teacher_id,
        date=record.date,
        status=record.status.value if hasattr(record.status, 'value') else record.status,
        comment=record.comment,
        created_at=record.created_at,
        updated_at=record.updated_at
    )

#  ПОЛУЧЕНИЕ ИСТОРИИ ПОСЕЩАЕМОСТИ РЕБЕНКА 
@router.get("/child/{child_id}/history", response_model=List[AttendanceResponse])
async def get_child_attendance_history(
    child_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Ребенок не найден")
    
    # Проверка доступа
    await check_teacher_access_to_group(child.group_id, current_user, db)
    
    # Базовый запрос
    query = db.query(Attendance).filter(Attendance.child_id == child_id)
    
    # Фильтры по датам
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)
    
    records = query.order_by(Attendance.date.desc()).all()
    
    return [
        AttendanceResponse(
            id=r.id,
            child_id=r.child_id,
            child_name=child.full_name,
            teacher_id=r.teacher_id,
            date=r.date,
            status=r.status.value if hasattr(r.status, 'value') else r.status,
            comment=r.comment,
            created_at=r.created_at,
            updated_at=r.updated_at
        )
        for r in records
    ]

# УДАЛЕНИЕ ЗАПИСИ ПОСЕЩАЕМОСТИ 
@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance(
    attendance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Только администратор может удалять записи посещаемости")
    
    record = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    
    db.delete(record)
    db.commit()
    return None
# Добавьте в конец файла app/routers/attendance.py:

@router.get("/stats/group/{group_id}")
async def get_attendance_stats(
    group_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Получить статистику посещаемости для группы за месяц"""
    
    # Проверка доступа
    await check_teacher_access_to_group(group_id, current_user, db)
    
    # Получаем детей группы
    children = db.query(Child).filter(
        Child.group_id == group_id,
        Child.is_active == True
    ).all()
    
    total_children = len(children)
    
    # Получаем записи за месяц
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    records = db.query(Attendance).filter(
        Attendance.child_id.in_([c.id for c in children]),
        Attendance.date >= start_date,
        Attendance.date < end_date
    ).all()
    
    # Статистика по дням
    from collections import defaultdict
    by_day = defaultdict(lambda: {"present": 0, "total": total_children})
    
    present_count = 0
    for record in records:
        day = record.date.day
        if record.status == AttendanceStatus.PRESENT:
            by_day[day]["present"] += 1
            present_count += 1
    
    total_possible = total_children * len(by_day)
    attendance_rate = (present_count / total_possible * 100) if total_possible > 0 else 0
    
    return {
        "total_children": total_children,
        "total_present": present_count,
        "total_days": len(by_day),
        "attendance_rate": round(attendance_rate, 1),
        "by_day": dict(by_day)
    }