import logging
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
import os
import socket
import json
from datetime import datetime

class LogstashHandler(logging.Handler):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = None
        self.formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        print(f"LogstashHandler inicializado para {host}:{port}")

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Conexión exitosa a Logstash en {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Error conectando a Logstash: {str(e)}")
            self.socket = None
            return False

    def emit(self, record):
        if not self.socket:
            if not self.connect():
                return

        try:
            log_entry = self.format(record)
            # Convert to dict to add @timestamp
            log_dict = json.loads(log_entry)
            if '@timestamp' not in log_dict:
                log_dict['@timestamp'] = datetime.utcnow().isoformat() + 'Z'
            # Add log level
            log_dict['level'] = record.levelname
            # Add additional context
            log_dict['logger'] = record.name
            log_dict['path'] = record.pathname
            log_dict['line'] = record.lineno
            log_dict['function'] = record.funcName
            print(f"Enviando a Logstash: {json.dumps(log_dict)}")
            self.socket.sendall((json.dumps(log_dict) + "\n").encode())
        except Exception as e:
            print(f"Error enviando log a Logstash: {str(e)}")
            self.socket = None

def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)  # Set default level to INFO

    # File handler for local logs
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Logstash handler
    logstash_handler = LogstashHandler('logstash', 5000)
    logstash_handler.setLevel(logging.INFO)
    root_logger.addHandler(logstash_handler)

    # Configurar loggers específicos
    loggers_to_configure = [
        'gunicorn.error',
        'gunicorn.access',
        'werkzeug',
        'flask.app'
    ]

    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        # Limpiar handlers existentes
        logger.handlers = []
        # Asegurar que los logs se propaguen al logger raíz
        logger.propagate = True
        # Añadir el handler de Logstash directamente
        logger.addHandler(logstash_handler)

    # Mostrar handlers activos
    print("\nHandlers activos en el logger raíz:")
    for handler in root_logger.handlers:
        print(f"- {handler.__class__.__name__}")

    # Log de prueba
    root_logger.info("Configuración de logging completada")

    return root_logger 