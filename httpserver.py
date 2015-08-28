# -*- coding: utf-8 -*-
from http.server import Server
import gevent
from http.server import Session
from http.message import Response
from databasehandler.dbhandler import DatabaseHandler
from cachelib.sessioncache import Unauthorized
import asyncore
import urllib
import mimetypes
from sqlalchemy import create_engine
from redis import ConnectionPool
from utils import validator
from cachelib.sessioncache import BaseSessionException
from error import error
import os
import logging

class ChatSession(Session):
    GET_METHOD_LOWER = 'get'
    POST_METHOD_LOWER = 'post'

    def __init__(self, sock=None, map=None, addr=None, staticpath="", cookiename="chat_cookie", *args, **kwargs):
        Session.__init__(self, sock, map, addr, args, kwargs)
        self.cookieName = cookiename
        self.staticPath = staticpath
        self.dbHandler = None
        self.set_post_urls()
        self.set_get_urls()

    def set_db_handler(self, dbhandler):
        """
        Set database engine
        :param dbhandler: sqlalchemy engine
        """
        self.dbHandler = dbhandler

    def set_post_urls(self):
        """
        Set dictionary where key - regexp url, value - render method
        :return:
        """
        self.postUrlList = {
            '/auth': self.auth,
            '/registration': self.registration,
        }

    def set_get_urls(self):
        """
        Set dictionary where key - regexp url, value - render method
        :return:
        """
        self.getUrlList = {
            '/': self.index,
            '/index.html': self.index,
            '/chat.html': self.chat,
            '/logout': self.log_out,
        }

    def render(self, request):
        log = self._log.getChild("render")
        try:
            method = request.method.lower()
            if method == self.GET_METHOD_LOWER:
                gevent.spawn(self.render_get, request).join()
            elif method == self.POST_METHOD_LOWER:
                gevent.spawn(self.render_post, request).join()
            else:
                response = Response()
                response.responseCode = 501
                self.write(response)
        except (error.BaseException, BaseSessionException) as bErr:
            response = Response()
            response.responseCode = 400
            response.content = validator.create_json_response(errorCode=bErr.errno, reason=bErr.errorMsg)
            response.headers['Content-Type'] = 'application/json'
            self.write(response)
        except Exception as err:
            log.exception("Exception in rended: {}".format(err))
            response = Response()
            response.responseCode = 500
            response.content = validator.create_json_response(errorCode=500, reason="Internal error.")
            response.headers['Content-Type'] = 'application/json'
            self.write(response)

    def render_post(self, request):
        """
        Render HTTP POST request
        :param request: http request
        """
        try:
            self.postUrlList[request.url](request)
        except KeyError:
            response = Response()
            response.responseCode = 404
            self.write(response)

    def index(self, request):
        """
        Index Page
        :param request: http request
        :return:
        """
        log = self._log.getChild("index")
        try:
            userId = self._check_auth(request)
            response = self.get_redirect_response("/chat.html")
            self.write(response)
        except Unauthorized:
            url = request.url
            if url == '/':
                url = '/index.html'
            self.get_from_static(url)

    def auth(self, request):
        """
        Authorize user
        :param request:
        :return:
        """
        log = self._log.getChild("auth")
        login = request.get_param('login')
        password = request.get_param('password')
        user = self.dbHandler.get_user(login, password)
        cookie = self.dbHandler.set_session(user.id)
        response = Response()
        response.set_cookie(self.cookieName, cookie)
        response.content = validator.create_json_response(data={})
        response.headers['Content-Type'] = '; '.join(['application/json', 'charset=utf-8'])
        self.write(response)

    def registration(self, request):
        """
        Registrate new user
        :param request: http request
        :return:
        """
        log = self._log.getChild("registration")
        login = request.get_param('login')
        password = request.get_param('password')
        validator.is_valid_login(login)
        validator.is_valid_password(password)
        userId = self.dbHandler.register_user(login, password)
        cookie = self.dbHandler.set_session(userId)
        response = Response()
        response.set_cookie(self.cookieName, cookie)
        response.content = validator.create_json_response(data={})
        response.headers['Content-Type'] = '; '.join(['application/json', 'charset=utf-8'])
        self.write(response)

    def log_out(self, request):
        """
        Sing out
        :param request: http request
        :return:
        """
        log = self._log.getChild("sing_out")
        cookie = request.get_cookie(self.cookieName)
        self.dbHandler.close_session(cookie)
        self.get_redirect_response('/')
        response = self.get_redirect_response('/')
        response.headers['Set-Cookie'] = '{}=""; ' \
                                         'expires=Thu, 01 Jan 1970 00:00:00 GMT; ' \
                                         'path="/" httponly'.format(self.cookieName)
        self.write(response)

    def chat(self, request):
        """
        Render chat page
        :param request: http request
        :return:
        """
        log = self._log.getChild("chat")
        try:
            userId = self._check_auth(request)
            self.get_from_static(request.url)
        except Unauthorized:
            response = self.get_redirect_response('/')
            self.write(response)

    def render_get(self, request):
        """
        Render HTTP GET request
        :param request: request
        """
        log = self._log.getChild("render_get")
        url = request.url
        try:
            self.getUrlList[url](request)
            return
        except KeyError:
            self.get_from_static(url)

    def get_from_static(self, url):
        """
        Get files from static
        :param url: HTTP url
        :return:
        """
        log = self._log.getChild("get_from_static")
        response = Response()
        try:
            path = ''.join([self.staticPath, url])
            with open(path, 'r') as file:
                content = file.read()
                response.content = content
                contentType = self.get_file_content_type(path)
                response.headers['Content-Type'] = '; '.join([contentType, 'charset=utf-8'])
        except Exception as err:
            log.warning("Client: {}, url: {} error: {}".format(self.addr, url, err))
            response.responseCode = 404
        finally:
            self.write(response)

    def get_file_content_type(self, filepath):
        """
        Get HTTP content type of file
        :param filepath: path to file
        :return: Content-Type
        """
        url = urllib.pathname2url(filepath)
        return mimetypes.guess_type(url)[0]

    def _check_auth(self, request):
        """
        Check authorization
        :param request: http request
        :return: user identifier
        """
        cookie = request.get_cookie(self.cookieName)
        return self.dbHandler.get_authorized_user_id(cookie)

    def get_redirect_response(self, path='/'):
        """
        Send redirect
        :param path: redirect path
        :return:
        """
        response = Response()
        response.responseCode = 302
        response.headers['Location'] = path
        return response

class ChatServer(Server):

    def __init__(self, host, port, handler, staticpath='', dbhandler=None):
        Server.__init__(self, host, port, handler)
        self.staticpath = staticpath
        self.dbHanler = dbhandler

    def wrap_session(self, sock, addr, *args, **kwargs):
        handler = self.handler(sock, addr=addr, staticpath=self.staticpath)
        if self.dbHanler:
            handler.set_db_handler(self.dbHanler)

def create_database(engine):
    from models.chat import Base
    Base.metadata.create_all(engine)

def start_http():
    dbpath = 'db/database.db'
    if not os.path.exists(os.path.dirname(dbpath)):
        os.makedirs(os.path.dirname(dbpath))
    engine = create_engine("".join(["sqlite:///", dbpath]))
    create_database(engine)
    redisHost = '127.0.0.1'
    redisPort = 6379
    redisConnectionPool = ConnectionPool(host=redisHost, port=int(redisPort))
    dbHandler = DatabaseHandler(engine, redisConnectionPool)
    server = ChatServer('0.0.0.0', 9090, ChatSession, 'html', dbHandler)
    asyncore.loop()

if __name__ == '__main__':
    logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s] %(name)s > %(message)s',
                       level=logging.DEBUG,
    )
    start_http()