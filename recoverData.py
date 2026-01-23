from app import create_app, db
from app.models import User, Task, TaskHistory
from datetime import datetime

app = create_app()


def restore():
    with app.app_context():
        # 1. Get the User 'jorg' (created by init_db.py)
        user = User.query.filter_by(username='jorg').first()
        if not user:
            print("❌ User 'jorg' not found. Please run init_db.py first!")
            return

        print(f"👤 Restoring data for user: {user.username} (ID: {user.id})")

        # --- RESTORE TASKS ---
        print("📥 Restoring Tasks...")

        # Helper to parse dates with or without microseconds
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

        # Task 5: Spot Assessment
        t5 = Task(
            content='Complete Spot Assessment for all tasks',
            priority='high',
            category='work',
            complete=True,
            user_id=user.id,
            due_date=parse_date('2026-01-21 00:00:00.000000'),
            last_completed=parse_date('2026-01-21 17:03:57.712758'),
            color='#9b59b6',
            recurrence='none',
            is_habit=False,
            created_date=datetime.now()  # Default for new schema
        )
        db.session.add(t5)

        # Task 6: Gabriela's Party
        t6 = Task(
            content="Gabriela's Party",
            priority='normal',
            category='personal',
            complete=False,
            user_id=user.id,
            due_date=parse_date('2026-01-23 00:00:00.000000'),
            color='#2ecc71',
            recurrence='none',
            is_habit=False,
            created_date=datetime.now()
        )
        db.session.add(t6)

        # Task 7: Medication
        t7 = Task(
            content='Medication',
            priority='high',
            category='health',
            complete=True,
            user_id=user.id,
            due_date=parse_date('2026-01-24 08:46:22.192834'),
            last_completed=parse_date('2026-01-23 08:46:22.192805'),
            color='#e74c3c',
            recurrence='daily',
            is_habit=True,
            created_date=datetime.now()
        )
        db.session.add(t7)

        # Task 8: Fill Ebadu
        t8 = Task(
            content='Fill Ebadu',
            priority='urgent',
            category='work',
            complete=False,
            user_id=user.id,
            due_date=parse_date('2026-01-25 00:00:00.000000'),
            color='#e74c3c',
            recurrence='none',
            is_habit=False,
            created_date=datetime.now()
        )
        db.session.add(t8)

        # Commit tasks so they get IDs
        db.session.commit()

        # --- RESTORE HISTORY ---
        print("📥 Restoring History...")

        # Note: We use the Python objects (t5, t7) to get the NEW IDs automatically

        # Task 7 (Medication) history
        h1 = TaskHistory(task_id=t7.id, user_id=user.id, completed_date=datetime.strptime(
            '2026-01-21', '%Y-%m-%d').date())
        h3 = TaskHistory(task_id=t7.id, user_id=user.id, completed_date=datetime.strptime(
            '2026-01-22', '%Y-%m-%d').date())
        h4 = TaskHistory(task_id=t7.id, user_id=user.id, completed_date=datetime.strptime(
            '2026-01-23', '%Y-%m-%d').date())

        # Task 5 (Spot Assess) history
        h2 = TaskHistory(task_id=t5.id, user_id=user.id, completed_date=datetime.strptime(
            '2026-01-21', '%Y-%m-%d').date())

        db.session.add_all([h1, h2, h3, h4])
        db.session.commit()

        print("✅ Data Restoration Complete! You are ready to login.")


if __name__ == '__main__':
    restore()
