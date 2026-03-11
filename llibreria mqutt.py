import usocket as socket
import ustruct as struct
from ubinascii import hexlify

class MQTTException(Exception):
    pass

class MQTTClient:
    def __init__(self, client_id, server, port=0, user=None, password=None, keepalive=0, ssl=False, ssl_params={}):
        if port == 0:
            port = 8883 if ssl else 1883
        self.client_id = client_id
        self.sock = None
        self.server = server
        self.port = port
        self.ssl = ssl
        self.ssl_params = ssl_params
        self.pid = 0
        self.cb = None
        self.user = user
        self.pswd = password
        self.keepalive = keepalive
        self.lw_topic = None
        self.lw_msg = None
        self.lw_qos = 0
        self.lw_retain = False

    def _send_str(self, s):
        self.sock.write(struct.pack("!H", len(s)))
        self.sock.write(s)

    def _recv_len(self):
        n = 0
        sh = 0
        while 1:
            res = self.sock.read(1)[0]
            n |= (res & 0x7F) << sh
            if not res & 0x80:
                return n
            sh += 7

    def connect(self, clean_session=True):
        self.sock = socket.socket()
        addr = socket.getaddrinfo(self.server, self.port)[0][-1]
        self.sock.connect(addr)
        if self.ssl:
            import ussl
            self.sock = ussl.wrap_socket(self.sock, **self.ssl_params)
        premsg = bytearray(b"\x10\0\0\x04MQTT\x04\x02\0\0")
        msg = bytearray(b"\x10\0\0\0")
        msg[1] = 10 + 2 + len(self.client_id)
        msg[3] = 4
        if self.user is not None:
            msg[1] += 2 + len(self.user) + 2 + len(self.pswd)
            msg[9] |= 0xC0
        if self.keepalive:
            msg[1] += 2
            msg[10] |= self.keepalive >> 8
            msg[11] |= self.keepalive & 0x00FF
        if not clean_session:
            msg[9] &= 0xFD
        self.sock.write(msg)
        self._send_str(self.client_id)
        if self.user is not None:
            self._send_str(self.user)
            self._send_str(self.pswd)
        res = self.sock.read(4)
        return res[3] & 1

    def disconnect(self):
        self.sock.write(b"\xe0\0")
        self.sock.close()

    def publish(self, topic, msg, retain=False, qos=0):
        pkt = bytearray(b"\x30\0\0\0")
        pkt[0] |= qos << 1 | retain
        sz = 2 + len(topic) + len(msg)
        if qos > 0:
            sz += 2
        assert sz < 2097152
        i = 1
        while sz > 0x7F:
            pkt[i] = (sz & 0x7F) | 0x80
            sz >>= 7
            i += 1
        pkt[i] = sz
        self.sock.write(pkt, i + 1)
        self._send_str(topic)
        if qos > 0:
            self.pid += 1
            self.sock.write(struct.pack("!H", self.pid))
        self.sock.write(msg)
