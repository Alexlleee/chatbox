# -*- coding: utf-8 -*-
import hashlib
import uuid
import redis

class BaseSessionException(Exception):
    """
    Base redis exception class
    """
    def __init__(self, errorMsg='Base Redis Exception', errno=1):
        Exception.__init__(self, errorMsg)
        self.errorMsg = errorMsg
        self.errno = errno

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "%s[errno %s]: %s" % (self.__class__.__name__, self.errno, self.errorMsg)

class CookieNotAvailable(BaseSessionException):
    """
    Cookie is already exists exception.
    """
    def __init__(self, errorMsg="Can't generate unique cookie.", errno=21):
        BaseSessionException.__init__(self, errorMsg=errorMsg, errno=errno)

class Unauthorized(BaseSessionException):
    """
    Unauthorized exception. Cookie not found.
    """
    def __init__(self, errorMsg="You are not logined.", errno=401):
        BaseSessionException.__init__(self, errorMsg=errorMsg, errno=errno)

class SessionCache(object):
    """
    Session cache class based on Redis noSQL database
    """
    def __init__(self, connection_pool=None, host='127.0.0.1', port=6379):
        if connection_pool:
            self.server = redis.Redis(connection_pool=connection_pool)
        else:
            self.server = redis.Redis(host, port)
        self.SALT = 'ipisolt2121'
        self.COOKIE_PREFIX = 'cookie:'
        self.USER_ID_PREFIX = 'userid:'

    def set_session(self, userId, oldCookie=None):
        """
        Set cookie to user
        :param userId: user identifier
        :return: cookie name
        :raise CookieNotAvailable: cookie name is already exists.
        """
        # if cookie exists then generate again
        for x in range(0, 2):
            cookie = oldCookie or self.gen_cookie()
            if self.server.setnx(self._get_cookie_key(cookie), userId):
                self.server.sadd(self._get_user_id_key(userId), cookie)
                return cookie
        raise CookieNotAvailable

    def update_session(self, cookie):
        """
        Update cookie name for session
        :param cookie:
        :return: updated cookie name
        :raises:
        :raise Unauthorized: session is unauthorized. cookie not found.
        :raise CookieNotAvailable: cookie name is already exists.
        """
        userId = self.get_authorized_user_id(cookie)
        for x in range(0, 2):
            newCookie = self.gen_cookie()
            try:
                if self.server.renamenx(self._get_cookie_key(cookie),
                                        self._get_cookie_key(newCookie)):
                    pipe = self.server.pipeline()
                    pipe.srem(self._get_user_id_key(userId), cookie)
                    pipe.sadd(self._get_user_id_key(userId), newCookie)
                    result = pipe.execute()
                    if result[1]:
                        return newCookie
            except redis.exceptions.ResponseError as rErr:
                raise Unauthorized
        raise CookieNotAvailable

    def close_session(self, cookie):
        """
        Close session by deleting cookie
        :param cookie: session cookie name
        :return:
        :raise: Unauthorized: session is unauthorized. cookie not found.
        """
        userId = self.get_authorized_user_id(cookie)
        pipe = self.server.pipeline()
        pipe.delete(self._get_cookie_key(cookie))
        pipe.srem(self._get_user_id_key(userId), cookie)
        pipe.execute()

    def close_all_session(self, cookie=None, userId=None):
        """
        Close all session by deleting cookies
        :param cookie: session cookie name
        :return:
        :raise: Unauthorized: session is unauthorized. cookie not found.
        """
        userId = userId or self.get_authorized_user_id(cookie)
        for cookie in self.get_cookie_set_by_userId(userId):
            self.close_session(cookie)
        self.server.delete(self._get_user_id_key(userId))

    def close_others_sessions(self, cookie):
        """
        Close all session among active session by deleting cookies
        :param cookie: session cookie name
        :return:
        :raise: Unauthorized: session is unauthorized. cookie not found.
        """
        userId = self.get_authorized_user_id(cookie)
        self.close_all_session(cookie)
        return self.set_session(userId, cookie)

    def get_authorized_user_id(self, cookie):
        """
        Get user identifier by cookie
        :param cookie: cookie name
        :return: user id
        :raise Unauthorized: user id by cookie not found
        """
        userId = self.server.get(self._get_cookie_key(cookie))
        if not userId:
            raise Unauthorized
        return userId

    def get_cookie_set_by_userId(self, userId):
        """
        Get all cookies by user id
        :param userId: user identirier
        :return: set of cookies
        """
        return self.server.smembers(self._get_user_id_key(userId))

    def gen_cookie(self):
        return "{}{}".format(hashlib.sha1(self.SALT).hexdigest(), hashlib.sha1(str(uuid.uuid1())).hexdigest())

    def _get_user_id_key(self, userId):
        return "{}{}".format(self.USER_ID_PREFIX, userId)

    def _get_cookie_key(self, cookie):
        return "{}{}".format(self.COOKIE_PREFIX, cookie)