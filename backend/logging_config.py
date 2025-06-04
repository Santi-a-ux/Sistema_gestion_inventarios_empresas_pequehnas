import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    # Configurar el logger raíz
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Crear directorio de logs si no existe
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configurar handler para archivo
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
    logger.addHandler(file_handler)

    # Configurar handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.info("Configuración de logging completada") 