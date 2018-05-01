#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plik zawierający funkcje renderowanych stron."""

# importy modułów py
import datetime
import bcrypt
from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from sqlalchemy import func

# importy nasze
from validate import EmailForm, LoginForm, DataForm, PwForm, OldPwForm, is_safe_next
from models import db, User, Grave, Parcel, ParcelType, Family, Payments
from config import APP
from data_handling import register_new_user, change_user_data, change_user_pw
from mail_sending import common_msg
from generate_data import generate_password

pages = Blueprint('pages', __name__)
login_manager = LoginManager()

temp_serializer = URLSafeTimedSerializer(APP.APP_KEY)


@login_manager.user_loader
def load_user(session_token):
    """Wczytywanie uzytkownika przy pomocy tokena."""
    return User.query.filter_by(token_id=session_token).first()


@login_manager.unauthorized_handler
def handle_needs_login():
    """Obsługa erroru 401.

    Przekierowanie do strony logowania, oraz przekazanie parametru next
    po zalogowaniu powrót na stronę żądaną.
    """
    flash('Musisz się najpierw zalogować!', 'error')
    return redirect(url_for('pages.login', next=url_for(request.endpoint)))


@pages.route('/')
def index():
    """Renderowanie strony głównej."""
    return render_template('index.html')


@pages.route('/login', methods=['GET', 'POST'])
def login():
    """Strona logowania."""
    if current_user.is_authenticated:
        return redirect(url_for('pages.index'))
    next_page = request.args.get('next')
    form_login = LoginForm(request.form)
    if request.method == 'POST' and form_login.validate():
        user_request = User.query.filter_by(email=form_login.email.data).first()
        if user_request and user_request.active_user:
            if bcrypt.checkpw(form_login.password.data.encode('UTF_8'), user_request.password):
                login_user(user_request)
                flash('Zostałeś poprawnie zalogowany!', 'succes')
                return (redirect(next_page) if next_page and is_safe_next(next_page) else
                        redirect(url_for('pages.index')))
        flash('Niepawidłowy e-mail lub hasło!', 'error')
        return redirect(url_for('pages.login'))
    return render_template('login.html', form_login=form_login)


@pages.route('/pw_recovery', methods=['POST', 'GET'])
def password_recovery():
    """Strona do odzyskiwania hasła.

    Wymaga podania jedynie adresu email, dalsze instrukcje zostają wysłane na podany adres.
    """
    if current_user.is_authenticated:
        return redirect(url_for('pages.index'))
    form_email = EmailForm(request.form)
    if request.method == 'POST' and form_email.validate():
        user = User.query.filter_by(email=form_email.email.data).first()
        # sprawdzenie czy użytkownik jest w bazie oraz czy został aktywowany
        if user and user.active_user:
            password_token = temp_serializer.dumps(user.token_id, salt='pw-recovery')
            link_url = url_for('pages.recovery_password',
                               pw_token=password_token,
                               _external=True)
            common_msg('Odzyskiwanie hasła', user.email, 'pw_recovery', link_url)
            flash('Na podany adres email zostały wysłane dalsze informacje.', 'succes')
            return redirect(url_for('pages.index'))
        flash('Podany adres e-mail nie istnieje!', 'error')
    return render_template('recovery.html', form_email=form_email)


@pages.route('/pw_recovery/<pw_token>')
def recovery_password(pw_token):
    """Strona do generowania nowego hasła.

    Jest wysyłana drogą mailową w postaci url, po wejściu hasło zostaje
    zresetowane a następnie wysłane drugim mailem do użytkownika.
    """
    try:
        token_id = temp_serializer.loads(pw_token, salt='pw-recovery', max_age=3600)
        user = User.query.filter_by(token_id=token_id).first()
        new_pw = generate_password()
        change_user_pw(user, new_pw, form=False)
        db.session.commit()
        common_msg('Nowe hasło', user.email, 'new_password', new_pw)
        flash('Nowe hasło zostało wysłane na twój e-mail.', 'succes')
        return redirect(url_for('pages.login'))
    except (SignatureExpired, BadSignature, AttributeError):
        flash('Podany link jest nieaktywny!', 'error')
        return redirect(url_for('pages.index'))


@pages.route('/logout')
@login_required
def logout():
    """Wylogowywanie użytkownika i przekierowywanie na stronę główną."""
    logout_user()
    flash('Zostałeś poprawnie wylogowany!', 'succes')
    return redirect(url_for('pages.index'))


@pages.route('/register', methods=['GET', 'POST'])
def register():
    """Strona rejestracji."""
    if current_user.is_authenticated:
        return redirect(url_for('pages.index'))
    form_email = EmailForm(request.form)
    form_pw = PwForm(request.form)
    form_data = DataForm(request.form)
    if request.method == 'POST' and all([x.validate() for x in [form_email, form_pw, form_data]]):
        user = User.query.filter_by(email=form_email.email.data).first()
        if not user:
            # rejestracja nowego użytkownika
            new_user = register_new_user(form_email, form_pw, form_data)
            db.session.add(new_user)
            db.session.commit()
        elif not user.active_user:
            # zmiana danych użytkownika
            change_user_pw(user, form_pw)
            change_user_data(user, form_data)
            db.session.commit()
        else:
            flash('Podany adres e-mail jest w użyciu!', 'error')
            return redirect(url_for('pages.register'))
        # wysyłanie e-maila z linkiem do aktywacji
        register_token = temp_serializer.dumps(form_email.email.data, salt='confirm-email')
        link_url = url_for('pages.confirm_email', register_token=register_token, _external=True)
        common_msg('Aktywacja konta', form_email.email.data, 'register_message', link_url)
        flash('Na podany adres email został wysłany kod weryfikacyjny!', 'succes')
        return redirect(url_for('pages.index'))
    return render_template('user_settings.html',
                           form_email=form_email,
                           form_pw=form_pw,
                           form_data=form_data)


