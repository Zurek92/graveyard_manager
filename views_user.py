#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plik zawierający funkcje renderowanych stron dostępnych dla użytkownika."""
# importy modułów py
import bcrypt
import random
import numpy as np
import datetime
from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import current_user, login_required, login_user
from sqlalchemy import func, and_, or_

# importy nasze

from data_validate import DataForm, PwForm, OldPwForm, NewGraveForm, owner_required
from db_models import db, User, Grave, Parcel, ParcelType, Family
from data_db_manage import change_user_data, change_user_pw

pages_user = Blueprint('pages_user', __name__)


@pages_user.route('/user', methods=['POST', 'GET'])
@login_required
def user_page():
    """Ogólny panel ustawień użytkownika."""
    graves = Grave.query.filter_by(user_id=current_user.id)
    parcels = Parcel.query.all()
    taken_parcels = []
    for p, g in db.session.query(Parcel, Grave).filter(Parcel.id == Grave.parcel_id):
        taken_parcels.append(p.id)
    max_p = db.session.query(func.max(Parcel.position_x)).scalar()

    favourite_graves_list = db.session.query(Grave.id, Grave.name, Grave.last_name, Grave.day_of_birth,
                                             Grave.day_of_death, Grave.parcel_id)\
        .join(Family)\
        .filter(and_((Grave.id == Family.grave_id),(Family.user_id == current_user.id))).all()


    zombie_mode = False

    if 'zombie_mode' in request.form:
        zombie_mode = True

    if 'follow_zombie' in request.form:
        zombie_mode = True
        x_moved = []
        for x in taken_parcels:
            moves = np.arange(-10, 10)
            x += random.choice(moves)
            if x < max_p * max_p and x != 0:
                x_moved.append(abs(x))
            elif x == 0:
                x_moved.append(1)
            else:
                x_moved.append(max_p * max_p)
        taken_parcels = [x for x in x_moved]

    elif 'end' in request.form:
        zombie_mode = False
        taken_parcels = [x.parcel_id for x in Grave.query.all()]

    return render_template('user_page.html', graves=graves, parcels=parcels, max_p=max_p,
                           favourite_graves_list=favourite_graves_list, taken_parcels=taken_parcels,
                           zombie_mode=zombie_mode)


@pages_user.route('/user/password', methods=['POST', 'GET'])
@login_required
def user_set_pw():
    """Zmiana hasła użytkownika."""
    form_pw = PwForm(request.form)
    form_oldpw = OldPwForm(request.form)
    user = User.query.get(current_user.id)
    if request.method == 'POST' and all([x.validate() for x in [form_pw, form_oldpw]]):
        if bcrypt.checkpw(form_oldpw.old_password.data.encode('UTF_8'), user.password):
            change_user_pw(user, form_pw)
            db.session.commit()
            # ponowne zalogowanie - zmiana tokena automatycznie wylogowuje
            login_user(user)
            flash('Hasło zostało prawidłowo zmienione!', 'succes')
            return redirect(url_for('pages_user.user_page'))
        flash('Podane hasło jest nieprawidłowe!', 'error')
        return redirect(url_for('pages_user.user_set_pw'))
    return render_template('user_settings.html', form_pw=form_pw, form_oldpw=form_oldpw)


@pages_user.route('/user/data', methods=['POST', 'GET'])
@login_required
def user_set_data():
    """Zmiana danych personalnych użytkownika."""
    user = User.query.get(current_user.id)
    form_oldpw = OldPwForm(request.form)
    form_data = DataForm(request.form,
                         name=user.name,
                         last_name=user.last_name,
                         city=user.city,
                         zip_code=user.zip_code,
                         street=user.street,
                         house_number=user.house_number,
                         flat_number=user.flat_number)
    if request.method == 'POST' and all([x.validate() for x in [form_oldpw, form_data]]):
        if bcrypt.checkpw(form_oldpw.old_password.data.encode('UTF_8'),
                          User.query.get(current_user.id).password):
            # zmiana danych użytkownika - funkcja importowana z data_db_manage
            change_user_data(user, form_data)
            db.session.commit()
            flash('Dane zostały prawidłowo zmodyfikowane!', 'succes')
        else:
            flash('Podane hasło jest nieprawidłowe!', 'error')
            return redirect(url_for('pages_user.user_set_data'))
        return redirect(url_for('pages_user.user_page'))
    return render_template('user_settings.html', form_oldpw=form_oldpw, form_data=form_data)


@pages_user.route('/add_grave/<p_id>', methods=['POST', 'GET'])
@login_required
def add_grave(p_id):
    parcel = Parcel.query.get(p_id)
    parcel_type = ParcelType.query.get(parcel.parcel_type_id)
    if Grave.query.filter_by(parcel_id=parcel.id).first() is None:
        form = NewGraveForm(request.form)
        if request.method == 'POST' and form.validate():
            new_grave = Grave(user_id=current_user.id,
                              parcel_id=parcel.id,
                              name=form.name.data,
                              last_name=form.surname.data,
                              day_of_birth=form.birth_date.data,
                              day_of_death=form.death_date.data)
            db.session.add(new_grave)
            db.session.commit()
            return redirect(url_for('pages_user.user_page'))
        return render_template('add_grave.html', form=form, parcel_type=parcel_type, parcel=parcel)
    flash('Ta parcela jest już zajęta', 'error')
    return redirect(url_for('pages_user.user_page'))


@pages_user.route('/grave/<grave_id>', methods=['POST', 'GET'])
@login_required
@owner_required(Grave, 'grave_id')
def grave(grave_id):
    grave = Grave.query.get(grave_id)
    parcel_grave = Parcel.query.get(grave.parcel_id)
    parcel_type = ParcelType.query.get(parcel_grave.parcel_type_id)
    form = NewGraveForm(request.form,
                        name=grave.name,
                        surname=grave.last_name,
                        birth_date=grave.day_of_birth,
                        death_date=grave.day_of_death)
    if request.method == 'POST' and form.validate():
        grave.name = form.name.data
        grave.last_name = form.surname.data
        grave.day_of_birth = form.birth_date.data
        grave.day_of_death = form.death_date.data
        db.session.commit()
        return redirect(url_for('pages_user.grave', grave_id=grave.id))
    return render_template('grave_page.html', grave=grave, parcel_type=parcel_type, form=form)


@pages_user.route('/delete/<grave_id>', methods=['POST'])
@login_required
@owner_required(Grave, 'grave_id')
def delete_grave(grave_id):
    grave = Grave.query.filter_by(id=grave_id).first()
    db.session.delete(grave)
    db.session.commit()
    return redirect(url_for('pages_user.user_page'))


@pages_user.route('/zombie_deathday', methods=['POST', 'GET'])
@login_required
def zombie_deathday():
    graves = Grave.query.all()
    deathday_boys = []
    for grave in graves:
        if grave.day_of_death.strftime('%m-%d') == datetime.datetime.today().strftime('%m-%d'):
            deathday_boys.append(grave)

    return render_template('zombie_deathday.html', deathday_boys=deathday_boys, graves=graves)
