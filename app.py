from datetime import datetime
from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, IntegerField
from wtforms.validators import DataRequired, Optional

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SECRET_KEY'] = 'mysecretkey'
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


with app.app_context():
    db.create_all()

activeFilter = 'none'


@app.route('/')
def index():
    global activeFilter
    todos_query = Todo.query.filter_by(open=True)
    if activeFilter == 'prio_asc':
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
        todo = Todo(value=value, start=start, deadline=deadline, priority=priority, position=0, open=True)
        db.session.add(todo)
        db.session.commit()
    except ValueError:
        print(f'Todo konnte nicht erstellt werden')
    finally:
        return redirect('/')


@app.route('/remove/<int:id>', methods=['POST'])
def remove_todo(id):
    try:
        todo = Todo.query.get_or_404(id)
        db.session.delete(todo)
        db.session.commit()
    except ValueError:
        print(f'Todo konnte nicht gelöscht werden')
    finally:
        return redirect('/')


@app.route('/todo/finish/<int:id>', methods=['POST'])
def finish_todo(id):
    try:
        todo = Todo.query.get_or_404(id)
        todo.open = False
        todo.end = datetime.now()
        db.session.commit()
    except ValueError:
        print(f'Todo konnte nicht geschlossen werden')
    finally:
        return redirect('/')


@app.route('/todo/reopen/<int:id>', methods=['POST'])
def reopen_todo(id):
    try:
        todo = Todo.query.get_or_404(id)
        todo.open = True
        todo.end = datetime.now()
        db.session.commit()
    except ValueError:
        print(f'Todo konnte nicht wieder geöffnet werden')
    finally:
        return redirect('/')


@app.route('/filter/<filter>', methods=['POST'])
def set_filter(filter):
    global activeFilter
    activeFilter = filter
    index()
    return redirect('/')


if __name__ == '__main__':
    app.run()
