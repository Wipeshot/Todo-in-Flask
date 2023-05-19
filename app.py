from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import func
from wtforms import StringField, DateField, IntegerField, PasswordField
from wtforms.validators import DataRequired, Optional, Email
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SECRET_KEY'] = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
db = SQLAlchemy(app)


class TodoForm(FlaskForm):
    value = StringField('Value', validators=[DataRequired()])
    start = DateField('Start', validators=[DataRequired()])
    deadline = DateField('Deadline', validators=[Optional()])
    priority = IntegerField('Priority', validators=[DataRequired()])


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(200), nullable=False)
    start = db.Column(db.Date, nullable=False)
    end = db.Column(db.Date)
    deadline = db.Column(db.Date)
    priority = db.Column(db.Integer)
    position = db.Column(db.Integer)
    open = db.Column(db.Boolean)
    user = db.Column(db.Integer, db.ForeignKey('user.id'))


class RegisterForm(FlaskForm):
    username = StringField(validators=[DataRequired()])
    email = StringField(validators=[Email()])
    password = PasswordField(validators=[DataRequired()])


class LoginForm(FlaskForm):
    username = StringField(validators=[DataRequired()])
    password = PasswordField(validators=[DataRequired()])


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)


with app.app_context():
    db.create_all()

activeFilter = 'none'


def generate_hashed_password(password):
    return password


def decrypt_hashed_password(hashed_password):
    password = hashed_password
    return password


def login_session(user):
    session['user'] = user.id
    session['exp'] = datetime.utcnow() + timedelta(hours=2)
    return True


def check_login(username, password):
    user = User.query.filter_by(username=username).first()
    if user is not None and user.password == password:
        return True
    else:
        return False


def check_for_unique(username, email):
    username_unique = User.query.filter_by(username=username).first()
    email_unique = User.query.filter_by(email=email).first()
    if username_unique is None and email_unique is None:
        return True
    else:
        return False


def require_login(func):
    @wraps(func)
    def check_session(*args, **kwargs):
        with app.app_context():
            if 'exp' not in session or session['exp'] < datetime.now(timezone.utc):
                return redirect(url_for('login'))
            elif User.query.filter_by(id=session['user']).first() is None:
                return redirect(url_for('login'))
        return func(*args, **kwargs)

    return check_session


@app.route('/register', methods=['GET', 'POST'])
def register():
    session['user'] = None
    if request.method == 'GET':
        return render_template('register.html', form=RegisterForm)
    elif request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_hashed_password(request.form['password'])
        if check_for_unique(username, email):
            db.session.add(User(username=username, email=email, password=password))
            db.session.commit()
            login_session(User.query.filter_by(username=username).first())
            return redirect(url_for('index'))
        else:
            return redirect('/register')


@app.route('/login', methods=['GET', 'POST'])
def login():
    session['user'] = None
    if request.method == 'GET':
        return render_template('login.html', form=LoginForm)
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_login(username, password):
            login_session(User.query.filter_by(username=username).first())
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))


@app.route('/')
@require_login
def index():
    global activeFilter
    todos_query = Todo.query.filter_by(open=True, user=session['user'])
    if activeFilter == 'none':
        todos_query = todos_query.order_by(Todo.position.asc())
    elif activeFilter == 'prio_asc':
        todos_query = todos_query.order_by(Todo.priority.asc())
    elif activeFilter == 'prio_desc':
        todos_query = todos_query.order_by(Todo.priority.desc())
    elif activeFilter == 'deadline_asc':
        todos_query = todos_query.order_by(Todo.deadline.asc())
    elif activeFilter == 'deadline_desc':
        todos_query = todos_query.order_by(Todo.deadline.desc())
    todos = todos_query.all()
    finished_todos_query = Todo.query.filter_by(open=False)
    finished_todos = finished_todos_query.all()
    filters = [
        {'value': 'none', 'label': 'Standard'},
        {'value': 'prio_asc', 'label': 'Priorität (aufsteigend)'},
        {'value': 'prio_desc', 'label': 'Priorität (absteigend)'},
        {'value': 'deadline_asc', 'label': 'Deadline (aufsteigend)'},
        {'value': 'deadline_desc', 'label': 'Deadline (absteigend)'}
    ]
    return render_template('todo-list.html', todos=todos, closed_todos=finished_todos, filters=filters,
                           activeFilter=activeFilter)


@app.route('/add', methods=['POST'])
@require_login
def add_todo():
    try:
        value = request.form['value']
        start = datetime.now()
        deadline_str = request.form.get('deadline')
        if deadline_str:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        else:
            deadline = None
        priority = int(request.form['priority'])

        max_position = db.session.query(func.max(Todo.position)).filter_by(open=True).scalar()
        if max_position is not None:
            position = max_position + 1
        else:
            position = 1
        todo = Todo(value=value,
                    start=start,
                    deadline=deadline,
                    priority=priority,
                    position=position,
                    open=True,
                    user=session['user'])
        db.session.add(todo)
        db.session.commit()
        reset_positions()
    except ValueError:
        print(f'Todo konnte nicht erstellt werden')
    finally:
        return redirect('/')


@app.route('/remove/<int:id>', methods=['POST'])
@require_login
def remove_todo():
    try:
        todo = Todo.query.get_or_404(id)
        db.session.delete(todo)
        db.session.commit()
        reset_positions()
    except ValueError:
        print(f'Todo konnte nicht gelöscht werden')
    finally:
        return redirect('/')


@app.route('/todo/finish/<int:id>', methods=['POST'])
@require_login
def finish_todo():
    print('test')
    try:
        todo = Todo.query.get_or_404(id)
        todo.open = False
        todo.end = datetime.now()
        todo.position = 9999
        db.session.commit()
        reset_positions()
    except ValueError:
        print(f'Todo konnte nicht geschlossen werden')
    finally:
        return redirect('/')


@app.route('/todo/reopen/<int:id>', methods=['POST'])
@require_login
def reopen_todo():
    try:
        todo = Todo.query.get_or_404(id)
        todo.open = True
        todo.end = datetime.now()
        db.session.commit()
        reset_positions()
    except ValueError:
        print(f'Todo konnte nicht wieder geöffnet werden')
    finally:
        return redirect('/')


@app.route('/filter/<filter>', methods=['POST'])
@require_login
def set_filter():
    global activeFilter
    activeFilter = filter
    index()
    return redirect('/')


def reset_positions():
    todos = Todo.query.filter_by(open=True).order_by(Todo.position.asc())
    i = 0

    for todo in todos:
        todo.position = i
        db.session.add(todo)
        i += 1

    db.session.commit()


if __name__ == '__main__':
    app.run()
