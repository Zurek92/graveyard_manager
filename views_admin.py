#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plik zawierający funkcje renderowanych stron dla administratora."""

from flask import Blueprint, redirect, url_for, render_template, request, flash, abort
from flask_login import current_user, login_required
from functools import wraps
import datetime

from data_db_manage import obituary_add_data
from data_func_manage import convert_date
from db_models import db, User, Messages, Obituaries
from mail_sending import msg_to_all_users
from data_validate import ObituaryForm, is_time_format, is_date_format

pages_admin = Blueprint('pages_admin', __name__)


def admin_required(func):
    """Dekorator, sprawdza czy użytkownik ma status administratora."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.admin:
            return func(*args, **kwargs)
        return abort(404)
    return wrapper


@pages_admin.route('/admin', methods=['POST', 'GET'])
@login_required
@admin_required
def admin():
    """Panel administratora - wymaga statusu w bazie "admin=True"."""
    form_obituary = ObituaryForm(request.form)
    if request.method == 'POST':
        # parametry z formularza nowej wiadomości
        post_title = request.form.get('post_header', False)
        post_content = request.form.get('post_content', False)
        # parametry z formularza wiadomości email
        email_title = request.form.get('email_title', False)
        email_content = request.form.get('email_content', False)
        # parametry z formularza dla nowego nekrologu
        funeral_date = request.form.get('funeral_date', False)
        funeral_time = request.form.get('funeral_time', False)
        if post_title and post_content:
            # dodawanie nowej wiadomości na stronę główną
            new_message = Messages(title=post_title,
                                   content=post_content,
                                   create_date=datetime.datetime.now())
            db.session.add(new_message)
            db.session.commit()
            flash('Dodawanie wiadomości zakończone powodzeniem!', 'succes')
        elif email_title and email_content:
            # wysyłanie wiadomości do wszystkich aktywowanych użytkowników
            users = User.query.filter_by(active_user=True)
            msg_to_all_users(email_title, email_content, users)
            flash('Wysyłanie wiadomości zakończone!', 'succes')
        elif all([form_obituary.validate(),
                  is_time_format(funeral_time),
                  is_date_format(funeral_date)]):
            # funkcja importowana z modułu data_db_manage
            new_obituary = obituary_add_data(form_obituary,
                                             funeral_date,
                                             funeral_time,
                                             calendar_is_html=True,
                                             clock_is_str=True)
            db.session.add(new_obituary)
            db.session.commit()
            flash('Dodano nowy nekrolog!', 'succes')
        else:
            flash('Nieprawidłowe dane', 'error')
        return redirect(url_for('pages_admin.admin'))
    return render_template('admin_page.html', form_obituary=form_obituary)


@pages_admin.route('/message/<message_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def message_edit(message_id):
    """Edycja zamieszczonych wiadomości na stronie głównej."""
    message = Messages.query.get_or_404(message_id)
    if request.method == 'POST':
        post_title = request.form.get('post_header', False)
        post_content = request.form.get('post_content', False)
        if post_title and post_content:
            message.title = post_title
            message.content = post_content
            db.session.commit()
            flash('Wiadomość zmodyfikowano pomyślnie!', 'succes')
        else:
            flash('Nieprawidłowe dane', 'error')
        return redirect(url_for('pages.index'))
    return render_template('message_edit.html', message=message)


@pages_admin.route('/message/<message_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def message_delete(message_id):
    """Usuwanie wiadomości wyświetlanej na stronie głównej."""
    message = Messages.query.get_or_404(message_id)
    if request.method == 'POST':
        db.session.delete(message)
        db.session.commit()
        flash('Wiadomość została usunięta pomyślnie!', 'succes')
        return redirect(url_for('pages.index'))
    return render_template('message_delete.html', message=message)


@pages_admin.route('/obituary/<obituary_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def obituary_edit(obituary_id):
    """Edycja zamieszczonych nekrologów na stronie głównej."""
    obituary = Obituaries.query.get_or_404(obituary_id)
    form_obituary = ObituaryForm(request.form,
                                 name=obituary.name,
                                 surname=obituary.surname,
                                 years_old=obituary.years_old,
                                 death_date=obituary.death_date,
                                 gender=obituary.gender)
    funeral_calendar = obituary.funeral_date.strftime('%Y-%m-%d')
    funeral_clock = obituary.funeral_date.strftime('%H:%M')
    if request.method == 'POST':
        funeral_date = request.form.get('funeral_date', False)
        funeral_time = request.form.get('funeral_time', False)
        if form_obituary.validate() and funeral_date and funeral_time:
            obituary.name = form_obituary.name.data
            obituary.surname = form_obituary.surname.data
            obituary.years_old = form_obituary.years_old.data
            obituary.death_date = form_obituary.death_date.data
            obituary.funeral_date = convert_date(funeral_date, funeral_time)
            obituary.gender = form_obituary.gender.data
            db.session.commit()
            flash('Wiadomość zmodyfikowano pomyślnie!', 'succes')
        else:
            flash('Nieprawidłowe dane!', 'error')
        return redirect(url_for('pages.index'))
    return render_template('obituary_edit.html',
                           form_obituary=form_obituary,
                           funeral_calendar=funeral_calendar,
                           funeral_clock=funeral_clock)


@pages_admin.route('/obituary/<obituary_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def obituary_delete(obituary_id):
    """Usuwanie nekrologu wyświetlanej na stronie."""
    obituary = Obituaries.query.get_or_404(obituary_id)
    if request.method == 'POST':
        db.session.delete(obituary)
        db.session.commit()
        flash('Nekrolog został usunięty pomyślnie!', 'succes')
        return redirect(url_for('pages.index'))
    return render_template('obituary_delete.html', obituary=obituary)
