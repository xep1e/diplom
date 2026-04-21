from jose import jwt, JWTError

SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"


def get_user_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"🔐 Декодирован токен: {payload}")  # Отладка

        # 🔥 ИСПРАВЛЕНО: берем user_id из поля "sub"
        return {
            "user_id": payload.get("sub"),  # 👈 ЗДЕСЬ БЫЛО "user_id", НУЖНО "sub"
            "role": payload.get("role"),
            "username": payload.get("username"),
        }
    except JWTError as e:
        print(f"❌ Ошибка токена: {e}")
        return None