#!/usr/bin/env python
# coding: utf-8

from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from sqlalchemy.orm import relationship
import jsonpickle

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
    type = db.Column(db.String(50))
    # created_on = db.Column(db.DateTime(), default=datetime.utcnow)
    # updated_on = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

class Entries(db.Model):
    __tablename__ = 'entries'
    id = db.Column('id', db.Text(length=36), default=lambda: str(uuid.uuid4()), primary_key=True)
    # id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'))
    value = db.Column(db.String(50), nullable=False)
    created_on = db.Column(db.DateTime(), default=datetime.utcnow)
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

with app.app_context():
    db.create_all()

# app name
@app.errorhandler(404)

# перехватываем 404 ошибку
def not_found(e):
    return render_template("404.html")

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
        post_values = list(request.form.keys())
        if 'del_droup_id' in post_values:
            Groups.query.filter_by(id = request.form['del_droup_id']).delete()
            db.session.commit()
        else:
            newline = Groups(name=request.form['name'], desc=request.form['desc'])
            db.session.add(newline)
            db.session.commit()

    table_columns = Groups.__table__.columns.keys()
    rows = Groups.query.all()

    return render_template('admin.html', 
                            table_columns=table_columns,
                            rows=rows,
                            groups=rows)


@app.route('/admin/grp/<int:group_id>', methods=['GET', 'POST'])
def dynamic_route(group_id):
    if request.method == 'POST':
        post_values = list(request.form.keys())
        # return(post_values)
        if 'del_property' in post_values:
            Properties.query.filter_by(id = request.form['del_property']).delete()
            db.session.commit()
        if 'name' in post_values and 'desc' in post_values:
            newline = Properties(name = request.form['name'],
                                desc = request.form['desc'],
                                group_id = group_id,
                                type = request.form['type'])
            db.session.add(newline)
            db.session.commit()
    rows = Properties.query.filter_by(group_id = group_id)
    table_columns = Properties.__table__.columns.keys()

    return render_template(
                'properties.html',
                data=rows,
                table_columns=table_columns,
                title = db.session.query(Groups.name).filter(Groups.id == group_id)[0][0],
                group_id = group_id,
                groups = Groups.query.all(),
            )


'''
    заносим новые записи по выбранной группе
'''
@app.route('/grp/<int:group_id>', methods=['GET', 'POST'])
def group(group_id):
    table_columns = Properties.query.filter_by(group_id = group_id)

    if request.method == 'POST':
        post_values = list(request.form.keys())
        if 'del_entrie' in post_values:
            Entries.query.filter_by(id = request.form['del_entrie']).delete()
            db.session.commit()
        else:
            for post_value in post_values:
                # return(request.form[port_value] + '<br>')
                newline = Entries(group_id = group_id,
                                property_id = post_value,
                                value = request.form[post_value])
                db.session.add(newline)
                db.session.commit()

    # rows = Entries.query.filter_by(group_id = group_id)
    rows = db.session.query(Entries.id, Properties.name, Entries.value, Entries.created_on, Properties.type).filter(Entries.property_id == Properties.id).filter(Entries.group_id == group_id)
    entr_columns = Entries.__table__.columns.keys()
    return render_template(
            'group.html',
            data=rows,
            table_columns=table_columns,
            groups=Groups.query.all(),
            group_id = group_id,
            entr_columns = entr_columns,
            entries = rows)

if __name__ == '__main__':
    app.run(debug=True)
