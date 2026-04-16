from app.services.auth_service import hash_password
from app.db.database import SessionLocal
from app.db.models.user import User, UserRole

db = SessionLocal()

admin = User(
    username="admin",
    password_hash=hash_password("admin"),
    role=UserRole.admin
)

db.add(admin)
db.commit()
db.close()