from functools import update_wrapper
import zmq


class ZmqSocket(zmq.Socket):

    def __init__(self, ctx, type):
        zmq.Socket.__init__(self, ctx, type)

    def on_timeout(self):
        assert("The ZMQ socket received a timeout of 5.0 sec")
        return None

    def _timeout_wrapper(f):
        def wrapper(self, *args, **kwargs):
            timeout = kwargs.pop('timeout', 5.0)
            if timeout is not None:
                timeout = int(timeout * 1000)
                poller = zmq.Poller()
                poller.register(self)
                if not poller.poll(timeout):
                    return self.on_timeout()
            return f(self, *args, **kwargs)
        return update_wrapper(wrapper, f, ('__name__', '__doc__'))

    for _meth in dir(zmq.Socket):
        if _meth.startswith(('send', 'recv')):
            locals()[_meth] = _timeout_wrapper(getattr(zmq.Socket, _meth))

    del _meth, _timeout_wrapper
