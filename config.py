#!usr/bin/env python3
"""Główny plik konfiguracyjny"""
try:
    from config_dev import *
    print('zastosowano deweloperskie ustawienia')
except ImportError:
    try:
        from config_prod import *
        print('zastosowano produkcyjne ustawienia')
    except ImportError:
        print('brak pliku konfiguracyjnego!')

class DB:
    """Konfiguracja bazy danych."""

    PATH = CONFIG_DB.PATH
    TRACK_MODIFICATIONS = CONFIG_DB.TRACK_MODIFICATIONS
    DEFAULT_ACTIVE_USER = CONFIG_DB.DEFAULT_ACTIVE_USER


class APP:
    """Konfiguracja aplikacji."""

    IP = CONFIG_APP.IP
    PORT = CONFIG_APP.PORT
    DEBUG = CONFIG_APP.DEBUG
    APP_KEY = CONFIG_APP.APP_KEY


class EMAIL:
    """Konfiguracja serwera poczty."""

    SERVER = CONFIG_EMAIL.SERVER
    PORT = CONFIG_EMAIL.PORT
    SSL = CONFIG_EMAIL.SSL
    USERNAME = CONFIG_EMAIL.USERNAME
    PASSWORD = CONFIG_EMAIL.PASSWORD
    DEFAULT_SENDER = CONFIG_EMAIL.DEFAULT_SENDER
    FILES_PATH = CONFIG_EMAIL.FILES_PATH
