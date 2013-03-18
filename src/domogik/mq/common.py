
def socketid2hex(sid):
    """Returns printable hex representation of a socket id.
    """
    ret = ''.join("%02X" % ord(c) for c in sid)
    return ret

def split_address(msg):
    """Function to split return Id and message received by ROUTER socket.

    Returns 2-tuple with return Id and remaining message parts.
    Empty frames after the Id are stripped.
    """
    ret_ids = []
    for i, p in enumerate(msg):
        if p:
            ret_ids.append(p)
        else:
            break
    return (ret_ids, msg[i + 1:])
