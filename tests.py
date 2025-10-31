import socket
import time
from onionchat.utils.funcs import wrap_text, load_class
from onionchat.chat.generic_chat import GenericChat
from onionchat.utils.types import EmptyMessage, TerminateConnection
from onionchat.pipeline_builder import PipelineBuilder

def test_wrap_text():
    assert wrap_text("abcdef", 2) == ["ab", "cd", "ef"]
    assert wrap_text("abc", 5) == ["abc"]

def test_load_class():
    cls = load_class("onionchat.chat.generic_chat:GenericChat")
    assert cls is GenericChat

def test_generic_chat():
    # create a socketpair for local peer simulation
    s_left, s_right = socket.socketpair()
    try:
        gc = GenericChat(s_left, recv_timeout=0.2)
        instantiated = PipelineBuilder.instantiate_class(GenericChat, {"sock": s_left, "recv_timeout": 0.2})
        assert isinstance(instantiated, GenericChat)

        gc.send_msg("hello")
        data = s_right.recv(1024)
        assert data.decode() == "hello"

        s_right.sendall(b"world")
        assert gc.recv_msg() == "world"

        # no data available -> timeout -> EmptyMessage
        # ensure no data pending
        assert isinstance(gc.recv_msg(), EmptyMessage)

        # when the peer closes, recv returns empty bytes -> TerminateConnection
        s_right.close()
        time.sleep(0.05)
        res = gc.recv_msg()
        assert isinstance(res, TerminateConnection)
    finally:
        try:
            s_left.close()
        except:
            pass