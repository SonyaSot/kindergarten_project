from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Group, User
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse
from app.routers.auth import get_current_user_from_token

router = APIRouter(prefix="/groups", tags=["Группы"])

# ПОЛУЧИТЬ МОИ ГРУППЫ 
@router.get("/me", response_model=List[GroupResponse])
async def get_my_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
   
    if current_user.role.value == "teacher":
        # Воспитатель видит только группы, где он teacher_id
        groups = db.query(Group).filter(Group.teacher_id == current_user.id).all()
    else:
        # Админ и бухгалтер видят все группы
        groups = db.query(Group).all()
    return groups

#  СОЗДАНИЕ ГРУППЫ 
@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Только администратор может создавать группы")
    
    new_group = Group(
        name=group_data.name,
        age_range=group_data.age_range,
        teacher_id=group_data.teacher_id
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group

# ПОЛУЧЕНИЕ ВСЕХ ГРУПП 
@router.get("/", response_model=List[GroupResponse])
async def get_all_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    # Воспитатель видит только свои группы
    if current_user.role.value == "teacher":
        groups = db.query(Group).filter(Group.teacher_id == current_user.id).all()
    else:
        groups = db.query(Group).all()
    return groups

#  ПОЛУЧЕНИЕ ОДНОЙ ГРУППЫ 
@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    # Воспитатель видит только свои группы
    if current_user.role.value == "teacher" and group.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой группе")
    
    return group

#  ОБНОВЛЕНИЕ ГРУППЫ 
@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    group_data: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Только администратор может редактировать группы")
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    # Обновляем только указанные поля
    if group_data.name is not None:
        group.name = group_data.name
    if group_data.age_range is not None:
        group.age_range = group_data.age_range
    if group_data.teacher_id is not None:
        group.teacher_id = group_data.teacher_id
    
    db.commit()
    db.refresh(group)
    return group

# УДАЛЕНИЕ ГРУППЫ 
@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Только администратор может удалять группы")
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    db.delete(group)
    db.commit()
    return None

