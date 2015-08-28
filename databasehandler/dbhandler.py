# -*- coding: utf-8 -*-
from cachelib.sessioncache import SessionCache
from cachelib.messagecache import MessageCache
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from error import error
from models.chat import User
from sqlalchemy import and_
from models.chat import Message
from models.chat import ForbiddenWord
from cachelib import sessioncache
from utils import validator
import re
import logging

class DatabaseHandler(object):
    """
    Class to handle with database
    """

    def __init__(self, dbengine, redis_connection_pool):
        """
        Constructor
        :param dbengine: engine with database
        :param redis_connection_pool: redis connection pool
        """
        self._log = logging.getLogger(self.__class__.__name__)
        self.dbEngine = dbengine
        self.redisConnectionPool = redis_connection_pool
        self.sessionCache = SessionCache(self.redisConnectionPool)
        self.messageCache = MessageCache(self.redisConnectionPool)

    def register_user(self, login, password):
        """
        Register user
        :param login: login
        :param password: passsword
        :return: user identifier
        """
        user = User(login, validator.password_to_hash(password))
        session = self._get_db_session()
        session.add(user)
        try:
            session.commit()
            return user.id
        except (sqlalchemy.exc.IntegrityError, sqlalchemy.exc.OperationalError) as err:
            raise error.Exists(errorMsg="User {} is already exists.".format(login))
        finally:
            session.close()

    def get_user(self, login, password):
        """
        Get user by login and password
        :param login: user login
        :param password: user password
        :return: User object
        """
        session = self._get_db_session()
        enc_password = validator.password_to_hash(password)
        try:
            user = session.query(User).filter(and_(User.login.like(login),
                                                                   User.password.like(enc_password))).one()
            return user
        except sqlalchemy.orm.exc.NoResultFound:
            raise error.IncorrectNameError
        finally:
            session.close()

    def get_user_by_id(self, userid):
        """
        Get user by identifier
        :param userid: user identifier
        :return: user object
        """
        session = self._get_db_session()
        user = session.query(User).get(userid)
        session.close()
        return user

    def get_user_by_cookie(self, cookie):
        """
        Get user by cookie
        :param cookie: HTTP cookie
        :return: user object
        """
        try:
            userId = self.get_authorized_user_id(cookie)
            return self.get_user_by_id(userId)
        except sessioncache.Unauthorized as err:
            return None

    def set_session(self, userid):
        """
        Set HTTP session
        :param userid: user identifier
        :return: cookie
        """
        return self.sessionCache.set_session(userid)

    def close_session(self, cookie):
        """
        Log out
        :param cookie: http cookie
        :return:
        """
        self.sessionCache.close_session(cookie)

    def get_authorized_user_id(self, cookie):
        """
        Get authorized user identifier
        :param cookie: HTTP cookie
        :return: user identifier
        """
        return self.sessionCache.get_authorized_user_id(cookie)

    def store_msg(self, msg, userid, login):
        """
        Store message from user
        :param msg: message
        :param userid: user identifier
        :return: message object
        """
        session = self._get_db_session()
        forbiddenWordList = [item.word for item in session.query(ForbiddenWord).all()]

        def replace(match):
            word = match.group()
            if word.lower() in forbiddenWordList:
                return '*' * len(word)
            else:
                return word

        msg = re.sub(r'\b\w*\b', replace, msg, flags=re.I|re.U)
        message = Message(msg, userid)
        session.add(message)
        session.commit()
        self.messageCache.add_message(message.id, msg, login, message.get_str_time())
        session.close()
        return message

    def remove_msg(self, messageid):
        """
        Remove message
        :param messageid: message identifier
        :return:
        """
        self.messageCache.delete_message(messageid)

    def get_message_list(self):
        """
        Get message list
        :return:
        """
        return self.messageCache.get_message_list()

    def get_user_top_list(self):
        """
        Get the most active users
        :return:
        """
        session = self._get_db_session()
        res = session.query(User.login).join(Message).group_by(User.id).order_by(sqlalchemy.desc(sqlalchemy.func.count(Message.id))).limit(5)
        session.close()
        return [item[0] for item in res]

    def _get_db_session(self):
        """
        Get database session
        :return: database session
        """
        Session = sessionmaker(bind=self.dbEngine)
        return Session()
