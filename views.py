#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plik zawierający funkcje renderowanych stron dostępnych bez zalogowania."""

# importy modułów py
import datetime
from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import current_user, login_required
from sqlalchemy import func, and_, or_


# importy nasze
from db_models import db, Grave, Parcel, Family, Messages, Obituaries

pages = Blueprint('pages', __name__)


@pages.route('/')
def index():
    """Renderowanie strony głównej."""
    messages_to_display = Messages.query.order_by(Messages.create_date.desc())
    return render_template('index.html', infos=messages_to_display)


@pages.route('/obituaries')
def obituaries():
    """Wyświatlanie nekrologów uporządkowane datami i tylko aktualne."""
    today_date = datetime.datetime.now() - datetime.timedelta(hours=4)
    obits = Obituaries.query.order_by(Obituaries.funeral_date.asc()).filter(
        Obituaries.funeral_date >= today_date)
    return render_template('obituaries.html', obits=obits)


@pages.route('/graves', methods=['GET'])
def graves():
    search_name = request.args.get('search_name')
    search_last_name = request.args.get('search_last_name')
    if current_user.is_authenticated:
        if not search_name and not search_last_name:
            #tworzy listę grobów
            graves_list = db.session.query(Grave.id, Grave.name, Grave.last_name, Grave.day_of_birth, Grave.day_of_death, Grave.parcel_id, Family.id.label("my_family"))\
                .outerjoin(Family, and_((Grave.id == Family.grave_id),(Family.user_id == current_user.id)))
        else:
            #wyszukiwarka
            search_like_name = '%'+search_name+'%'
            search_like_last_name = '%' + search_last_name + '%'
            graves_list = db.session.query(Grave.name, Grave.last_name, Grave.day_of_birth, Grave.day_of_death,Grave.parcel_id, Family.id.label("my_family"))\
                .outerjoin(Family, and_((Grave.id == Family.grave_id),(Family.user_id == current_user.id)))\
                .filter(and_(Grave.name.like(search_like_name), Grave.last_name.like(search_like_last_name)))
    else:
        if not search_name and not search_last_name:
            #tworzy listę grobów
            graves_list = db.session.query(Grave.id, Grave.name, Grave.last_name, Grave.day_of_birth, Grave.day_of_death, Grave.parcel_id)
        else:
            #wyszukiwarka
            search_like_name = '%'+search_name+'%'
            search_like_last_name = '%' + search_last_name + '%'
            graves_list = db.session.query(Grave.name, Grave.last_name, Grave.day_of_birth, Grave.day_of_death,Grave.parcel_id)\
                .filter(and_(Grave.name.like(search_like_name), Grave.last_name.like(search_like_last_name)))

    return render_template('graves.html', graves_list=graves_list, current_user=current_user)

@pages.route('/graves/<grave_id>/add-favourite', methods=['GET'])
@login_required
def add_favourite(grave_id):

    is_family = db.session.query(Family.user_id, Family.grave_id).\
        filter(Family.user_id == current_user.id, Family.grave_id == grave_id).first()
    if not is_family:
        new_favourite = Family(user_id=current_user.id,
                               grave_id=grave_id)
        db.session.add(new_favourite)
        db.session.commit()
        flash('Dodano do znanych grobów', 'succes')
    else:
        flash('Ten grób jest już w znanych grobach', 'error')

    return redirect('/graves')


@pages.route('/user/delete-favourite/<grave_id>', methods=['GET'])
@login_required
def delete_favourite(grave_id):
    back_url = request.args.get('back_url')
    my_favourite = Family.query.filter_by(user_id=current_user.id, grave_id=grave_id).first()
    if my_favourite:
        db.session.delete(my_favourite)
        db.session.commit()
    if back_url:
        return redirect(back_url)
    else:
        return redirect('/')


@pages.app_errorhandler(404)
def page_not_found(e):
    """Obsługa erroru 404."""
    return render_template('page_404.html')


@pages.app_errorhandler(405)
def page_wrong_method(e):
    """Obsługa erroru 405."""
    return redirect(url_for('pages.index'))
