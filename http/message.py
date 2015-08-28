# -*- coding: utf-8 -*-
import re
import time

class BaseMessage(object):
    """
    HTTP base message structure class
    """
    CONTENT_LEN = 'Content-Length'
    CONTENT_LEN_NAME = 'content_length'
    CONTENT_NAME = 'content'
    CONTENT_LEN_MATCH = re.compile(r"^.*?(%s\D*(?P<%s>\d+)).*?(\r?\n\r?\n)(?P<%s>.*)$" %
                                  (CONTENT_LEN, CONTENT_LEN_NAME, CONTENT_NAME), re.DOTALL)
    NO_CONTENT_MATCH = re.compile(r"^.*(\r?\n){2}$", re.DOTALL)
    HEADERS_MATCH = re.compile(r"(?P<key>.*?): (?P<value>.*?)\r?\n")

    def __init__(self, headers={}, body=''):
        """
        Constructor
        :param headers: http headers
        :param body: http body
        """
        self.headers = headers
        self.content = body

    @property
    def content(self):
        return self._body

    @content.setter
    def content(self, value):
        self._body = str(value)
        self.headers[self.CONTENT_LEN] = str(len(self._body))

    def from_string(self, message):
        """
        Load HTTP message from string
        :param message: message in str type
        :raise ValueError: if message if not complete
        """
        if not BaseMessage.is_message_ready(message):
            raise ValueError("The HTTP message is not complete.")
        self.headers.update(dict(self.HEADERS_MATCH.findall(message)))
        try:
            groupDict = BaseMessage.CONTENT_LEN_MATCH.match(message).groupdict()
            self.content = groupDict.get(self.CONTENT_NAME)
        except AttributeError:
            pass

    @staticmethod
    def is_message_ready(message):
        """
        Check message to completeness
        :param message: http message
        :return: message complete - True, else - False
        """
        try:
            groupDict = BaseMessage.CONTENT_LEN_MATCH.match(message).groupdict()
            return int(groupDict.get(BaseMessage.CONTENT_LEN_NAME)) <= len(groupDict.get(BaseMessage.CONTENT_NAME))
        except AttributeError as err:
            return bool(BaseMessage.NO_CONTENT_MATCH.match(message))

    @staticmethod
    def get_message_len(message):
        """
        Get length of message
        :param message: http message
        :return: length
        """
        try:
            groupDict = BaseMessage.CONTENT_LEN_MATCH.match(message).groupdict()
            return message.find(b'\r\n\r\n')+len(b'\r\n\r\n') + int(groupDict.get(BaseMessage.CONTENT_LEN_NAME))
        except AttributeError as err:
            return message.find(b'\r\n\r\n')+len(b'\r\n\r\n')

    def __str__(self):
        """
        Parse message to string
        :return: message in string type
        """
        return "\r\n\r\n".join(["\r\n".join([": ".join([k, v]) for k, v in self.headers.items()]), self.content])


class Request(BaseMessage):
    """
    HTTP request class
    """
    COOKIE = 'Cookie'
    METHOD = 'method'
    URL = 'url'
    VERSION = 'version'
    POST_METHOD_LOWER = 'post'
    REQUEST_INFO_MATCH = re.compile(r"^(?P<%s>.*?) (?P<%s>.*?) HTTP/(?P<%s>.*?)\r?\n" % (METHOD, URL, VERSION),
                                   re.DOTALL)

    def __init__(self, headers={}, body='', method='GET', version='1.0', url='/', params={}):
        """
        Constructor
        :param headers: HTTP headers
        :param body: HTTP content
        :param method: HTTP method
        :param version: HTTP version
        :param url: HTTP url
        """
        BaseMessage.__init__(self, headers, body)
        self.method = method
        self.version = version
        self.url = url
        self.params = params

    def from_string(self, message):
        info = self.REQUEST_INFO_MATCH.findall(message)
        if not info:
            raise ValueError("Message has not HTTP method info.")
        self.method = info[0][0]
        self.url = info[0][1]
        self.version = info[0][2]
        BaseMessage.from_string(self, message)
        self.parse_params()

    def get_cookie(self, name):
        """
        Get cookie from request
        :param name: cookie key name
        :return: cookie value
        """
        cookieList = self.headers.get(self.COOKIE, '').split(';')
        namePrefix = "".join([name, "="])
        for item in cookieList:
            item = item.replace(" ", "")
            if item.startswith(namePrefix):
                return item[len(namePrefix):]
        return None

    def __str__(self):
        return "\r\n".join(["%s %s HTTP/%s" % (self.method.upper(), self.url, self.version), BaseMessage.__str__(self)])

    def parse_params(self):
        """
        Parse HTTP params
        """
        if self.method.lower() == self.POST_METHOD_LOWER:
            for param in self.content.split("&"):
                result = param.split("=", 1)
                if len(result) == 2:
                    self.params[result[0]] = result[1]

    def get_param(self, name):
        """
        Get HTTP request parameter
        :param name: parameter name
        :return: parameter value
        """
        return self.params[name]

