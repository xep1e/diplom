from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.userApi import router as user_router

app = FastAPI(title="ЛК Аналитика")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # фронт
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Префикс API
app.include_router(user_router, prefix="/api/users", tags=["users"])

@app.get("/")
def root():
    return {"message": "Backend работает!"}