# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, create_engine, DateTime, ForeignKey, TEXT, UnicodeText, Unicode
import datetime
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    login = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    messages = relationship("Message", backref='user', cascade="all, delete, delete-orphan")

    def __init__(self, login, password):
        self.login = login
        self.password = password

    def __repr__(self):
        return "<User(id='%s', login='%s', password='%s')>" % (self.id, self.login, self.password)

    def to_dict(self):
        return {"id": self.id, "login": self.login}

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    message = Column(TEXT)
    time = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'))

    def __init__(self, message, userid):
        if isinstance(message, str):
            self.message = unicode(message, 'utf-8')
        else:
            self.message = message
        self.user_id = userid

    def get_message(self):
        return self.message.encode("utf-8")

    def get_str_time(self):
        return Message.time_to_str(self.time)

    @staticmethod
    def time_to_str(time):
        return datetime.datetime.strftime(time, '%H:%M:%S')

    def __repr__(self):
        return "<Message((%s) user(id='%s'): message='%s')>" % (self.time, self.user_id, self.get_message())

class ForbiddenWord(Base):

    __tablename__ = 'forbiddenwords'

    id = Column(Integer, primary_key=True)
    word = Column(String, unique=True)

    def __init__(self, word):
        if isinstance(word, str):
            self.word = unicode(word, 'utf-8')
        else:
            self.word = word

    def get_word(self):
        return self.word.encode('utf-8')

    def __repr__(self):
        return "<Forbidden word '%s'>" % (self.get_word())
