#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Plik z tabelami do SQLAlchemy."""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from config import DB

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Tabela użytkownika."""

    id = db.Column(db.Integer, primary_key=True)
    active_user = db.Column(db.Boolean, default=DB.DEFAULT_ACTIVE_USER)
    token_id = db.Column(db.Text, unique=True)
    email = db.Column(db.String(63), unique=True, nullable=False)
    password = db.Column(db.String(72), nullable=False)
    name = db.Column(db.String(80))
    last_name = db.Column(db.String(120))
    city = db.Column(db.String(80))
    zip_code = db.Column(db.Integer)
    street = db.Column(db.String(150))
    house_number = db.Column(db.Integer)
    flat_number = db.Column(db.Integer)
    admin = db.Column(db.Boolean, default=False)

    def get_id(self):
        """Zmiana domyślnego pobierania id podczas logowania na token."""
        return self.token_id


class Grave(db.Model):
    """Tabela właściwości grobów."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parcel_id = db.Column(db.Integer, db.ForeignKey('parcel.id'), nullable=False, unique=True)
    name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    day_of_birth = db.Column(db.Date(), nullable=False)
    day_of_death = db.Column(db.Date(), nullable=True)


class Parcel(db.Model):
    """Tabela odnoszona do Grave - współrzędne grobów."""

    id = db.Column(db.Integer, primary_key=True)
    parcel_type_id = db.Column(db.Integer, db.ForeignKey('parcel_type.id'), nullable=False)
    position_x = db.Column(db.Integer, nullable=False)
    position_y = db.Column(db.Integer, nullable=False)


class ParcelType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(120))


class Family(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    grave_id = db.Column(db.Integer, db.ForeignKey('grave.id'), nullable=False)


class Payments(db.Model):
    """Tabela dotycząca płatności."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parcel_id = db.Column(db.Integer, db.ForeignKey('parcel.id'), nullable=False)
    date_of_payments = db.Column(db.DateTime(), nullable=False)
    status = db.Column(db.String(120), nullable=False)
    payment_amount = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime(), nullable=False)


class Messages(db.Model):
    """Tabela przechowująca posty administratora na stronę główną."""

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    create_date = db.Column(db.DateTime(), nullable=False)


class Obituaries(db.Model):
    """Tabela do przechowywania nekrologów."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    surname = db.Column(db.String(120), nullable=False)
    # man // woman
    gender = db.Column(db.String(5))
    years_old = db.Column(db.Integer)
    death_date = db.Column(db.DateTime(), nullable=False)
    funeral_date = db.Column(db.DateTime(), nullable=False)
