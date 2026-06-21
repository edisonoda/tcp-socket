import hashlib

# Padronização das ações:
# - GET arquivo.ext
# - START size
# - DATA seq checksum bytes
# - (N)ACK seq
# - ERROR msg
# - END

S_IP = '127.0.0.1'
S_PORT = 2000

FILE_DIR = 'files'
BUFFER_SIZE = 1024

def parse_msg(msg):
    parts = msg.split(b' ', 2)
    if not parts:
        return None, None
    
    # 0: ação, 1-N: outros argumentos
    return parts[0], parts[1:]