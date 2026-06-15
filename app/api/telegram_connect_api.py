from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from uuid import uuid4

from app.db.database import SessionLocal

from app.api.userApi import (
    get_current_user
)

from app.db.models.user import (
    User
)

router = APIRouter(
    prefix="/telegram"
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


@router.post(
    "/generate-token"
)
def generate_token(
        current_user: User = Depends(
            get_current_user
        ),
        db: Session = Depends(
            get_db
        )
):

    # получаем пользователя
    user = (
        db.query(User)
        .filter(
            User.id
            ==
            current_user.id
        )
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )

    token = (
        str(uuid4())
        [:8]
        .upper()
    )

    user.telegram_connect_token = token

    db.add(user)

    db.commit()

    db.refresh(user)

    print(
        f"TG TOKEN сохранен: "
        f"{user.username} → "
        f"{token}"
    )

    return {

        "token": token,

        "command":
        f"/connect {token}"

    }