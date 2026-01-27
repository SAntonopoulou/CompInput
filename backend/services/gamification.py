from sqlmodel import Session, select
from backend.models import User, Achievement, UserAchievement, Notification


def award_achievement(user: User, achievement_key: str, session: Session):
    """
    Awards an achievement to a user if they don't already have it.
    This function does not commit the session.
    """
    # Check if the user already has the achievement by joining with the Achievement table
    statement = (
        select(UserAchievement)
        .join(Achievement)
        .where(
            UserAchievement.user_id == user.id,
            Achievement.key == achievement_key,
        )
    )
    existing_user_achievement = session.exec(statement).first()

    if existing_user_achievement:
        return  # User already has this achievement

    # Find the achievement
    statement = select(Achievement).where(Achievement.key == achievement_key)
    achievement = session.exec(statement).one_or_none()

    if not achievement:
        # In a real application, you might want to log this error
        print(f"ERROR: Achievement with key '{achievement_key}' not found.")
        return

    # Create the link table entry
    user_achievement = UserAchievement(user_id=user.id, achievement_id=achievement.id)
    session.add(user_achievement)

    # Create a notification for the user
    notification = Notification(
        user_id=user.id,
        message=f"You've unlocked a new achievement: {achievement.name}!",
        link="/profile/me?tab=achievements",
    )
    session.add(notification)

    # The calling function is responsible for session.commit()
