# Sistema de Gestión de Inventario

Un sistema web simple para la gestión de inventario de pequeñas empresas, desarrollado con Python y Flask.

## Características

- Registro y gestión de productos
- Control de stock con alertas de reorden
- Interfaz web intuitiva y responsiva
- Base de datos SQLite integrada
- Sistema de alertas para productos con bajo stock

## Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd <nombre-del-directorio>
```

2. Crear un entorno virtual (opcional pero recomendado):
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

## Ejecución

1. Activar el entorno virtual (si se creó uno):
```bash
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Iniciar la aplicación:
```bash
python app.py
```

3. Abrir un navegador web y acceder a:
```
http://localhost:5000
```

## Uso

1. **Ver Inventario**: La página principal muestra todos los productos en el inventario.
2. **Agregar Producto**: Hacer clic en "Agregar Nuevo Producto" y completar el formulario.
3. **Editar Producto**: Hacer clic en el botón "Editar" de cualquier producto.
4. **Registrar Salida**: Usar el botón "Registrar Salida" para disminuir el stock.
5. **Ver Productos a Reordenar**: Acceder a la sección "Reordenar" para ver productos con bajo stock.

## Estructura del Proyecto

```
.
├── app.py              # Aplicación principal
├── requirements.txt    # Dependencias del proyecto
├── static/            # Archivos estáticos
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── templates/         # Plantillas HTML
    ├── base.html
    ├── inventario.html
    ├── agregar_producto.html
    ├── editar_producto.html
    └── reordenar.html
```

## Contribuir

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles. 