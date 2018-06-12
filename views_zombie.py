#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plik zawierający funkcje renderowanych stron dostępnych dla użytkownika."""
# importy modułów py
import bcrypt
from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import current_user, login_required, login_user
from sqlalchemy import func, and_, or_

# importy nasze

from data_validate import DataForm, PwForm, OldPwForm, NewGraveForm, owner_required
from db_models import db, User, Grave, Parcel, ParcelType, Family
from data_db_manage import change_user_data, change_user_pw

pages_user = Blueprint('pages_user', __name__)


