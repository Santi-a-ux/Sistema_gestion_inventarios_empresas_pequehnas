import logging
import time
from logging_config import setup_logging

def test_logging():
    # Configurar logging
    setup_logging()
    logger = logging.getLogger()

    # Probar diferentes niveles de log
    logger.debug("Este es un mensaje de DEBUG")
    logger.info("Este es un mensaje de INFO")
    logger.warning("Este es un mensaje de WARNING")
    logger.error("Este es un mensaje de ERROR")

    # Probar logs con contexto
    logger.info("Mensaje con contexto", extra={
        'type': 'test',
        'context': {
            'user_id': 123,
            'action': 'test_logging'
        }
    })

    # Probar logs de error con stack trace
    try:
        1/0
    except Exception as e:
        logger.error("Error en prueba", exc_info=True, extra={
            'type': 'test_error',
            'error_type': type(e).__name__
        })

    # Esperar un momento para asegurar que los logs se envíen
    time.sleep(2)

if __name__ == '__main__':
    test_logging() 