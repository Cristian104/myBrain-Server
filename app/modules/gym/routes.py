from datetime import datetime
import os
from flask import current_app
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.modules.gym.models import GymRoutine, GymExercise, GymProgram, GymExerciseLibrary

gym_bp = Blueprint('gym', __name__, url_prefix='/gym')

# --- DASHBOARD ---


@gym_bp.route('/')
@login_required
def index():
    active_program = GymProgram.query.filter_by(
        user_id=current_user.id, is_active=True).first()

    # Auto-create default program if none exists
    if not active_program:
        # Create program AND the 7 default days
        active_program = GymProgram(
            user_id=current_user.id, name="My First Program", is_active=True)
        db.session.add(active_program)
        db.session.flush()

        for i in range(1, 8):
            day = GymRoutine(
                user_id=current_user.id, program_id=active_program.id, name="Rest Day", order_index=i)
            db.session.add(day)
        db.session.commit()

    routines = GymRoutine.query.filter_by(
        program_id=active_program.id).order_by(GymRoutine.order_index).all()

    # Ensure we strictly have 7 days (Self-Healing if data is weird)
    if len(routines) < 7:
        current_count = len(routines)
        for i in range(current_count + 1, 8):
            new_day = GymRoutine(
                user_id=current_user.id, program_id=active_program.id, name="Rest Day", order_index=i)
            db.session.add(new_day)
        db.session.commit()
        routines = GymRoutine.query.filter_by(
            program_id=active_program.id).order_by(GymRoutine.order_index).all()

    # Next Up Logic
    current_day_idx = current_user.current_gym_day or 1
    next_routine = GymRoutine.query.filter_by(
        program_id=active_program.id, order_index=current_day_idx).first()

    # If current day is missing (e.g. index 8), reset to 1
    if not next_routine:
        current_user.current_gym_day = 1
        db.session.commit()
        next_routine = GymRoutine.query.filter_by(
            program_id=active_program.id, order_index=1).first()

    return render_template('gym/index.html', routines=routines, next_routine=next_routine, program=active_program)

# --- PROGRAM MANAGEMENT ---


@gym_bp.route('/programs')
@login_required
def programs():
    programs_list = GymProgram.query.filter_by(
        user_id=current_user.id).order_by(GymProgram.created_at.desc()).all()
    return render_template('gym/programs.html', programs=programs_list)


@gym_bp.route('/program/create', methods=['POST'])
@login_required
def create_program():
    name = request.form.get('name')
    if name:
        GymProgram.query.filter_by(
            user_id=current_user.id).update({'is_active': False})

        new_prog = GymProgram(user_id=current_user.id,
                              name=name, is_active=True)
        db.session.add(new_prog)
        db.session.flush()

        # ⚡ AUTO-GENERATE 7 REST DAYS
        for i in range(1, 8):
            day = GymRoutine(
                user_id=current_user.id, program_id=new_prog.id, name="Rest Day", order_index=i)
            db.session.add(day)

        current_user.current_gym_day = 1
        db.session.commit()
        flash(f'Started 7-Day Cycle: {name}', 'success')

    return redirect(url_for('gym.index'))


@gym_bp.route('/program/duplicate/<int:program_id>', methods=['POST'])
@login_required
def duplicate_program(program_id):
    source = GymProgram.query.get_or_404(program_id)
    new_prog = GymProgram(user_id=current_user.id,
                          name=f"Copy of {source.name}", is_active=False)
    db.session.add(new_prog)
    db.session.flush()

    # Duplicate existing days exactly as they are
    for r in source.routines:
        # Don't duplicate beyond 7 just in case old data was bad
        if r.order_index > 7:
            continue

        new_routine = GymRoutine(user_id=current_user.id, program_id=new_prog.id,
                                 name=r.name, order_index=r.order_index, notes=r.notes)
        db.session.add(new_routine)
        db.session.flush()

        for ex in r.exercises:
            new_ex = GymExercise(routine_id=new_routine.id, name=ex.name, name_es_display=ex.name_es_display,
                                 target_sets=ex.target_sets, target_reps=ex.target_reps, library_id=ex.library_id)
            db.session.add(new_ex)

    db.session.commit()
    flash('Program copied successfully!', 'success')
    return redirect(url_for('gym.programs'))


