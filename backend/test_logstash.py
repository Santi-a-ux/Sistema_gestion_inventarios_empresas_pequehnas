import socket
import json
from datetime import datetime

log = {
    "message": "PRUEBA MANUAL DESDE PYTHON",
    "@timestamp": datetime.utcnow().isoformat() + "Z"
}

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("logstash", 5000))
s.sendall((json.dumps(log) + "\n").encode())
s.close() 