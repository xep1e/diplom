from fastapi import APIRouter, Depends
from app.api.userApi import get_current_user
from app.db.database import SessionLocal
from app.db.models.user import User

router = APIRouter(prefix="/bitrix", tags=["bitrix"])

CLIENT_ID = "YOUR_BITRIX_APP_CLIENT_ID"
REDIRECT_URI = "http://localhost:8000/bitrix/callback"

@router.get("/connect")
def connect_bitrix(current_user: User = Depends(get_current_user)):
    url = (
        "https://oauth.bitrix.info/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={current_user.id}"
    )

    return {"url": url}