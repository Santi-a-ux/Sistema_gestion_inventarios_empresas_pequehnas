# Sistema de Gestión de Productos

Sistema completo de gestión de productos con backend en Flask, frontend en React, base de datos PostgreSQL y stack ELK para logging.

## Características

- **Backend (Flask)**
  - API RESTful completa
  - Autenticación basada en tokens
  - Validación de datos con Marshmallow
  - Logging centralizado con ELK Stack
  - Manejo de errores y excepciones
  - Documentación de API con Swagger

- **Frontend (React)**
  - Interfaz moderna y responsiva
  - Gestión de productos, categorías y proveedores
  - Dashboard con métricas
  - Formularios validados
  - Manejo de errores y notificaciones

- **Base de Datos (PostgreSQL)**
  - Modelos relacionales optimizados
  - Migraciones automáticas
  - Scripts de inicialización
  - Datos de prueba incluidos

- **Logging (ELK Stack)**
  - Elasticsearch para almacenamiento y búsqueda
  - Logstash para procesamiento de logs
  - Kibana para visualización
  - Políticas de retención de logs
  - Logs estructurados en JSON

## Requisitos

- Docker y Docker Compose
- Git

- Python 3.9+ (para desarrollo backend)

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/santiagoaux/product-system-management.git
cd product-system-management
```

2. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

3. Iniciar los servicios:
```bash
docker-compose up -d
```

## Estructura del Proyecto

```
.
├── backend/                 # Aplicación Flask
│   ├── app.py              # Punto de entrada principal
│   ├── logging_config.py   # Configuración de logging
│   ├── requirements.txt    # Dependencias Python
│   └── Dockerfile         # Configuración Docker
├── frontend/               # Aplicación React
│   ├── src/               # Código fuente
│   ├── package.json       # Dependencias Node
│   └── Dockerfile         # Configuración Docker
├── elasticsearch/          # Configuración Elasticsearch
│   ├── config/            # Archivos de configuración
│   └── init-indices.sh    # Script de inicialización
├── logstash/              # Configuración Logstash
│   ├── config/            # Archivos de configuración
│   └── pipeline/          # Configuración de pipelines
├── docker-compose.yml     # Configuración de servicios
└── README.md             # Este archivo
```

## Servicios

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:5001
- **Kibana**: http://localhost:5601
- **Elasticsearch**: http://localhost:9200

## Imágenes DockerHub

Las imágenes están disponibles en DockerHub bajo el usuario `santiagoaux`:

- Backend: `santiagoaux/product-system-backend:1.0.1`
- Frontend: `santiagoaux/product-system-frontend:1.0.1`

## Logging

El sistema utiliza el stack ELK para el manejo centralizado de logs:

1. **Backend**: Los logs se envían a Logstash usando un handler personalizado
2. **Logstash**: Procesa y enriquece los logs
3. **Elasticsearch**: Almacena los logs con políticas de retención
4. **Kibana**: Visualiza y analiza los logs

### Configuración de Logging

- Los logs se envían en formato JSON
- Se incluye información contextual (timestamp, nivel, logger, etc.)

- Índices diarios con el formato `product-system-logs-YYYY.MM.DD`

### Visualización en Kibana

1. Acceder a Kibana (http://localhost:5601)
2. Crear patrón de índice para `product-system-logs-*`
3. Explorar logs en la sección "Discover"
4. Crear dashboards personalizados

## Casos de Uso Funcionales

1. **Gestión de Productos**: Alta, baja, modificación y consulta de productos. Validación de stock, unicidad de nombre/código, y reglas de negocio para categorías.
2. **Gestión de Categorías**: CRUD de categorías, asociación de productos, validación de duplicados y dependencias.
3. **Gestión de Proveedores**: Alta, baja, modificación y consulta de proveedores. Validación de datos de contacto y reglas de negocio para productos asociados.
4. **Gestión de Movimientos de Stock**: Registro de entradas y salidas de inventario, actualización manual de stock, validación de cantidades y motivos de movimiento (compra, venta, ajuste, etc.).
5. **Gestión de Órdenes de Compra**: Creación, actualización y seguimiento de órdenes. Validación de stock, reglas de negocio para estados y notificaciones.
6. **Búsqueda y Filtrado de Productos**: Búsqueda por nombre, categoría o proveedor, y filtrado avanzado para facilitar la gestión y localización de productos en el sistema.


## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Santiago Aux - [@santiagoaux](https://github.com/santiagoaux)

Link del proyecto: [https://github.com/santiagoaux/product-system-management](https://github.com/santiagoaux/product-system-management) 