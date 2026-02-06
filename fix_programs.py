from app import create_app, db
from app.modules.gym.models import GymRoutine, GymProgram
from app.models import User

def fix_orphaned_routines():
    app = create_app()
    with app.app_context():
        # Get your user
        user = User.query.first() 
        
        # Get or Create the active program
        program = GymProgram.query.filter_by(user_id=user.id, is_active=True).first()
        if not program:
            program = GymProgram(user_id=user.id, name="My First Program", is_active=True)
            db.session.add(program)
            db.session.commit()
            print("✅ Created new active program.")

        # Find routines with NO program
        orphans = GymRoutine.query.filter_by(user_id=user.id, program_id=None).all()
        
        if orphans:
            print(f"🧐 Found {len(orphans)} hidden routines. Linking them now...")
            for r in orphans:
                r.program_id = program.id
            db.session.commit()
            print("🎉 Success! All routines are now visible in the dashboard.")
        else:
            print("✅ No hidden routines found.")

if __name__ == "__main__":
    fix_orphaned_routines()