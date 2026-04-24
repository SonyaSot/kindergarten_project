"""
scripts/seed_data.py — ФИНАЛЬНАЯ ВЕРСИЯ 2
Добавлен teacher_id в attendance (обязательное поле)
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from datetime import datetime, timedelta
import random

DATABASE_URL = "postgresql://postgres:postgres123@db:5432/kindergarten_db"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def hash_pwd(p): return pwd_context.hash(p)

# Данные для родителей
PARENT_NAMES = ["Иванов Иван", "Петрова Мария", "Сидоров Пётр", "Козлова Анна", "Смирнова Елена"]
PARENT_PHONES = ["+79001112233", "+79004445566", "+79007778899", "+79001234567", "+79009876543"]
PARENT_EMAILS = ["parent1@test.ru", "parent2@test.ru", "parent3@test.ru", "parent4@test.ru", "parent5@test.ru"]

print("=" * 60) 
print("🌱 ГЕНЕРАЦИЯ ТЕСТОВЫХ ДАННЫХ")
print("=" * 60)

session = Session()

try:
    # 1. Админ
    print("\n👤 Пользователи:")
    session.execute(text("""
        INSERT INTO users (email, hashed_password, role, full_name, is_active)
        VALUES (:email, :pwd, 'ADMIN', 'Администратор', true)
        ON CONFLICT (email) DO UPDATE SET hashed_password = EXCLUDED.hashed_password
    """), {"email": "admin@sadik.ru", "pwd": hash_pwd("admin123")})
    print("✅ Админ: admin@sadik.ru / admin123")
    
    # 2. Учителя
    print("\n👨‍🏫 Учителя:")
    teachers = [
        ("sotnikova@sadik.ru", "sotnikova123", "Сотникова София Романовна"),
        ("vasilevskaya@sadik.ru", "vasilevskaya123", "Василевская Вероника Валерьевна"),
    ]
    teacher_ids = []
    for email, pwd, name in teachers:
        result = session.execute(text("""
            INSERT INTO users (email, hashed_password, role, full_name, is_active)
            VALUES (:email, :pwd, 'TEACHER', :name, true)
            ON CONFLICT (email) DO UPDATE SET hashed_password = EXCLUDED.hashed_password
            RETURNING id
        """), {"email": email, "pwd": hash_pwd(pwd), "name": name})
        tid = result.scalar()
        teacher_ids.append(tid)
        print(f"✅ {name}: {email}")
    
    # 3. Группы и дети
    print("\n📦 Группы и дети:")
    groups = [
        ("Солнышко", "3-4 года", teacher_ids[0]),
        ("Радуга", "3-4 года", teacher_ids[0]),
        ("Звёздочка", "4-5 лет", teacher_ids[1]),
        ("Капитошка", "4-5 лет", teacher_ids[1]),
    ]
    
    for group_idx, (gname, age, tid) in enumerate(groups):
        # Проверка/создание группы
        existing = session.execute(text("SELECT id FROM groups WHERE name = :n"), {"n": gname}).fetchone()
        if existing:
            gid = existing[0]
            print(f"   ⚠️ Группа '{gname}' уже существует (ID: {gid})")
        else:
            result = session.execute(text("""
                INSERT INTO groups (name, age_range, teacher_id)
                VALUES (:name, :age, :tid)
                RETURNING id
            """), {"name": gname, "age": age, "tid": tid})
            gid = result.scalar()
            print(f"   ✅ Группа '{gname}' создана (ID: {gid})")
        
        # 4. Дети (15 в группе)
        child_ids = []
        for i in range(15):
            parent_idx = i % len(PARENT_NAMES)
            # Проверяем, нет ли уже такого ребёнка
            existing = session.execute(text("SELECT id FROM children WHERE full_name = :n AND group_id = :g"), 
                                     {"n": f"Ребёнок {gname}-{i+1}", "g": gid}).fetchone()
            if existing:
                cid = existing[0]
            else:
                result = session.execute(text("""
                    INSERT INTO children (
                        full_name, date_of_birth, group_id, is_active,
                        parent_name, parent_phone, parent_email
                    )
                    VALUES (:name, :dob, :gid, true, :pname, :pphone, :pemail)
                    RETURNING id
                """), {
                    "name": f"Ребёнок {gname}-{i+1}",
                    "dob": datetime(2020, random.randint(1,12), random.randint(1,28)).date(),
                    "gid": gid,
                    "pname": PARENT_NAMES[parent_idx],
                    "pphone": PARENT_PHONES[parent_idx],
                    "pemail": PARENT_EMAILS[parent_idx]
                })
                cid = result.scalar()
            if cid:
                child_ids.append(cid)
        print(f"   👶 Детей в '{gname}': {len(child_ids)}")
        
        # 5. Посещаемость (90 дней) — С teacher_id!
        statuses = ["PRESENT", "PRESENT", "PRESENT", "SICK", "ABSENT"]
        records_count = 0
        for cid in child_ids:
            for days_ago in range(90):
                date = datetime.now().date() - timedelta(days=days_ago)
                status = random.choice(statuses)
                
                # Проверяем, нет ли уже записи на эту дату
                exists = session.execute(text("""
                    SELECT id FROM attendance WHERE child_id = :cid AND date = :date
                """), {"cid": cid, "date": date}).fetchone()
                
                if not exists:
                    # ✅ ДОБАВЛЯЕМ teacher_id (владелец группы)
                    session.execute(text("""
                        INSERT INTO attendance (child_id, date, status, teacher_id)
                        VALUES (:cid, :date, :status, :tid)
                    """), {"cid": cid, "date": date, "status": status, "tid": tid})
                    records_count += 1
        print(f"   📊 Посещаемость: {records_count} новых записей")
    
    # 6. Коммит
    session.commit()
    
    # 7. Статистика
    print("\n" + "=" * 60)
    stats = session.execute(text("""
        SELECT 
            (SELECT COUNT(*) FROM users WHERE role = 'ADMIN') as admins,
            (SELECT COUNT(*) FROM users WHERE role = 'TEACHER') as teachers,
            (SELECT COUNT(*) FROM groups) as groups,
            (SELECT COUNT(*) FROM children) as children,
            (SELECT COUNT(*) FROM attendance) as attendance_records
    """)).fetchone()
    
    print("📊 СТАТИСТИКА:")
    print(f"   Админы:       {stats[0]}")
    print(f"   Учителя:      {stats[1]}")
    print(f"   Группы:       {stats[2]}")
    print(f"   Дети:         {stats[3]}")
    print(f"   Посещаемость: {stats[4]} записей")
    
    print("\n🔐 ДАННЫЕ ДЛЯ ВХОДА:")
    print("   ADMIN:   admin@sadik.ru / admin123")
    print("   TEACHER1: sotnikova@sadik.ru / teacher123")
    print("   TEACHER2: vasilevskaya@sadik.ru / teacher123")
    print("=" * 60)
    print("✅ ГОТОВО!")
    
except Exception as e:
    session.rollback()
    print(f"\n❌ ОШИБКА: {e}")
    raise
finally:
    session.close()