#!usr/bin/env python3
"""Plik konfiguracyjny."""
import os


class CONFIG_DB:
    """Konfiguracja bazy danych."""

    PATH = os.environ['DB_PATH']
    TRACK_MODIFICATIONS = False
    DEFAULT_ACTIVE_USER = False


class CONFIG_APP:
    """Konfiguracja aplikacji."""

    IP = '0.0.0.0'
    PORT = 8080
    DEBUG = False
    APP_KEY = os.environ['APP_KEY']


class CONFIG_EMAIL:
    """Konfiguracja serwera poczty."""

    SERVER = 'poczta.o2.pl'
    PORT = 465
    SSL = True
    USERNAME = os.environ['EMAIL_USERNAME']
    PASSWORD = os.environ['EMAIL_PASSWORD']
    DEFAULT_SENDER = 'graveyard_manager@o2.pl'
    FILES_PATH = 'static/emails/'
