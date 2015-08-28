__author__ = 'alex'
import random
import redis

class MessageCache(object):
    """
    Cache class to store confirm codes based on Redis noSQL database
    """
    def __init__(self, connection_pool=None, host='127.0.0.1', port=6379):
        if connection_pool:
            self.server = redis.Redis(connection_pool=connection_pool)
        else:
            self.server = redis.Redis(host, port)
        self.USER_LOGIN = "userlogin"
        self.MESSAGE = "message"
        self.TIMESTAMP = 'timestamp'
        self.MESSAGE_ID = 'id'
        self.MESSAGE_KEY = 'messageid:'
        self.MESSAGE_TIMEOUT = 86400

    def add_message(self, messageid, message, userlogin, timestamp):
        """
        Add message to cache
        :param messageid: message identifier
        :param message: message
        :param userlogin: user login
        :param timestamp: timestamp
        :return:
        """
        with self.server.pipeline() as pipe:
            messageKey = self._get_message_key(messageid)
            pipe.multi()
            pipe.hmset(messageKey, {self.MESSAGE_ID: messageid, self.MESSAGE: message,
                                    self.USER_LOGIN: userlogin, self.TIMESTAMP: timestamp})
            pipe.expire(messageKey, self.MESSAGE_TIMEOUT)
            pipe.execute()

    def delete_message(self, messageid):
        """
        Delete message
        :param messageid: message identifier
        :return:
        """
        self.server.delete(self._get_message_key(messageid))

    def get_message_list(self):
        """
        Get message list
        :return:
        """
        keyList = self.server.keys('{}*'.format(self.MESSAGE_KEY))
        result = []
        for key in keyList:
            messageInfo = self.server.hmget(key, self.MESSAGE_ID, self.MESSAGE, self.USER_LOGIN, self.TIMESTAMP)
            result.append(messageInfo)
        result.sort(key=lambda r: r[3])
        return result

    def _get_message_key(self, messageid):
        return "{}{}".format(self.MESSAGE_KEY, messageid)


def main():
    cache = MessageCache()
    import time
    import datetime
    print(cache.get_message_list())
    return
    import random
    for x in xrange(1, 100):
        cache.add_message(x, "Message %s" % x, "Login %s" % (random.randint(1, 5)), datetime.datetime.utcnow())
        messageList = cache.get_message_list()
        print(messageList)
        for item in messageList:
            ts = datetime.datetime.strptime(item[3],'%Y-%m-%d %H:%M:%S.%f')
        messageList.sort()
        print(messageList)
        print("*"*100)
        time.sleep(0.5)

if __name__ == '__main__':
    main()