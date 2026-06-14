from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.task import Task


def get_users_with_failed_plan(db: Session):

    users = db.query(User).all()

    result = []

    for user in users:

        tasks = db.query(Task).filter(
            Task.assigned_user_id == user.id
        ).all()

        plan = 10

        if len(tasks) < plan:

            result.append({
                "user": user,
                "fact": len(tasks),
                "plan": plan
            })

    return result