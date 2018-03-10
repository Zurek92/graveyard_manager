#!usr/bin/env python3
'''plik konfiguracyjny'''

class DB:
    '''konfiguracja bazy danych'''
    PATH = 'sqlite:///grave_db.db'
    TRACK_MODIFICATIONS = False

class APP:
    '''konfiguracja aplikacji'''
    IP = '0.0.0.0'
    PORT = 5000
    DEBUG = True
    APP_KEY = '\x88\xe7\xfa\x94\xbb\xa0s\xfa\xaf~\x03\xb7:\x9d\xe6I\x12\x07\\\x02yXU\xb6'

class EMAIL:
    SERVER = 'poczta.o2.pl'
    PORT = 465
    SSL = True
    USERNAME = 'graveyard_manager'
    PASSWORD = '@T15x?q8'
    DEFAULT_SENDER = 'graveyard_manager@o2.pl'
