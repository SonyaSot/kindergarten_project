from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from datetime import datetime, timedelta
import random
import os
import sys

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@db:5432/kindergarten_db")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def hash_pwd(p): return pwd_context.hash(p)

def fix_schema(session):
    """Добавляет отсутствующие колонки, если их нет"""
    print(" Проверка схемы базы данных...")
    
    # 1. Исправляем таблицу users
    try:
        result = session.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'updated_at'
        """)).fetchone()
        if not result:
            print("    Добавляем column 'updated_at' в users...")
            session.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP"))
            
        result = session.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'group_id'
        """)).fetchone()
        if not result:
            print("    Добавляем column 'group_id' в users...")
            session.execute(text("ALTER TABLE users ADD COLUMN group_id INTEGER"))
            
    except Exception as e:
        print(f"    Ошибка при обновлении users: {e}")

    # 2. Исправляем таблицу children (has_discount)
    try:
        result = session.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'children' AND column_name = 'has_discount'
        """)).fetchone()
        if not result:
            print("    Добавляем column 'has_discount' в children...")
            session.execute(text("ALTER TABLE children ADD COLUMN has_discount BOOLEAN DEFAULT FALSE"))
        else:
            print("    Обнуляем NULL значения в has_discount...")
            session.execute(text("UPDATE children SET has_discount = FALSE WHERE has_discount IS NULL"))
            
    except Exception as e:
        print(f"    Ошибка при обновлении children: {e}")
    
    session.commit()
    print(" Схема базы данных актуальна!")

# --- СПИСКИ ИМЕН ДЛЯ ДЕТЕЙ ---
BOY_NAMES = [
    "Александр", "Максим", "Артем", "Даниил", "Михаил", "Иван", "Дмитрий", 
    "Егор", "Кирилл", "Никита", "Андрей", "Сергей", "Алексей", "Павел", "Роман"
]
GIRL_NAMES = [
    "София", "Анна", "Мария", "Виктория", "Алиса", "Полина", "Ева", 
    "Екатерина", "Дарья", "Ксения", "Ольга", "Наталья", "Елена", "Юлия", "Вероника"
]
LAST_NAMES = [
    "Иванов", "Смирнов", "Кузнецов", "Попов", "Васильев", "Петров", "Соколов", 
    "Михайлов", "Новиков", "Федоров", "Морозов", "Волков", "Алексеев", "Лебедев", "Семенов"
]

# Данные для родителей (теперь они будут совпадать с фамилиями детей для реалистичности)
PARENT_SUFFIXES = ["Иванович", "Петрович", "Сергеевич", "Александрович", "Дмитриевич"]
PARENT_MOTHER_SUFFIXES = ["Ивановна", "Петровна", "Сергеевна", "Александровна", "Дмитриевна"]


print(" ГЕНЕРАЦИЯ ТЕСТОВЫХ ДАННЫХ")


session = Session()

try:
    # 0. Сначала чиним схему БД
    fix_schema(session)

    # 1. Админ
    print("\n Пользователи:")
    session.execute(text("""
        INSERT INTO users (email, hashed_password, role, full_name, is_active)
        VALUES (:email, :pwd, 'ADMIN', 'Администратор Системы', true)
        ON CONFLICT (email) DO UPDATE SET hashed_password = EXCLUDED.hashed_password
    """), {"email": "admin@sadik.ru", "pwd": hash_pwd("admin123")})
    print(" Админ: admin@sadik.ru / admin123")
    
    # 2. Учителя
    print("\n‍ Учителя:")
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
        print(f" {name}: {email}")
    
    # 3. Группы и дети
    print("\n Группы и дети:")
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
            print(f"    Группа '{gname}' уже существует (ID: {gid})")
        else:
            result = session.execute(text("""
                INSERT INTO groups (name, age_range, teacher_id)
                VALUES (:name, :age, :tid)
                RETURNING id
            """), {"name": gname, "age": age, "tid": tid})
            gid = result.scalar()
            print(f"    Группа '{gname}' создана (ID: {gid})")
        
        # 4. Дети (15 в группе) - ГЕНЕРАЦИЯ ИМЕН
        child_ids = []
        used_names = set() # Чтобы имена не повторялись в одной группе
        
        for i in range(15):
            # Выбираем пол случайно
            is_boy = random.choice([True, False])
            
            # Генерируем имя, пока не получим уникальное для этой группы
            while True:
                first_name = random.choice(BOY_NAMES if is_boy else GIRL_NAMES)
                last_name = random.choice(LAST_NAMES)
                full_name = f"{last_name} {'Александр' if is_boy else 'Александра'}" # Отчество для красоты, но в БД только ФИО
                # Для простоты запишем просто Фамилия Имя
                child_full_name = f"{last_name} {first_name}"
                
                if child_full_name not in used_names:
                    used_names.add(child_full_name)
                    break
            
            # Генерируем данные родителя (фамилия та же)
            parent_first = "Иван" if is_boy else "Мария" # Упрощенно
            parent_name = f"{last_name} {parent_first} {random.choice(PARENT_SUFFIXES if is_boy else PARENT_MOTHER_SUFFIXES)}"
            parent_email = f"{last_name.lower()}.{i}@mail.ru"
            parent_phone = f"+7900{random.randint(1000000, 9999999)}"

            # Проверяем, нет ли уже такого ребёнка (по имени и группе)
            existing = session.execute(text("SELECT id FROM children WHERE full_name = :n AND group_id = :g"), 
                                     {"n": child_full_name, "g": gid}).fetchone()
            
            if existing:
                cid = existing[0]
            else:
                result = session.execute(text("""
                    INSERT INTO children (
                        full_name, date_of_birth, group_id, is_active,
                        parent_name, parent_phone, parent_email, has_discount
                    )
                    VALUES (:name, :dob, :gid, true, :pname, :pphone, :pemail, false)
                    RETURNING id
                """), {
                    "name": child_full_name,
                    "dob": datetime(2020, random.randint(1,12), random.randint(1,28)).date(),
                    "gid": gid,
                    "pname": parent_name,
                    "pphone": parent_phone,
                    "pemail": parent_email
                })
                cid = result.scalar()
                print(f"       Добавлен: {child_full_name} ({'мальчик' if is_boy else 'девочка'})")
            
            if cid:
                child_ids.append(cid)
                
        print(f"    В группе '{gname}' всего детей: {len(child_ids)}")
        
        # 5. Посещаемость (90 дней)
        statuses = ["PRESENT", "PRESENT", "PRESENT", "SICK", "ABSENT"]
        records_count = 0
        for cid in child_ids:
            for days_ago in range(90):
                date = datetime.now().date() - timedelta(days=days_ago)
                status = random.choice(statuses)
                
                exists = session.execute(text("""
                    SELECT id FROM attendance WHERE child_id = :cid AND date = :date
                """), {"cid": cid, "date": date}).fetchone()
                
                if not exists:
                    session.execute(text("""
                        INSERT INTO attendance (child_id, date, status, teacher_id)
                        VALUES (:cid, :date, :status, :tid)
                    """), {"cid": cid, "date": date, "status": status, "tid": tid})
                    records_count += 1
        print(f"    Посещаемость: {records_count} новых записей")
    
    session.commit()
    
    # 6. Статистика
    print("\n" + "=" * 60)
    stats = session.execute(text("""
        SELECT 
            (SELECT COUNT(*) FROM users WHERE role = 'ADMIN') as admins,
            (SELECT COUNT(*) FROM users WHERE role = 'TEACHER') as teachers,
            (SELECT COUNT(*) FROM groups) as groups,
            (SELECT COUNT(*) FROM children) as children,
            (SELECT COUNT(*) FROM attendance) as attendance_records
    """)).fetchone()
    
    print(" СТАТИСТИКА:")
    print(f"   Админы:       {stats[0]}")
    print(f"   Учителя:      {stats[1]}")
    print(f"   Группы:       {stats[2]}")
    print(f"   Дети:         {stats[3]}")
    print(f"   Посещаемость: {stats[4]} записей")
    
    print("\n ДАННЫЕ ДЛЯ ВХОДА:")
    print("   ADMIN:   admin@sadik.ru / admin123")
    print("   TEACHER1: sotnikova@sadik.ru / teacher123")
    print("   TEACHER2: vasilevskaya@sadik.ru / teacher123")
    print("=" * 60)
    print(" ГОТОВО!")
    
except Exception as e:
    session.rollback()
    print(f"\n ОШИБКА: {e}")
finally:
    session.close()