@pages.route('/confirm_email/<register_token>')
def confirm_email(register_token):
    """Strona do potwierdzania adresu e-mail.

    Jest generowana i wysyłana drogą mailową w postaci url, po wejściu status "active_user" zostaje
    zmieniony z domyślnego False na True co umożliwia zalogowanie.
    """
    try:
        email = temp_serializer.loads(register_token, salt='confirm-email', max_age=3600)
        user = User.query.filter_by(email=email).first()
        if user.active_user:
            flash('Konto już jest aktywne!', 'error')
            return redirect(url_for('pages.index'))
        user.active_user = True
        db.session.commit()
        flash('Konto zostało aktywowane pomyślnie!', 'succes')
        return redirect(url_for('pages.login'))
    except (SignatureExpired, BadSignature):
        flash('Podany link jest nieaktywny!', 'error')
        return redirect(url_for('pages.index'))


@pages.route('/user', methods=['POST', 'GET'])
@login_required
def user_page():
    """Ogólny panel ustawień użytkownika."""
    graves = Grave.query.filter_by(user_id=current_user.id)
    parcels = Parcel.query.all()
    max_p = db.session.query(func.max(Parcel.position_x)).scalar()
    return render_template('user_page.html', graves=graves, parcels=parcels, max_p=max_p)


@pages.route('/user/password', methods=['POST', 'GET'])
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
            return redirect(url_for('pages.user_page'))
        flash('Podane hasło jest nieprawidłowe!', 'error')
        return redirect(url_for('pages.user_set_pw'))
    return render_template('user_settings.html', form_pw=form_pw, form_oldpw=form_oldpw)


@pages.route('/user/data', methods=['POST', 'GET'])
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
            # zmiana danych użytkownika
            change_user_data(user, form_data)
            db.session.commit()
            flash('Dane zostały prawidłowo zmodyfikowane!', 'succes')
        else:
            flash('Podane hasło jest nieprawidłowe!', 'error')
            return redirect(url_for('pages.user_set_data'))
        return redirect(url_for('pages.user_page'))
    return render_template('user_settings.html', form_oldpw=form_oldpw, form_data=form_data)


@pages.route('/admin', methods=['POST', 'GET'])
@login_required
def admin():
    """Panel administratora - wymaga statusu w bazie "admin=True"."""
    if current_user.admin:
        txt = 'cześć adminie'
        return txt
    return redirect(url_for('pages.index'))


@pages.route('/add_grave/<p_id>', methods=['POST', 'GET'])
def add_grave(p_id):
    parcel = Parcel.query.filter_by(id=p_id).scalar()
    p_id = parcel.id
    if Grave.query.filter_by(parcel_id=p_id).first() is None:
        if request.method == 'POST':
            name = request.form['name']
            last_name = request.form['last_name']
            day_of_birth = datetime.datetime.strptime(request.form['day_of_birth'], '%Y-%m-%d')
            day_of_death = datetime.datetime.strptime(request.form['day_of_death'], '%Y-%m-%d')
            new_grave = Grave(user_id=current_user.id,
                              parcel_id=p_id,
                              name=name,
                              last_name=last_name,
                              day_of_birth=day_of_birth,
                              day_of_death=day_of_death)
            db.session.add(new_grave)
            db.session.commit()
            return redirect(url_for('pages.user_page'))
        return render_template('add_grave.html', p_id=p_id, parcel=parcel)
    else:
        flash('Ta parcela jest już zajęta', 'error')
        return redirect(url_for('pages.user_page'))


@pages.route('/grave/<grave_id>', methods=['POST', 'GET'])
def grave(grave_id):
    grave = Grave.query.filter_by(id=grave_id).first()
    parcel_grave = Parcel.query.filter_by(id=grave.parcel_id).first()
    parcel_type = ParcelType.query.filter_by(id=parcel_grave.parcel_type_id).first()

    if request.method == 'POST':
        grave.name = request.form['edited_name']
        grave.last_name = request.form['edited_last_name']
        grave.day_of_birth = datetime.datetime.strptime(request.form['edited_birth'], '%Y-%m-%d')
        grave.day_of_death = datetime.datetime.strptime(request.form['edited_death'], '%Y-%m-%d')
        db.session.commit()

    return render_template('grave_page.html', grave_id=grave_id, grave=grave, parcel_type=parcel_type)


@pages.route('/delete/<grave_id>', methods=['POST'])
def delete_grave(grave_id):
    grave = Grave.query.filter_by(id=grave_id).first()
    db.session.delete(grave)
    db.session.commit()
    return redirect(url_for('pages.user_page'))


@pages.app_errorhandler(404)
def page_not_found(e):
    """Obsługa erroru 404."""
    return render_template('page_404.html')
