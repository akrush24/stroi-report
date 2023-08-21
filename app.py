from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
db = SQLAlchemy(app)

# Создание модели таблицы
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    desc = db.Column(db.String(100), nullable=False)
    # created_on = db.Column(db.DateTime(), default=datetime.utcnow)
    # updated_on = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

class Groups(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    desc = db.Column(db.String(100), nullable=False)

class Properties(db.Model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    name = db.Column(db.String(50), nullable=False)
    desc = db.Column(db.String(100), nullable=False)
    # created_on = db.Column(db.DateTime(), default=datetime.utcnow)
    # updated_on = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

class Entries(db.Model):
    __tablename__ = 'entries'
    id = db.Column('id', db.Text(length=36), default=lambda: str(uuid.uuid4()), primary_key=True)
    # id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    name = db.Column(db.String(50), nullable=False)
    desc = db.Column(db.String(100), nullable=False)
    created_on = db.Column(db.DateTime(), default=datetime.utcnow)
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)


with app.app_context():
    db.create_all()

# Перенести все операции с базой данных внутрь функции или маршрута Flask
@app.route('/')
def index():
    return render_template('base.html', groups=Groups.query.all())

'''
    Админка
'''
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        newline = Groups(name=request.form['name'], desc=request.form['desc'])
        db.session.add(newline)
        db.session.commit()

    table_columns = Groups.__table__.columns.keys()
    rows = Groups.query.all()

    return render_template('admin.html', 
                            table_columns=table_columns,
                            rows=rows,
                            groups=rows)

'''
    Заносим данные
'''
@app.route('/enter', methods=['GET', 'POST'])
def enter_data():
    table_columns = Properties.__table__.columns.keys()
    if request.method == 'POST':
        newline = Properties(name=request.form['name'],
                            desc=request.form['desc'],
                            group_id=request.form['group_id'])
        db.session.add(newline)
        db.session.commit()
    return render_template('enter_data.html', table_columns=table_columns, groups=Groups.query.all())

@app.route('/properties')
def properties():
    rows = User.query.all()
    table_columns = User.__table__.columns.keys()
    return render_template(
            'properties.html',
            data=rows,
            table_columns=table_columns,
            groups=Groups.query.all())

@app.route('/grp/<int:n>', methods=['GET', 'POST'])
def dynamic_route(n):
    if request.method == 'POST':
        port_values = list(request.form.keys())
        if 'del' in port_values:
            Properties.query.filter_by(id = request.form['del']).delete()
            db.session.commit()
        if 'name' in port_values and 'desc' in port_values:
            newline = Properties(name = request.form['name'],
                                desc = request.form['desc'],
                                group_id = n)
            db.session.add(newline)
            db.session.commit()
    rows = Properties.query.filter_by(group_id = n)
    table_columns = Properties.__table__.columns.keys()
    return render_template(
            'properties.html',
            data=rows,
            table_columns=table_columns,
            groups=Groups.query.all(),
            group_id = n
            )


if __name__ == '__main__':
    app.run(debug=True)
