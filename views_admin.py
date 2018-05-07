#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plik zawierający funkcje renderowanych stron dla administratora."""

from flask import Blueprint, redirect, url_for, render_template, request, flash, abort
from flask_login import current_user, login_required
import datetime

from models import db, User, Messages, Comments, Obituaries
from mail_sending import msg_to_all_users
from generate_data import convert_date

pages_admin = Blueprint('pages_admin', __name__)


def admin_required(func):
    """Dekorator, sprawdza czy użytkownik ma status administratora."""
    def wrapper(*args, **kwargs):
        if current_user.admin:
            return func(*args, **kwargs)
        return abort(404)
    # musi być zmieniona nazwa - wynika to z samego flaska a nie konstrukcji dekoratora
    wrapper.__name__ = func.__name__
    return wrapper


@pages_admin.route('/admin', methods=['POST', 'GET'])
@login_required
@admin_required
def admin():
    """Panel administratora - wymaga statusu w bazie "admin=True"."""
    if request.method == 'POST':
        # parametry z formularza nowej wiadomości
        post_title = request.form.get('post_header', False)
        post_content = request.form.get('post_content', False)
        # parametry z formularza wiadomości email
        email_title = request.form.get('email_title', False)
        email_content = request.form.get('email_content', False)
        # parametry z formularza dla nowego nekrologu
        name = request.form.get('name', False)
        surname = request.form.get('surname', False)
        death_date = request.form.get('death_date', False)
        years_old = request.form.get('years_old', False)
        gender = request.form.get('gender', True)
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
        elif all([name, surname, death_date, years_old, funeral_date, funeral_time]):
            # dodawanie nowego nekrologu
            gender = True if gender == 'man' else False
            # funkcja convert_date z pliku generate_data
            funeral_date = convert_date(funeral_date, funeral_time)
            death_date = convert_date(death_date)
            new_obituary = Obituaries(name=name,
                                      surname=surname,
                                      years_old=int(years_old),
                                      death_date=death_date,
                                      gender=gender,
                                      funeral_date=funeral_date)
            db.session.add(new_obituary)
            db.session.commit()
            flash('Dodano nowy nekrolog!', 'succes')
        else:
            flash('Nieprawidłowe dane', 'error')
        return redirect(url_for('pages_admin.admin'))
    return render_template('admin_page.html')


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
    if request.method == 'POST':
        name = request.form.get('name', False)
        surname = request.form.get('surname', False)
        death_date = request.form.get('death_date', False)
        years_old = request.form.get('years_old', False)
        gender = request.form.get('gender', True)
        funeral_date = request.form.get('funeral_date', False)
        funeral_time = request.form.get('funeral_time', False)
        if all([name, surname, death_date, years_old, funeral_date, funeral_time]):
            # funkcja convert_date z pliku generate_data
            funeral_date = convert_date(funeral_date, funeral_time)
            death_date = convert_date(death_date)
            obituary.name = name
            obituary.surname = surname
            obituary.death_date = death_date
            obituary.years_old = int(years_old)
            obituary.gender = True if gender == 'man' else False
            obituary.funeral_date = funeral_date
            db.session.commit()
            flash('Wiadomość zmodyfikowano pomyślnie!', 'succes')
        else:
            flash('Nieprawidłowe dane', 'error')
        return redirect(url_for('pages.index'))
    return render_template('obituary_edit.html', obituary=obituary)


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
