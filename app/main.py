from fastapi import FastAPI
from app.database import engine, Base
from app.models import User, Group, Child, Attendance, Payment


# Импортируем роутеры НАПРЯМУЮ из файлов (обходим __init__.py)
from app.routers.auth import router as auth_router
from app.routers.groups import router as groups_router
from app.routers.children import router as children_router
from app.routers.attendance import router as attendance_router
from app.routers.payments import router as payments_router
from app.routers import ai_predictions  
from app.routers import audit

# Создаём таблицы в базе данных
try:
    Base.metadata.create_all(bind=engine)
    print(" Таблицы базы данных созданы успешно")
except Exception as e:
    print(f" Ошибка подключения к базе данных: {e}")

app = FastAPI(title="Детский сад - Учет посещаемости")

# Подключаем роутеры
app.include_router(auth_router)
app.include_router(groups_router)
app.include_router(children_router)
app.include_router(attendance_router)
app.include_router(payments_router)
app.include_router(ai_predictions.router) 
app.include_router(audit.router, tags=["Журнал действий"])

@app.get("/")
async def root():
    return {"message": "Система работает! Этап 5 завершен."}

@app.get("/health")
async def health():
    return {"status": "ok"}