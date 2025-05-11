# Sistema de Gestión de Inventario

Un sistema web completo para la gestión de inventario de pequeñas empresas, desarrollado con **React (Frontend)**, **Flask (Backend)**, **PostgreSQL** y monitoreo/logs con **Elasticsearch + Kibana (ELK)**.  
Incluye despliegue con **Docker Compose** y scripts de inicialización.

## Características principales

- Registro y gestión de productos, proveedores y órdenes de compra.
- Control de stock con alertas de reorden.
- Gestión de usuarios y roles (admin, usuario, etc.).
- Manejo de logs y visualización en Kibana.
- Visualizaciones y dashboards personalizados en Kibana.
- Integración y despliegue fácil con Docker Compose.
- Scripts de inicialización de base de datos y datos de ejemplo.

## Arquitectura del Proyecto

```
.
├── frontend/                   # Aplicación React (interfaz de usuario)
├── backend/                    # API Flask (lógica de negocio)
├── init.sql                    # Script de inicialización y seeding de la BD
├── docker-compose.yml
├── elasticsearch + kibana      # Contenedores ELK
└── README.md
```

## Requisitos

- Docker y Docker Compose
- (Opcional) Python 3.8+ y Node.js si quieres correr FE/BE fuera de Docker

## Instalación y ejecución rápida

1. **Clona el repositorio:**
   ```bash
   git clone <url-del-repositorio>
   cd <nombre-del-directorio>
   ```

2. **Levanta todo con Docker Compose:**
   ```bash
   docker-compose up --build
   ```

3. **Accede a:**
   - **Frontend:** http://localhost:8080
   - **Backend (API):** http://localhost:5000
   - **Kibana:** http://localhost:5601
   - **Elasticsearch:** http://localhost:9200

## Scripts de inicialización

- El archivo `init.sql` crea la estructura de la base de datos y agrega datos de ejemplo (productos, proveedores, categorías, usuario admin, etc.).

## Casos de uso funcionales

- [x] Registro y edición de productos
- [x] Gestión de proveedores
- [x] Creación y seguimiento de órdenes de compra
- [x] Control de stock y alertas de reorden
- [x] Gestión de usuarios y roles
- [x] Manejo de errores y mensajes amigables
- [x] Visualización de logs y datos en Kibana

## Logs y monitoreo con ELK

- Todos los eventos importantes y logs del backend se envían a Elasticsearch.
- Puedes visualizar logs y datos en tiempo real desde **Kibana**.
- Dashboards y visualizaciones personalizadas para productos, proveedores y órdenes.

## Visualizaciones recomendadas en Kibana

- **Productos por categoría** (gráfico de barras)
- **Stock de productos** (gráfico de barras)
- **Órdenes por estado** (gráfico circular)
- **Proveedores registrados por nombre** (gráfico de barras)
- **Alertas de stock bajo** (tabla)
- **Logs de acciones y errores** (Discover)

## Usuarios de prueba

- **Admin:**  
  - Usuario: `admin`  
  - Contraseña: `admin123`
- Puedes crear más usuarios desde la interfaz o la API.

## Pruebas y validaciones

- Todos los flujos principales han sido validados.
- Manejo de errores y mensajes claros para el usuario.
- Roles y permisos probados.

## Cómo contribuir

1. Haz un fork del repositorio.
2. Crea una rama para tu feature (`git checkout -b feature/NuevaFeature`)
3. Haz commit de tus cambios.
4. Abre un Pull Request.

## Licencia

Este proyecto está bajo la Licencia MIT. 