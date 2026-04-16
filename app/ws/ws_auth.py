from jose import jwt, JWTError

SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"


def get_user_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "user_id": payload.get("user_id"),
            "role": payload.get("role"),
            "username": payload.get("username"),
        }
    except JWTError:
        return None