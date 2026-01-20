# run.py (Ensure it looks like this)
from app import create_app, db
from app.scheduler import start_scheduler

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Start the scheduler
        start_scheduler(app)

    # use_reloader=False prevents double notifications during development
    app.run(debug=True, use_reloader=False)
