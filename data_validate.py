#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Plik do walidacji danych."""
# importy modułów py
import datetime
import re
from flask import abort
from flask_login import current_user
from functools import wraps
from urllib.parse import urlparse
from wtforms import Form, StringField, PasswordField, IntegerField, RadioField
from wtforms.fields.html5 import DateField
from wtforms.validators import ValidationError, input_required, email, length, equal_to, Optional


def owner_required(db_param, func_param):
    """Funkcja z parametrami dla dekoratora."""
    def owner_required_call(func):
        """Prawdziwy dekorator, sprawdza czy dany element należy do użytkownika."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            param = db_param.query.get_or_404(kwargs[func_param])
            if current_user.id == param.user_id:
                return func(*args, **kwargs)
            return abort(404)
        return wrapper
    return owner_required_call


def is_safe_next(next_page):
    """Funkcja do weryfikacji parametru next."""
    return not urlparse(next_page).netloc


def is_time_format(time_to_check):
    """Funkcja sprawdza czy czas ma prawidłowy format: HH:MM:SS w zakresie 00:00:00 do 23:59:59."""
    return True if re.search(r'(^[0-1][0-9]|2[0-3])(:[0-5][0-9]){1,2}$', time_to_check) else False


def is_date_format(date_to_check):
    """Funkcja sprawdza czy data w formacie str jest prawidłowa."""
    try:
        datetime.datetime.strptime(date_to_check, '%Y-%m-%d')
        return True
    except Exception:
        return False


# walidacja danych użytkownika
class PwForm(Form):
    """Klasa wtforms do ustalania hasła użytkownika."""

    password = PasswordField('Hasło:',
                             [input_required(message='Pole wymagane!'),
                              length(max=72, message='Hasło nie może być dłuższe niż 72 znaki!'),
                              equal_to('repeat_password', message='Hasła nie są identyczne!')],
                             render_kw={'placeholder': 'hasło'})
    repeat_password = PasswordField('Powtórz hasło:', render_kw={'placeholder': 'powtórz hasło'})


class OldPwForm(Form):
    """Klasa wtforms do weryfikacji aktualnego hasła."""

    old_password = PasswordField('Aktualne hasło:', [input_required(message='Pole wymagane!')],
                                 render_kw={'placeholder': 'aktualne hasło'})


class DataForm(Form):
    """Klasa wtforms do ustawiania danych personalnych użytkownika."""

    def digit_or_none(self, field):
        """Pole musi pozostac puste lub być liczbą."""
        if field.data != '':
            if not field.data.isdigit():
                raise ValidationError('Niepoprawny numer!')

    def zip_code_validator(self, field):
        """Walidacja kodu pocztowego zgodnie ze standarem polskim "dd-ddd"."""
        if field.data != '':
            if not re.match(r'^\d\d-\d\d\d$', field.data):
                raise ValidationError('Niepoprawny kod pocztowy!')

    name = StringField('Imię:', [length(max=80)], render_kw={'placeholder': 'imię'})
    last_name = StringField('Nazwisko:', [length(max=120)], render_kw={'placeholder': 'nazwisko'})
    city = StringField('Miasto:', [length(max=80)], render_kw={'placeholder': 'miasto'})
    zip_code = StringField('Kod pocztowy:', [zip_code_validator],
                           render_kw={'placeholder': 'kod pocztowy'})
    street = StringField('Ulica:', [length(max=150)], render_kw={'placeholder': 'ulica'})
    house_number = StringField('Numer domu:', [digit_or_none],
                               render_kw={'placeholder': 'nr domu', 'type': 'number', 'min': 1})
    flat_number = StringField('Numer mieszkania:', [digit_or_none],
                              render_kw={'placeholder': 'nr mieszkania', 'type': 'number', 'min': 1}
                             )


class EmailForm(Form):
    """Klasa wtforms do rejestracji użytkownika - ustawianie adresu e-mail."""

    email = StringField('Adres e-mail:',
                        [input_required(message='Pole wymagane!'),
                         email(message='Niepoprawny adres e-mail!'),
                         length(max=63, message='Adres e-mail przekracza 63 znaki!')],
                        render_kw={'placeholder': 'adres e-mail'})


class LoginForm(Form):
    """Klasa wtforms do logowania."""

    email_login = StringField('Adres e-mail', [input_required(message='Pole wymagane!')],
                              render_kw={'placeholder': 'adres e-mail'})
    password = PasswordField('Hasło', [input_required(message='Pole wymagane!')],
                             render_kw={'placeholder': 'hasło'})


# walidacja danych podawanych przez administratora
class ObituaryForm(Form):
    """Klasa wtforms do walidacji tworzonych nekrologów."""

    name = StringField('Imię', [input_required(message='Pole wymagane!')],
                       render_kw={'required': True})
    surname = StringField('Nazwisko', [input_required(message='Pole wymagane!')],
                          render_kw={'required': True})
    years_old = IntegerField('Wiek', [input_required(message='Pole wymagane!')],
                             render_kw={'required': True, 'type': 'number', 'min': 0, 'max': 150})
    death_date = DateField('Data śmierci', format='%Y-%m-%d', render_kw={'required': True})
    gender = RadioField('Płeć', choices=[('man', 'Mężczyzna'), ('woman', 'Kobieta')], default='man')


class NewGraveForm(Form):
    """Klasa wtforms do walidacji danych dotyczących grobu."""
    def name_validator(self, field):
        if not re.match(r'^[A-Za-z -]+$', field.data):
            raise ValidationError('Pole może zawierać tylko litery, spacje i myślniki!')

    def date_past(self, field):
        today = datetime.datetime.today()
        if field.data > datetime.datetime.date(today):
            raise ValidationError('Data musi być starsza od dzisiejszej daty!')

    def death_after(self, field):
        if field.data < self.birth_date.data:
            raise ValidationError('Data urodzenia nie może przekroczyć daty śmierci!')

    name = StringField('Imię', [input_required(message='Pole wymagane!'),
                                name_validator],
                       render_kw={'required': True})
    surname = StringField('Nazwisko', [input_required(message='Pole wymagane!'),
                                       name_validator],
                          render_kw={'required': True})
    birth_date = DateField('Data urodzenia', [date_past],
                           format='%Y-%m-%d',
                           render_kw={'required': True})
    death_date = DateField('Data śmierci',
                           [Optional(), date_past, death_after],
                           format='%Y-%m-%d')