class Response(BaseMessage):
    """
    HTTP response class
    """
    SET_COOKIE = 'Set-Cookie'
    COOKIE_PATH = 'Path'
    COOKIE_HTTP_ONLY = 'HttpOnly'
    COOKIE_EXPIRES = 'Expires'
    STATUS_CODE = 'status_code'
    STATUS_NAME = 'status_name'
    VERSION = 'version'
    RESPONSE_INFO_MATH = re.compile(r"^HTTP/(?P<%s>.*?) (?P<%s>.*?) (?P<%s>.*?)\r?\n" % (VERSION, STATUS_CODE,
                                                                                        STATUS_NAME), re.DOTALL)

    def __init__(self, headers={
        "Date": time.strftime("%a, %d-%b-%Y %T GMT", time.gmtime(time.time())),
        "Server": "Python asyncio server",
        "Content-Type": "text/html; charset=utf-8",

    },
                 body='', responsecode=200, version='1.0'):
        """
        Constructor
        :param headers: HTTP header
        :param body: HTTP content
        :param responsecode: HTTP response code
        :param statusName: HTTP response shortcut
        :param version: HTTP version
        """
        BaseMessage.__init__(self, headers, body)
        self.responses = {
        100: ('Continue', 'Request received, please continue'),
        101: ('Switching Protocols',
              'Switching to new protocol; obey Upgrade header'),

        200: ('OK', 'Request fulfilled, document follows'),
        201: ('Created', 'Document created, URL follows'),
        202: ('Accepted',
              'Request accepted, processing continues off-line'),
        203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
        204: ('No Content', 'Request fulfilled, nothing follows'),
        205: ('Reset Content', 'Clear input form for further input.'),
        206: ('Partial Content', 'Partial content follows.'),

        300: ('Multiple Choices',
              'Object has several resources -- see URI list'),
        301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
        302: ('Found', 'Object moved temporarily -- see URI list'),
        303: ('See Other', 'Object moved -- see Method and URL list'),
        304: ('Not Modified',
              'Document has not changed since given time'),
        305: ('Use Proxy',
              'You must use proxy specified in Location to access this '
              'resource.'),
        307: ('Temporary Redirect',
              'Object moved temporarily -- see URI list'),

        400: ('Bad Request',
              'Bad request syntax or unsupported method'),
        401: ('Unauthorized',
              'No permission -- see authorization schemes'),
        402: ('Payment Required',
              'No payment -- see charging schemes'),
        403: ('Forbidden',
              'Request forbidden -- authorization will not help'),
        404: ('Not Found', 'Nothing matches the given URI'),
        405: ('Method Not Allowed',
              'Specified method is invalid for this resource.'),
        406: ('Not Acceptable', 'URI not available in preferred format.'),
        407: ('Proxy Authentication Required', 'You must authenticate with '
              'this proxy before proceeding.'),
        408: ('Request Timeout', 'Request timed out; try again later.'),
        409: ('Conflict', 'Request conflict.'),
        410: ('Gone',
              'URI no longer exists and has been permanently removed.'),
        411: ('Length Required', 'Client must specify Content-Length.'),
        412: ('Precondition Failed', 'Precondition in headers is false.'),
        413: ('Request Entity Too Large', 'Entity is too large.'),
        414: ('Request-URI Too Long', 'URI is too long.'),
        415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
        416: ('Requested Range Not Satisfiable',
              'Cannot satisfy request range.'),
        417: ('Expectation Failed',
              'Expect condition could not be satisfied.'),
        428: ('Precondition Required',
              'The origin server requires the request to be conditional.'),
        429: ('Too Many Requests', 'The user has sent too many requests '
              'in a given amount of time ("rate limiting").'),
        431: ('Request Header Fields Too Large', 'The server is unwilling to '
              'process the request because its header fields are too large.'),

        500: ('Internal Server Error', 'Server got itself in trouble'),
        501: ('Not Implemented',
              'Server does not support this operation'),
        502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
        503: ('Service Unavailable',
              'The server cannot process the request due to a high load'),
        504: ('Gateway Timeout',
              'The gateway server did not receive a timely response'),
        505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
        511: ('Network Authentication Required',
              'The client needs to authenticate to gain network access.'),
        }
        self.responseCode = responsecode
        self.version = version

    @property
    def responseCode(self):
        return self._responseCode

    @responseCode.setter
    def responseCode(self, value):
        self._responseCode = str(value)
        self._responseCodeName = self.responses.get(int(value))[0]

    @property
    def responseCodeName(self):
        return self._responseCodeName

    def from_string(self, message):
        info = self.RESPONSE_INFO_MATH.findall(message)
        if not info:
            raise ValueError("Message has not HTTP response info.")
        self.version = info[0][0]
        self._responseCode = info[0][1]
        self._responseCodeName = info[0][2]
        BaseMessage.from_string(self, message)

    def set_cookie(self, name, value, path='/', expiry=2592000):
        """
        Set cookie to response
        :param name: cookie name
        :param value: cookie value
        :param path: cookie path
        :return:
        """
        self.headers[self.SET_COOKIE] = '; '.join(["=".join([name, str(value)]),
                                                   "=".join([self.COOKIE_PATH, path]),
                                                   "=".join([self.COOKIE_EXPIRES, time.strftime("%a, %d-%b-%Y %T GMT",
                                                                                                time.gmtime(time.time()
                                                                                                            + expiry))]),
                                                   self.COOKIE_HTTP_ONLY])

    def __str__(self):
        return "\r\n".join(["HTTP/%s %s %s" % (self.version, self.responseCode, self.responseCodeName),
                            BaseMessage.__str__(self)])