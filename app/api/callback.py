from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
import requests

BITRIX_TOKEN_URL = "https://oauth.bitrix.info/oauth/token"
FRONTEND_URL = "http://localhost:5173/profile"

@router.get("/callback")
def callback(code: str, state: int, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == state).first()

    if not user:
        return RedirectResponse(f"{FRONTEND_URL}?bitrix=error_user")

    # 1. exchange code → token
    res = requests.get(BITRIX_TOKEN_URL, params={
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    })

    data = res.json()

    if "access_token" not in data:
        return RedirectResponse(f"{FRONTEND_URL}?bitrix=error_token")

    # 2. get bitrix user
    user_info = requests.get(
        f"{data['client_endpoint']}user.current",
        params={"auth": data["access_token"]}
    ).json()

    bitrix_id = user_info["result"]["ID"]

    # 3. save
    user.bitrix_user_id = int(bitrix_id)
    user.bitrix_access_token = data["access_token"]
    user.bitrix_refresh_token = data.get("refresh_token")

    db.commit()

    return RedirectResponse(f"{FRONTEND_URL}?bitrix=success")