@gym_bp.route('/program/activate/<int:program_id>')
@login_required
def activate_program(program_id):
    GymProgram.query.filter_by(
        user_id=current_user.id).update({'is_active': False})
    prog = GymProgram.query.get_or_404(program_id)
    prog.is_active = True
    current_user.current_gym_day = 1
    db.session.commit()
    return redirect(url_for('gym.index'))

# --- ROUTINE EDITING (NEW LOGIC) ---


@gym_bp.route('/routine/update_name/<int:routine_id>', methods=['POST'])
@login_required
def update_routine_name(routine_id):
    routine = GymRoutine.query.get_or_404(routine_id)
    new_name = request.form.get('name')
    if new_name:
        routine.name = new_name
        db.session.commit()
        flash('Day updated', 'success')
    return redirect(url_for('gym.index'))


@gym_bp.route('/routine/swap/<int:routine_id>/<direction>')
@login_required
def swap_routine(routine_id, direction):
    """Sorts days by swapping them Up or Down"""
    current_r = GymRoutine.query.get_or_404(routine_id)
    program_id = current_r.program_id
    current_idx = current_r.order_index

    target_idx = current_idx - 1 if direction == 'up' else current_idx + 1

    # Boundary checks
    if target_idx < 1 or target_idx > 7:
        return redirect(url_for('gym.index'))

    target_r = GymRoutine.query.filter_by(
        program_id=program_id, order_index=target_idx).first()

    if target_r:
        # Swap indices
        current_r.order_index = target_idx
        target_r.order_index = current_idx
        db.session.commit()

    return redirect(url_for('gym.index'))


@gym_bp.route('/skip_day')
@login_required
def skip_day():
    current = current_user.current_gym_day or 1
    # Simple 1-7 loop
    if current >= 7:
        current_user.current_gym_day = 1
    else:
        current_user.current_gym_day = current + 1
    db.session.commit()
    return redirect(url_for('gym.index'))

# --- EXERCISES (Keep same) ---


@gym_bp.route('/routine/<int:routine_id>')
@login_required
def view_routine(routine_id):
    routine = GymRoutine.query.get_or_404(routine_id)
    return render_template('gym/routine_detail.html', routine=routine)


@gym_bp.route('/api/search_exercises')
@login_required
def search_exercises():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    results = GymExerciseLibrary.query.filter((GymExerciseLibrary.user_id == current_user.id) & (
        (GymExerciseLibrary.name_en.ilike(f'%{query}%')) | (GymExerciseLibrary.name_es.ilike(f'%{query}%')))).limit(5).all()
    data = []
    for ex in results:
        data.append({'name_en': ex.name_en, 'name_es': ex.name_es,
                    'default_sets': ex.default_sets, 'default_reps': ex.default_reps})
    return jsonify(data)


# [Inside app/modules/gym/routes.py]

@gym_bp.route('/routine/<int:routine_id>/add_exercise', methods=['POST'])
@login_required
def add_exercise(routine_id):
    routine = GymRoutine.query.get_or_404(routine_id)

    name_input = request.form.get('name')
    library_id_input = request.form.get(
        'library_id')  # Hidden ID from autocomplete
    save_to_lib = request.form.get('save_to_library')  # Checkbox

    sets = request.form.get('sets')
    reps = request.form.get('reps')

    if name_input:
        selected_lib_id = None

        # CASE 1: User selected an existing template from dropdown
        if library_id_input:
            selected_lib_id = library_id_input

        # CASE 2: User checked "Save as Template" (Create new)
        elif save_to_lib == 'on':
            # Check if it already exists to avoid dupes
            existing = GymExerciseLibrary.query.filter_by(
                user_id=current_user.id, name_en=name_input).first()
            if existing:
                selected_lib_id = existing.id
            else:
                new_lib_item = GymExerciseLibrary(
                    user_id=current_user.id,
                    name_en=name_input,
                    default_sets=int(sets) if sets else 3,
                    default_reps=reps or "8-12"
                )
                db.session.add(new_lib_item)
                db.session.commit()
                selected_lib_id = new_lib_item.id

        # CASE 3: Standard one-off exercise (selected_lib_id remains None)

        new_exercise = GymExercise(
            routine_id=routine.id,
            library_id=selected_lib_id,  # Can be None now!
            name=name_input,  # We always save the name
            target_sets=int(sets) if sets else 3,
            target_reps=reps or "8-12"
        )
        db.session.add(new_exercise)
        db.session.commit()
        flash(f'Added {name_input}', 'success')

    return redirect(url_for('gym.view_routine', routine_id=routine_id))


