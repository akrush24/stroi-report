#!/usr/bin/env python
# coding: utf-8

from flask import Flask, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from sqlalchemy.orm import relationship
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
db = SQLAlchemy(app)

# Создание модели таблицы


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    desc = db.Column(db.String(100), nullable=False)

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


class Entries(db.Model):
    __tablename__ = 'entries'
    id = db.Column('id', db.Text(length=36), default=lambda: str(
        uuid.uuid4()), primary_key=True)
    # id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'))
    value = db.Column(db.String(50), nullable=False)
    created_on = db.Column(db.DateTime(), default=datetime.utcnow)
    updated_on = db.Column(
        db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)


with app.app_context():
    db.create_all()


@app.context_processor
def inject_global_vars():
    return {
        'global': {
            'title': "Система Учета ресурсов",
            'currentdate': datetime.now().date()
        }
    }

# app name


@app.errorhandler(404)
# перехватываем 404 ошибку
def not_found(e):
    return render_template('404.html', groups=Groups.query.all())


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'images'),
                               'favicon.png', mimetype='image/vnd.microsoft.icon')


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
        if 'del_group_id' in post_values:
            if Properties.query.filter_by(group_id=request.form['del_group_id']).count() == 0:
                Groups.query.filter_by(id=request.form['del_group_id']).delete()
                db.session.commit()
            else:
                return('У группы есть свойства, сначала удалите их!')
        else:
            newline = Groups(
                name=request.form['name'], desc=request.form['desc'])
            db.session.add(newline)
            db.session.commit()

    table_columns = Groups.__table__.columns.keys()
    rows = Groups.query.all()

    return render_template('admin.html',
                           table_columns=table_columns,
                           rows=rows,
                           groups=rows)


'''
    Редактирование групп и свойств
'''


@app.route('/admin/grp/<int:group_id>', methods=['GET', 'POST'])
def dynamic_route(group_id):
    if request.method == 'POST':
        post_values = list(request.form.keys())
        # return(post_values)
        if 'del_property' in post_values:
            if Entries.query.filter_by(property_id=request.form['del_property']).count() == 0:
                Properties.query.filter_by(
                    id=request.form['del_property']).delete()
                db.session.commit()
            else:
                return('У свойства есть записи, удалити сначала их')
        if 'name' in post_values and 'desc' in post_values and request.form['name'] != '':
            newline = Properties(name=request.form['name'],
                                 desc=request.form['desc'],
                                 group_id=group_id,
                                 type=request.form['type'])
            db.session.add(newline)
            db.session.commit()
    rows = Properties.query.filter_by(group_id=group_id)
    table_columns = Properties.__table__.columns.keys()

    return render_template(
        'properties.html',
        data=rows,
        table_columns=table_columns,
        title=db.session.query(Groups.name).filter(
            Groups.id == group_id)[0][0],
        group_id=group_id,
        groups=Groups.query.all(),
    )


'''
    заносим новые записи по выбранной группе
'''


@app.route('/grp/<int:group_id>', methods=['GET', 'POST'])
# @app.route('/grp/<int:group_id>', defaults={'filter_date': None}, methods=['GET', 'POST'])
# @app.route('/grp/<int:group_id>/<string:filter_date>', methods=['GET', 'POST'])
def group(group_id):
    table_columns = Properties.query.filter_by(group_id=group_id)

    if request.method == 'POST':
        post_values = list(request.form.keys())
        if 'del_entrie' in post_values:
            Entries.query.filter_by(id=request.form['del_entrie']).delete()
            db.session.commit()
        else:
            for post_value in post_values:
                if request.form[post_value] != "":
                    currentvalue = abs(float(request.form[post_value]))
                    # проверяем если строчка с такой датой уже есть то игнорирует добавление новой и делаем update
                    rows = Entries.query.\
                        filter(Entries.group_id == group_id).\
                        filter(Entries.property_id == post_value).\
                        filter(Entries.created_on.like(
                            str(datetime.now().date()) + '%'))
                    if rows.count() == 0:
                        newline = Entries(group_id=group_id,
                                        property_id=post_value,
                                        value=currentvalue,
                                        created_on=datetime.now()
                                        )
                        db.session.add(newline)
                    else:
                        rows.update(dict(value=currentvalue))
                    db.session.commit()

    rows = db.session.\
        query(Entries.id, Properties.name, Entries.value, Entries.created_on, Properties.type).\
        filter(Entries.property_id == Properties.id).\
        filter(Entries.group_id == group_id)
    entries_by_date = db.session.query(
        db.func.date(
            Entries.created_on).label('DATE'),
        db.func.count('*')).filter(Entries.group_id == group_id).group_by(db.func.date(Entries.created_on))
    tabs = [row[0] for row in entries_by_date.all()]
    properties_by_group = Properties.query.filter(
        Properties.group_id == group_id).all()
    daterow = {}
    # цикл по всем датам на которых есть записи
    sum = {}
    for date in tabs:
        all_day_properties = {}
        for property in properties_by_group:
            try:
                sum[property.id]
            except:
                sum[property.id] = 0
            # цикл по всем свойствам на которым есть записи на конкретную дату
            entries_by_date_by_property = db.session.query(Entries.value).filter(Entries.created_on.like(
                date+'%')).filter(Entries.group_id == group_id).filter(Entries.property_id == property.id)
            for v in entries_by_date_by_property:
                all_day_properties[property.id] = v.value
                if v.value == '':
                    correntvalue = 0
                else:
                    correntvalue = v.value
                sum[property.id] = float(sum[property.id]) + float(correntvalue)
        daterow[str(date)] = all_day_properties

    return render_template(
        'group.html',
        data=rows,
        table_columns=table_columns,
        groups=Groups.query.all(),
        properties=properties_by_group,
        group_id=group_id,
        entries=rows,
        valdict=daterow,
        sum=sum)


# записи по выбранной дате
@app.route('/grp/<int:group_id>/<string:filter_date>', methods=['GET', 'POST'])
def dateview(group_id, filter_date):
    if request.method == 'POST':
        post_values = list(request.form.keys())
        if 'del_entrie' in post_values:
            Entries.query.filter_by(id=request.form['del_entrie']).delete()
            db.session.commit()

    # rows = Entries.query.filter_by(group_id = group_id)
    rows = db.session.query(Entries.id, Properties.name, Entries.value, Entries.created_on, Properties.type).filter(
        Entries.property_id == Properties.id).filter(Entries.group_id == group_id)
    if filter_date:
        rows = rows.filter(Entries.created_on.like(filter_date+'%'))
    # entr_columns = Entries.__table__.columns.keys()
    # select DATE(created_on) as DATE, count(*) from entries where group_id = 2 group by date
    entries_by_date = db.session.query(
        db.func.date(
            Entries.created_on).label('DATE'),
        db.func.count('*')).filter(Entries.group_id == group_id).group_by(db.func.date(Entries.created_on))
    tabs = [row[0] for row in entries_by_date.all()]

    return render_template(
        'dateview.html',
        data=rows,
        groups=Groups.query.all(),
        group_id=group_id,
        entries=rows,
        tabs=tabs,
        filter_date=filter_date)


if __name__ == '__main__':
    app.run(debug=True)
