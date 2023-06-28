from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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
    description = StringField(validators=[Optional()])
    start = DateField('Start', validators=[DataRequired()])
    deadline = DateField('Deadline', validators=[Optional()])
    priority = IntegerField('Priority', validators=[DataRequired()])


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(500))
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
    if username_unique is None:
        return True
    else:
        return False


def require_login(func):
    @wraps(func)
    def check_session(*args, **kwargs):
        with app.app_context():
            if 'exp' not in session or session['exp'] is None or session['exp'] < datetime.now(timezone.utc):
                return redirect(url_for('login'))
            elif User.query.filter_by(id=session['user']).first() is None:
                return redirect(url_for('login'))
        return func(*args, **kwargs)
    return check_session


@app.route('/register', methods=['POST'])
def register():
    session['user'] = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_hashed_password(request.form['password'])
        if username == "" or password == "":
            print("Empty")
            return redirect('/login')
        if check_for_unique(username, email):
            if email is None:
                email = ""
            db.session.add(User(username=username, email=email, password=password))
            db.session.commit()
            login_session(User.query.filter_by(username=username).first())
            return redirect(url_for('index'))
        else:
            print("Error")
            return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    session['user'] = None
    if request.method == 'GET':
        user_agent = request.headers.get('User-Agent')
        if 'Mobile' in user_agent:
            return render_template('login-mobile.html', form=LoginForm)
        else:
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
    finished_todos_query = Todo.query.filter_by(open=False, user=session['user'])
    finished_todos = finished_todos_query.all()
    filters = [
        {'value': 'none', 'label': 'Standard'},
        {'value': 'prio_asc', 'label': 'Priorität (aufsteigend)'},
        {'value': 'prio_desc', 'label': 'Priorität (absteigend)'},
        {'value': 'deadline_asc', 'label': 'Deadline (aufsteigend)'},
        {'value': 'deadline_desc', 'label': 'Deadline (absteigend)'}
    ]
    user_agent = request.headers.get('User-Agent')
    print(user_agent)
    if 'Mobile' in user_agent:
        return render_template('todo-list-mobile.html', todos=todos, closed_todos=finished_todos, filters=filters,
                               activeFilter=activeFilter)
    else:
        return render_template('todo-list.html', todos=todos, closed_todos=finished_todos, filters=filters,
                               activeFilter=activeFilter)


@app.route('/add', methods=['POST'])
@require_login
def add_todo():
    try:
        value = request.form['value']
        if value == '':
            return
        description = request.form.get('description')
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
                    description=description,
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
def remove_todo(id):
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
def finish_todo(id):
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
def reopen_todo(id):
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


@app.route('/update/<int:id>', methods=['POST', 'GET'])
@require_login
def update_todo(id):
    if request.method == 'GET':
        todo = Todo.query.get_or_404(id)
        return render_template('update.html', form=TodoForm, todo=todo)
    elif request.method == 'POST':
        todo = Todo.query.filter_by(id=id).first()
        todo.value = request.form.get('value')
        todo.description = request.form.get('description')
        deadline_str = request.form.get('deadline')
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                return 'Ungültiges Datum', 400
        else:
            deadline = None
        todo.deadline = deadline
        todo.priority = request.form.get('priority')
        db.session.commit()
        return redirect(url_for('index'))


@app.route('/filter/<filter>', methods=['POST'])
@require_login
def set_filter(filter):
    global activeFilter
    activeFilter = filter
    index()
    return redirect('/')


@app.route('/logout')
@require_login
def logout():
    session['user'] = None
    session['exp'] = None
    return redirect(url_for('login'))


@app.route('/api/todo/<int:id>', methods=['GET'])
@require_login
def get_todo(id):
    print(id)
    todo = Todo.query.get_or_404(id)
    todo_data = {
        'id': todo.id,
        'value': todo.value,
        'description': todo.description,
        'start': todo.start.isoformat(),
        'end': todo.end.isoformat() if todo.end else None,
        'deadline': todo.deadline.isoformat() if todo.deadline else None,
        'priority': todo.priority,
        'open': todo.open
    }
    return jsonify(todo_data)


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
