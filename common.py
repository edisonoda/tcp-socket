import hashlib

# Padronização das ações:
# - GET arquivo.ext
# - START filename size
# - DATA bytes
# - ERROR msg
# - END sha256

S_IP = '127.0.0.1'
S_PORT = 2000

FILE_DIR = 'files'
BUFFER_SIZE = 8192

def recv_exact(sock, size):
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return None
        data.extend(chunk)
    return bytes(data)

def recv_frame(sock):
    header = recv_exact(sock, 10)
    if not header:
        return None, None
    
    cmd_len = int(header[:5].decode('ascii'))
    data_len = int(header[5:].decode('ascii'))
    cmd = recv_exact(sock, cmd_len) if cmd_len else b''
    if cmd is None:
        return None, None
    data = recv_exact(sock, data_len) if data_len else b''
    if data is None:
        return None, None
    return cmd, data

def send_frame(sock, cmd, data=b''):
    header = f'{len(cmd):05}{len(data):05}'.encode('ascii')
    sock.sendall(header + cmd + data)