@gym_bp.route('/exercise/promote/<int:exercise_id>')
@login_required
def promote_exercise(exercise_id):
    """Takes a standalone exercise and saves it to the Library"""
    ex = GymExercise.query.get_or_404(exercise_id)

    # Check if already exists in library
    existing = GymExerciseLibrary.query.filter_by(
        user_id=current_user.id, name_en=ex.name).first()

    if existing:
        ex.library_id = existing.id
        flash(f'Linked "{ex.name}" to existing template.', 'info')
    else:
        # Create new template
        new_lib = GymExerciseLibrary(
            user_id=current_user.id,
            name_en=ex.name,
            default_sets=ex.target_sets,
            default_reps=ex.target_reps
        )
        db.session.add(new_lib)
        db.session.commit()
        ex.library_id = new_lib.id
        flash(f'Saved "{ex.name}" as a new template!', 'success')

    db.session.commit()
    return redirect(url_for('gym.view_routine', routine_id=ex.routine_id))


@gym_bp.route('/exercise/delete/<int:exercise_id>')
@login_required
def delete_exercise(exercise_id):
    # 1. Get the exercise
    exercise = GymExercise.query.get_or_404(exercise_id)

    # 2. Save the routine ID (because we are about to delete the exercise)
    routine_id = exercise.routine_id

    # 3. Verify ownership
    if exercise.routine.user_id == current_user.id:
        db.session.delete(exercise)
        db.session.commit()
        flash('Exercise removed', 'success')

    # 4. Redirect explicitly naming the argument
    return redirect(url_for('gym.view_routine', routine_id=routine_id))


# --- LIBRARY MANAGEMENT ---

@gym_bp.route('/library')
@login_required
def library():
    exercises = GymExerciseLibrary.query.filter_by(
        user_id=current_user.id).order_by(GymExerciseLibrary.name_en).all()
    return render_template('gym/library.html', exercises=exercises)


@gym_bp.route('/library/update/<int:ex_id>', methods=['POST'])
@login_required
def update_library_item(ex_id):
    item = GymExerciseLibrary.query.get_or_404(ex_id)
    if item.user_id != current_user.id:
        return redirect(url_for('gym.library'))

    # Update text fields
    item.name_en = request.form.get('name_en')
    item.name_es = request.form.get('name_es')
    item.default_sets = request.form.get('default_sets')
    item.default_reps = request.form.get('default_reps')
    item.video_url = request.form.get('video_url')

    # Handle File Upload
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename != '':
            filename = secure_filename(
                f"user_{current_user.id}_{datetime.now().timestamp()}_{file.filename}")

            # Ensure directory exists
            upload_folder = os.path.join(
                current_app.root_path, 'static', 'uploads', 'gym')
            os.makedirs(upload_folder, exist_ok=True)

            file.save(os.path.join(upload_folder, filename))
            item.image_filename = filename

    db.session.commit()
    flash('Template updated!', 'success')
    return redirect(url_for('gym.library'))


@gym_bp.route('/library/delete/<int:ex_id>')
@login_required
def delete_library_item(ex_id):
    item = GymExerciseLibrary.query.get_or_404(ex_id)

    # Security check: Ensure user owns this item
    if item.user_id != current_user.id:
        return redirect(url_for('gym.library'))

    # 👇 STEP 1: CONVERT LINKED EXERCISES TO "NORMAL"
    # We find every past exercise that used this template
    linked_exercises = GymExercise.query.filter_by(library_id=item.id).all()

    # We cut the link, preserving the name/sets/reps in the history
    for ex in linked_exercises:
        ex.library_id = None

    # 👇 STEP 2: DELETE THE FILE (Clean up storage)
    if item.image_filename:
        try:
            file_path = os.path.join(
                current_app.root_path, 'static', 'uploads', 'gym', item.image_filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")

    # 👇 STEP 3: DELETE THE TEMPLATE
    db.session.delete(item)
    db.session.commit()

    flash('Template deleted. Past workouts converted to standalone exercises.', 'success')
    return redirect(url_for('gym.library'))
