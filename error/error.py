class BaseException(Exception):
    """
    Base exception class
    """
    def __init__(self, errorMsg='Exception', errno=1):
        Exception.__init__(self, errorMsg)
        self.errorMsg = errorMsg
        self.errno = errno

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "%s[errno %s]: %s" % (self.__class__.__name__, self.errno, self.errorMsg)

class IncorrectNameError(BaseException):

    def __init__(self, errorMsg="Login or password are incorrect.", errno=400):
        BaseException.__init__(self, errorMsg, errno)

class Exists(BaseException):

    def __init__(self, errorMsg="Is already exists", errno=2):
        BaseException.__init__(self, errorMsg, errno)

class NotAuthorized(BaseException):
    """
    Not authorized exception
    """
    def __init__(self, errorMsg="You are not logined.", errno=401):
        BaseException.__init__(self, errorMsg, errno)

class Forbidden(BaseException):
    """
    Access denied
    """
    def __init__(self, errorMsg="You are not logined.", errno=403):
        BaseException.__init__(self, errorMsg, errno)


class CameraSharedError(BaseException):

    def __init__(self, errorMsg="Access denied to camera. Not allowed.", errno=6):
        BaseException.__init__(self, errorMsg, errno)

class CameraOwnerError(BaseException):

    def __init__(self, errorMsg="Access denied to camera. You are not the owner of the camera.", errno=5):
        BaseException.__init__(self, errorMsg, errno)

class NotFound(BaseException):
    """
    Not found
    """
    def __init__(self, errorMsg="Not found", errno=404):
        BaseException.__init__(self, errorMsg, errno)


class InternalError(BaseException):
    """
    Internal error
    """
    def __init__(self, errorMsg="Internal error.", errno=500):
        BaseException.__init__(self, errorMsg, errno)


class BlockedError(BaseException):
    """
    Error for blocking user
    """
    def __init__(self, errorMsg='You have been blocked.', errno=600):
        BaseException.__init__(self, errorMsg, errno)

if __name__ == '__main__':
    try:
        raise NotAuthorized
    except BaseException as err:
        print(err.errno)