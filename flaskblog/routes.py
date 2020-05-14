import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, TaskForm
from flaskblog.models import User, Task
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
@app.route("/home")

@login_required
def home():
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=current_user.username).first_or_404()
    tasks = Task.query.filter_by(author=user) \
        .order_by(Task.date_posted.desc()) \
        .paginate(page=page, per_page=5)
    return render_template('user_tasks.html', posts=tasks, user=user)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@app.route("/task/new", methods=['GET', 'POST'])
@login_required
def new_task():
    tasks = Task.query.filter_by(author=current_user).all()
    if len(tasks) >= 50:
        flash('You can not add more than 50 tasks', 'danger')
        return redirect(url_for('home'))
    else:
        form = TaskForm()
        if form.validate_on_submit():
            file = None
            if form.file.data:
                file = save_picture(form.file.data)
            task = Task(title=form.title.data, content=form.content.data, author=current_user,
                        due_date = form.due_date.data, completion = form.completion.data,
                        completion_date = form.completion_date.data, attachment = file)

            print('lol : ', file)
            db.session.add(task)
            db.session.commit()
            flash('Your task has been created!', 'success')
            return redirect(url_for('home'))
        return render_template('create_task.html', title='New Task',
                               form=form, legend='New Task')


@app.route("/task/<int:task_id>")
def task(task_id):
    task = Task.query.get_or_404(task_id)
    return render_template('task.html', title=task.title, post=task)


@app.route("/task/<int:task_id>/update", methods=['GET', 'POST'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.author != current_user:
        abort(403)
    form = TaskForm()
    if form.validate_on_submit():
        task.title = form.title.data
        task.content = form.content.data
        db.session.commit()
        flash('Your task has been updated!', 'success')
        return redirect(url_for('task', task_id=task.id))
    elif request.method == 'GET':
        form.title.data = task.title
        form.content.data = task.content
    return render_template('create_task.html', title='Update Task',
                           form=form, legend='Update Task')


@app.route("/task/<int:task_id>/delete", methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.author != current_user:
        abort(403)
    db.session.delete(task)
    db.session.commit()
    flash('Your task has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
@login_required
def user_tasks(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    tasks = Task.query.filter_by(author=user)\
        .order_by(Task.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_tasks.html', posts=tasks, user=user)