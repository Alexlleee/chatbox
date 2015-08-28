import os
from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace
from sqlalchemy import create_engine
from redis import ConnectionPool
from databasehandler.dbhandler import DatabaseHandler
import gevent
import uuid
import logging

class ChatNamespace(BaseNamespace):
    _sessions = {}
    dbHandler = None
    cookieName = None

    def __init__(self, environ, ns_name, request=None):
        self._log = logging.getLogger(self.__class__.__name__)
        self.uuid = str(uuid.uuid1())
        self.user = None
        self.USER_LIST_METHOD = 'users'
        self.LOGIN_INFO_METHOD = 'login_info'
        self.ENTER_USER_METHOD = 'enter'
        self.EXIT_USER_METHOD = 'exit'
        self.MESSAGE_LIST_METHOD = 'messages'
        self.TOP_LIST_METHOD = 'top_list'
        self.CHAT_METHOD = 'chat'
        self.REMOVE_MSG_METHOD = 'remove_msg'
        BaseNamespace.__init__(self, environ, ns_name, request)

    @staticmethod
    def set_db_handler(dbhandler):
        ChatNamespace.dbHandler = dbhandler

    def initialize(self):
        """
        Session initialized
        :return:
        """
        log = self._log.getChild('initialize')
        cookie = self.get_cookie(self.cookieName)
        user = self.dbHandler.get_user_by_cookie(cookie)
        if not user:
            self.disconnect()
        self.user = user
        if self.is_user_entered():
            self._broadcast(self.ENTER_USER_METHOD, self.user.login)
        self._sessions[self.uuid] = self
        self.emit(self.LOGIN_INFO_METHOD, self.user.login)
        self.emit(self.USER_LIST_METHOD, self.get_online_user_list())
        messageList = self.dbHandler.get_message_list()
        self.emit(self.MESSAGE_LIST_METHOD, messageList)
        topList = self.dbHandler.get_user_top_list()
        self.emit(self.TOP_LIST_METHOD, topList)

    def is_user_exit(self):
        """
        Check is all sessions of user is closed
        :return: bool
        """
        for session in self._sessions.values():
            if session.user.id == self.user.id:
                return False
        return True

    def is_user_entered(self):
        """
        Check is it a new user
        :return:
        """
        for session in self._sessions.values():
            if session.user.id == self.user.id:
                return False
        return True

    def get_online_user_list(self):
        """
        Get online users
        :return: user list
        """
        userList = list(set([session.user.login for session in self._sessions.values()]))
        return userList

    def disconnect(self, *args, **kwargs):
        """
        Session disconnect
        :param args:
        :param kwargs:
        :return:
        """
        if self.user:
            del self._sessions[self.uuid]
            if self.is_user_exit():
                self._broadcast(self.EXIT_USER_METHOD, self.user.login)
        super(ChatNamespace, self).disconnect(*args, **kwargs)

    def on_chat(self, message):
        self.check_auth()
        gevent.spawn(self.hangle_msg, message).join()
        # self.send_msg(message)

    def hangle_msg(self, msg):
        self.check_auth()
        message = self.dbHandler.store_msg(msg, self.user.id, self.user.login)
        self._broadcast(self.CHAT_METHOD, [message.id, message.get_message(), self.user.login,
                                     message.get_str_time()])

    def on_remove_msg(self, msg):
        self.check_auth()
        self.dbHandler.remove_msg(msg)
        self._broadcast(self.REMOVE_MSG_METHOD, msg)

    def _broadcast(self, event, message):
        for s in self._sessions.values():
            s.emit(event, message)

    def get_cookie(self, cookieName):
        """
        Get cookie from request
        :param cookieName: cookie name
        :return:
        """
        if not self.cookieName:
            return ''
        cookieList = self.environ.get("HTTP_COOKIE", '').split(';')
        namePrefix = "".join([cookieName, "="])
        for item in cookieList:
            item = item.replace(" ", "")
            if item.startswith(namePrefix):
                return item[len(namePrefix):]

    def check_auth(self):
        """
        Check authorization
        :return:
        """
        if not self.user:
            self.disconnect()
            raise Exception

def start_socketio():

    def chat(environ, start_response):
        if environ['PATH_INFO'].startswith('/socket.io'):
            return socketio_manage(environ, {'/chat': ChatNamespace})
    dbpath = 'db/database.db'
    if not os.path.exists(os.path.dirname(dbpath)):
        os.makedirs(os.path.dirname(dbpath))
    engine = create_engine("".join(["sqlite:///", dbpath]))
    redisHost = '127.0.0.1'
    redisPort = 6379
    redisConnectionPool = ConnectionPool(host=redisHost, port=int(redisPort))
    dbHandler = DatabaseHandler(engine, redisConnectionPool)
    ChatNamespace.set_db_handler(dbHandler)
    ChatNamespace.cookieName = 'chat_cookie'
    sio_server = SocketIOServer(('', 8080), chat, policy_server=False)
    sio_server.serve_forever()

if __name__ == '__main__':
    logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s] %(name)s > %(message)s',
                       level=logging.DEBUG,
    )
    start_socketio()