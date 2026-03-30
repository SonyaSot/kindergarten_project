from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Date, Float, Text, func
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum
from app.database import Base


# === ENUMS ===
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    ACCOUNTANT = "accountant"

class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    SICK = "sick"
    NOT_MARKED = "not_marked"

# === МОДЕЛЬ: Пользователь ===
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения (обрати внимание на back_populates)
    groups_as_teacher = relationship("Group", foreign_keys="Group.teacher_id", back_populates="teacher")
    attendance_records = relationship("Attendance", back_populates="teacher")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

# === МОДЕЛЬ: Группа ===
class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age_range = Column(String, nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="groups_as_teacher")
    children = relationship("Child", back_populates="group")

    def __repr__(self):
        return f"<Group {self.name}>"

# === МОДЕЛЬ: Ребенок ===
class Child(Base):
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    parent_name = Column(String, nullable=False)
    parent_phone = Column(String, nullable=True)
    parent_email = Column(String, nullable=True)
    has_discount = Column(Boolean, default=False)
    discount_reason = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Отношения
    group = relationship("Group", back_populates="children")
    attendance_records = relationship("Attendance", back_populates="child")
    payments = relationship("Payment", back_populates="child")

    def __repr__(self):
        return f"<Child {self.full_name}>"

# === МОДЕЛЬ: Посещаемость ===
class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.NOT_MARKED)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ✅ Отношения
    child = relationship("Child", back_populates="attendance_records")
    teacher = relationship("User", back_populates="attendance_records")

    def __repr__(self):
        return f"<Attendance {self.child_id} - {self.date} - {self.status}>"

# === МОДЕЛЬ: Оплата ===
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    month = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0)
    status = Column(String, default="pending")
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ✅ Отношения
    child = relationship("Child", back_populates="payments")

    def __repr__(self):
        return f"<Payment {self.child_id} - {self.month} - {self.amount}>"

 # === Журнал действий пользователей  ===
class AuditLog(Base):
   
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    resource = Column(String(50))  # children, groups, payments, users
    resource_id = Column(Integer, nullable=True)  # ID затронутого объекта
    details = Column(String(500), nullable=True)  # Дополнительные данные
    ip_address = Column(String(50), nullable=True)  # IP адрес клиента
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связь с пользователем
    user = relationship("User", backref="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action})>"