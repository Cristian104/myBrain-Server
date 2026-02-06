from app import create_app, db
from app.models import User
from app.modules.gym.models import GymRoutine, GymExercise, GymLog
from sqlalchemy import text


def reset_gym_data():
    app = create_app()
    with app.app_context():
        print("🧹 Cleaning Gym Data...")

        # 1. Delete all gym data
        try:
            num_logs = GymLog.query.delete()
            num_exercises = GymExercise.query.delete()
            num_routines = GymRoutine.query.delete()

            print(f"   - Deleted {num_logs} logs")
            print(f"   - Deleted {num_exercises} exercises")
            print(f"   - Deleted {num_routines} routines")
        except Exception as e:
            print(f"   Error deleting data: {e}")
            return

        # 2. Fix the NULL crash for Users
        print("🔧 Patching User Accounts...")
        users = User.query.all()
        count = 0
        for user in users:
            # If it's None or 0, set it to 1
            if not user.current_gym_day:
                user.current_gym_day = 1
                count += 1

        db.session.commit()
        print(f"   - Fixed 'current_gym_day' for {count} users.")

        print("✅ Gym module reset complete! Your Tasks and Account are safe.")


if __name__ == "__main__":
    reset_gym_data()
