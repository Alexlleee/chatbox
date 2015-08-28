import asyncore
import socket
from http.message import Response
from http.message import Request
import gevent
import logging

class Session(asyncore.dispatcher):
    """
    HTTP session class
    """
    sessions = {}

    def __init__(self, sock=None, map=None, addr=None, *args, **kwargs):
        self._log = logging.getLogger(self.__class__.__name__)
        self.in_buffer_size = 4048
        self.out_buffer_size = 4048
        self.rbuff = b''
        self.wbuff = b''
        self.addr = addr
        asyncore.dispatcher.__init__(self, sock, map)
        self.sessions[id(self)] = self

    def handle_read(self):
        self.rbuff += self.recv(self.in_buffer_size)
        msg = self.get_block()
        if msg:
            request = Request()
            request.from_string(msg)
            gevent.spawn(self.render, request).join()

    def render(self, request):
        """
        Render response
        :param request: http request
        """
        response = Response()
        self.write(response)

    def is_block_ready(self):
        """
        Check reade buffer to completeness
        :return: read buffer complete - True, else - False
        """
        return Request.is_message_ready(self.rbuff)

    def get_block(self):
        """
        Get http request
        :return: http request
        """
        block = None
        if self.is_block_ready():
            rindex = Request.get_message_len(self.rbuff)
            block = self.rbuff[:rindex]
            self.rbuff = self.rbuff[rindex:]
        return block

    def writable(self):
        return len(self.wbuff) > 0

    def handle_write(self):
        self.send(self.wbuff[:self.out_buffer_size])
        self.wbuff = self.wbuff[self.out_buffer_size:]

    def handle_close(self):
        self.close()
        del self.sessions[id(self)]

    def write(self, response):
        """
        Write response
        :param response: response
        """
        self.wbuff += str(response)

class Server(asyncore.dispatcher):

    def __init__(self, host, port, handler):
        self._log = logging.getLogger(self.__class__.__name__)
        self.handler = handler
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            self.wrap_session(sock, addr)

    def wrap_session(self, sock, addr, *args, **kwargs):
        """
        Wrap session
        :param sock: socket
        :param addr: client address
        :param args: args
        :param kwargs: kwargs
        """
        self.handler(sock, addr=addr)

if __name__ == '__main__':
    logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s] %(name)s > %(message)s',
                       level=logging.DEBUG,
    )
    server = Server('localhost', 9090, Session)
    asyncore.loop()