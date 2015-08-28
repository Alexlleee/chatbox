# -*- coding: utf-8 -*-
import hashlib
import re
import uuid
import MySQLdb
from error import error
from json import dumps

ERROR_CODE = "errorcode"
REASON = "reason"
DATA = "data"
VERSION = "version"

## Функция создания JSON ответа
# @param errorCode - код ошибки
# @param reason - описание ошибки
# @param data - данные
# @param version - версия протокола
# @return - JSON ответ
def create_json_response(errorCode=0, reason="", data={}, version=3):
    return dumps({ERROR_CODE: errorCode, REASON: reason, DATA: data, VERSION: version})

def escape(string):
    """
    Escape characters
    :param string: non-escaped string
    :return: escaped string
    """
    return MySQLdb.escape_string(string)

## Метод проверяющий login
# @param login - логин для проверки
# @return если логин верный - True, иначе - False или NameError Exception
def is_valid_login(login):
    if not bool(re.match("^[A-Za-z0-9\._-]+$", login)):
        raise error.IncorrectNameError("The login field is incorrect.")
    return True

## Метод проверяющий является ли строка e-mail'ом
# @param email - входная строка
# @return если входная строка является e-mail'ом - True, иначе - False
def is_email(email):
    email = email or ""
    return bool(re.match("^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", email))

## Метод проверяющий пароль
# @param password - пароль для проверки
# @return если пароль верный - True, иначе - False или NameError Exception
def is_valid_password(password):
    if not password:
        raise error.BaseException("The password field is required.", 5)
    if len(password) not in range(4, 101):
        raise error.BaseException("The password must be between 4 and 100 characters.", 6)
    if not bool(re.match("^[A-Za-z0-9$\\\/\._-]+$", password)):
        raise error.BaseException("The password field has forbidden characters.", 7)
    return True

## Функция хеширования пароля со стороны клиента. При добавлении нового пользователя пароль передаётся в открытом виде,
# при других запросах - в виде хэша
# @param password - пароль
# @return - зашифрованный пароль
def password_to_client_hash(password):
    return hashlib.sha1(password).hexdigest()

## Функция переводящая пароль в хэш
# @param password - пароль
# @return - зашифрованный пароль
def password_to_hash(password):
    return hashlib.sha224(password).hexdigest()

## Функция вовращающая уникальный uuid
# @return uuid
def get_uuid():
    return str(uuid.uuid1())
