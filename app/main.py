from fastapi import FastAPI
from app.database import engine, Base
from app.models import User, Group, Child, Attendance, Payment
from fastapi.middleware.cors import CORSMiddleware 


# Импортируем роутеры НАПРЯМУЮ из файлов (обходим __init__.py)
from app.routers.auth import router as auth_router
from app.routers.groups import router as groups_router
from app.routers.children import router as children_router
from app.routers.attendance import router as attendance_router
from app.routers.payments import router as payments_router
from app.routers import ai_predictions  
from app.routers import audit

# ✅ ДОБАВЬ ЭТУ СТРОКУ:
from app.routers import users

# Создаём таблицы в базе данных
try:
    Base.metadata.create_all(bind=engine)
    print(" Таблицы базы данных созданы успешно")
except Exception as e:
    print(f" Ошибка подключения к базе данных: {e}")

app = FastAPI(title="Детский сад - Учет посещаемости")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Для разработки. В продакшене укажите ["http://localhost:5500", "http://127.0.0.1:5500"]
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы: GET, POST, PUT, DELETE
    allow_headers=["*"],  # Разрешаем все заголовки
)

# 2. Audit Middleware (если он совместим с FastAPI)
# app.add_middleware(AuditMiddleware)  # ← раскомментируйте, если нужно
# Подключаем роутеры
app.include_router(auth_router)
app.include_router(groups_router)
app.include_router(children_router)
app.include_router(attendance_router)
app.include_router(payments_router)
app.include_router(ai_predictions.router) 
app.include_router(audit.router, tags=["Журнал действий"])

# ✅ ДОБАВЬ ЭТУ СТРОКУ:
app.include_router(users.router, tags=["Пользователи"])

@app.get("/")
async def root():
    return {"message": "Система работает! Этап 5 завершен."}

@app.get("/health")
async def health():
    return {"status": "ok"}