from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
from flask_migrate import Migrate
import logging
from marshmallow import Schema, fields, validate, ValidationError
from functools import wraps
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import timedelta
import traceback

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

try:
    import logstash
    LOGSTASH_HOST = os.getenv("LOGSTASH_HOST")
    LOGSTASH_PORT = int(os.getenv("LOGSTASH_PORT", "5000"))
    if LOGSTASH_HOST:
        logstash_handler = logstash.TCPLogstashHandler(LOGSTASH_HOST, LOGSTASH_PORT, version=1)
        logger.addHandler(logstash_handler)
        logger.info(f"LogstashHandler inicializado para {LOGSTASH_HOST}:{LOGSTASH_PORT}")
except Exception as e:
    logger.warning(f"No se pudo inicializar LogstashHandler: {e}")

app = Flask(__name__)
CORS(app, origins=["http://localhost:8080", "http://127.0.0.1:8080"])

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

# Configuración de seguridad
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutos

# Middleware de seguridad
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Decorador para validar tokens
def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        logger.info(f"Validando token para ruta: {request.path}", extra={
            'type': 'auth',
            'method': request.method,
            'path': request.path,
            'headers': dict(request.headers)
        })
        token = request.headers.get('X-API-Token')
        expected_token = os.getenv('API_TOKEN')
        
        if not token:
            logger.error("No se recibió token en la petición", extra={
                'type': 'auth_error',
                'error': 'token_missing'
            })
            return jsonify({"error": "Token no proporcionado"}), 401
        if token != expected_token:
            logger.error("Token inválido", extra={
                'type': 'auth_error',
                'error': 'invalid_token'
            })
            return jsonify({"error": "Token inválido"}), 401
            
        logger.info("Token válido, procediendo con la petición", extra={
            'type': 'auth_success'
        })
        return f(*args, **kwargs)
    return decorated

# Configuración de la base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/inventario')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Log de prueba explícito para Logstash
logger.info("PRUEBA DE LOG A LOGSTASH", extra={"type": "test"})

logging.error("PRUEBA ERROR DESDE EL RAÍZ")

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    logger.error("PRUEBA ERROR SIMPLE")
    logger.error(f"Recurso no encontrado: {request.path}", extra={
        'type': 'not_found',
        'path': request.path,
        'method': request.method,
        'headers': dict(request.headers)
    })
    return jsonify({"error": "Recurso no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(
        f"Error interno del servidor: {str(error)}\n{traceback.format_exc()}",
        extra={
            'type': 'server_error',
            'error': str(error),
            'path': request.path,
            'method': request.method
        }
    )
    return jsonify({"error": "Error interno del servidor"}), 500

@app.errorhandler(400)
def bad_request_error(error):
    logger.error(f"Error en la solicitud: {str(error)}", extra={
        'type': 'bad_request',
        'error': str(error),
        'path': request.path,
        'method': request.method,
        'data': request.get_json(silent=True)
    })
    return jsonify({"error": "Error en la solicitud"}), 400

@app.errorhandler(ValidationError)
def validation_error(error):
    logger.error(f"Error de validación: {str(error)}", extra={
        'type': 'validation_error',
        'error': str(error),
        'path': request.path,
        'method': request.method,
        'data': request.get_json(silent=True)
    })
    return jsonify({"error": "Error de validación", "detalles": error.messages}), 400

# Modelos
class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_categoria = db.Column(db.String(100), unique=True, nullable=False)
    productos = db.relationship('Producto', backref='categoria', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre_categoria': self.nombre_categoria
        }

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    precio_costo = db.Column(db.Numeric(10, 2), nullable=False)
    precio_venta = db.Column(db.Numeric(10, 2), nullable=False)
    descripcion = db.Column(db.Text)
    cantidad = db.Column(db.Integer, default=0)
    umbral_reorden = db.Column(db.Integer, default=10)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'sku': self.sku,
            'precio_costo': float(self.precio_costo),
            'precio_venta': float(self.precio_venta),
            'descripcion': self.descripcion,
            'cantidad': self.cantidad,
            'umbral_reorden': self.umbral_reorden,
            'categoria_id': self.categoria_id,
            'categoria': self.categoria.nombre_categoria if self.categoria else None,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat()
        }

class Proveedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'email': self.email,
            'telefono': self.telefono,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat()
        }

class OrdenCompra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_entrega = db.Column(db.DateTime)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, completada, cancelada
    total = db.Column(db.Numeric(10, 2), default=0)
    items = db.relationship('OrdenCompraItem', backref='orden_compra', lazy=True, cascade='all, delete-orphan')
    proveedor = db.relationship('Proveedor', backref='ordenes_compra')

    def to_dict(self):
        from datetime import date, datetime as dt
        estado = self.estado
        fecha_entrega = self.fecha_entrega
        # Asegúrate de que fecha_entrega es un datetime antes de llamar a .date()
        if estado == "pendiente" and fecha_entrega:
            # Si es string, intenta convertirlo
            if isinstance(fecha_entrega, str):
                try:
                    fecha_entrega = dt.fromisoformat(fecha_entrega)
                except Exception:
                    fecha_entrega = None
            if fecha_entrega and fecha_entrega.date() < date.today():
                estado = "vencida"
        return {
            'id': self.id,
            'proveedor_id': self.proveedor_id,
            'proveedor': self.proveedor.nombre if self.proveedor else None,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_entrega': self.fecha_entrega.isoformat() if self.fecha_entrega else None,
            'estado': estado,
            'total': float(self.total),
            'items': [item.to_dict() for item in self.items]
        }

class OrdenCompraItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    orden_compra_id = db.Column(db.Integer, db.ForeignKey('orden_compra.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    producto = db.relationship('Producto')

    def to_dict(self):
        return {
            'id': self.id,
            'orden_compra_id': self.orden_compra_id,
            'producto_id': self.producto_id,
            'producto': self.producto.nombre if self.producto else None,
            'cantidad': self.cantidad,
            'precio_unitario': float(self.precio_unitario),
            'subtotal': float(self.subtotal)
        }

class MovimientoInventario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(20))  # 'venta', 'uso', 'ajuste_manual', etc.
    cantidad = db.Column(db.Integer, nullable=False)
    usuario = db.Column(db.String(100))  # Opcional, si tienes usuarios
    producto = db.relationship('Producto')

    def to_dict(self):
        return {
            'fecha': self.fecha.strftime('%Y-%m-%d'),
            'producto': self.producto.nombre if self.producto else None,
            'tipo': self.tipo,
            'cantidad': self.cantidad,
            'usuario': self.usuario or ''
        }

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'rol': self.rol
        }

# Schemas de validación
class ProductoSchema(Schema):
    nombre = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    sku = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    precio_costo = fields.Decimal(required=True, validate=validate.Range(min=0))
    precio_venta = fields.Decimal(required=True, validate=validate.Range(min=0))
    descripcion = fields.Str(allow_none=True)
    cantidad = fields.Int(validate=validate.Range(min=0))
    umbral_reorden = fields.Int(validate=validate.Range(min=0))
    categoria_id = fields.Int(allow_none=True)

class OrdenCompraSchema(Schema):
    proveedor_id = fields.Int(required=True)
    fecha_entrega = fields.DateTime(allow_none=True)
    estado = fields.Str(validate=validate.OneOf(['pendiente', 'completada', 'cancelada']))
    items = fields.List(fields.Dict(), required=True, validate=validate.Length(min=1))

class MovimientoSchema(Schema):
    producto_id = fields.Int(required=True)
    tipo = fields.Str(required=True, validate=validate.OneOf(['venta', 'uso', 'ajuste_manual']))
    cantidad = fields.Int(required=True)
    usuario = fields.Str(allow_none=True)

# Instancias de schemas
producto_schema = ProductoSchema()
orden_compra_schema = OrdenCompraSchema()
movimiento_schema = MovimientoSchema()

def require_jwt(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Token JWT requerido'}), 401
            token = auth_header.split(' ')[1]
            try:
                payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token expirado'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Token inválido'}), 401
            if role and payload.get('rol') != role:
                return jsonify({'error': 'Permisos insuficientes'}), 403
            request.user = payload
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Endpoints de Categorías
@app.route('/api/categorias', methods=['GET'])
def obtener_categorias():
    categorias = Categoria.query.all()
    return jsonify([c.to_dict() for c in categorias])

@app.route('/api/categorias/<int:id>', methods=['GET'])
def obtener_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    return jsonify(categoria.to_dict())

@app.route('/api/categorias', methods=['POST'])
@require_jwt('admin')
def crear_categoria():
    data = request.json
    nueva = Categoria(nombre_categoria=data['nombre_categoria'])
    db.session.add(nueva)
    db.session.commit()
    return jsonify(nueva.to_dict()), 201

@app.route('/api/categorias/<int:id>', methods=['PUT'])
@require_jwt('admin')
def actualizar_categoria(id):
    data = request.json
    categoria = Categoria.query.get_or_404(id)
    categoria.nombre_categoria = data['nombre_categoria']
    db.session.commit()
    return jsonify(categoria.to_dict())

@app.route('/api/categorias/<int:id>', methods=['DELETE'])
@require_jwt('admin')
def eliminar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    db.session.delete(categoria)
    db.session.commit()
    return '', 204

# Endpoints de Productos
@app.route('/api/productos', methods=['GET'])
def obtener_productos():
    logger.info("Obteniendo lista de productos", extra={
        'type': 'product_list',
        'method': 'GET'
    })
    try:
        productos = Producto.query.all()
        logger.debug(f"Productos encontrados: {len(productos)}", extra={
            'type': 'product_list',
            'count': len(productos)
        })
        return jsonify([p.to_dict() for p in productos])
    except Exception as e:
        logger.error(f"Error al obtener productos: {str(e)}", extra={
            'type': 'server_error',
            'error': str(e)
        })
        return jsonify({"error": "Error al obtener productos"}), 500

@app.route('/api/productos/<int:id>', methods=['GET'])
def obtener_producto(id):
    logger.info(f"Obteniendo producto con ID: {id}", extra={
        'type': 'product_get',
        'method': 'GET',
        'product_id': id
    })
    try:
        producto = Producto.query.get_or_404(id)
        logger.debug(f"Producto encontrado: {producto.to_dict()}", extra={
            'type': 'product_get',
            'product_id': id,
            'data': producto.to_dict()
        })
        return jsonify(producto.to_dict())
    except Exception as e:
        logger.error(f"Error al obtener producto {id}: {str(e)}", extra={
            'type': 'server_error',
            'error': str(e),
            'product_id': id
        })
        return jsonify({"error": "Error al obtener producto"}), 500

@app.route('/api/productos', methods=['POST'])
def crear_producto():
    logger.info("Iniciando creación de producto", extra={
        'type': 'product_creation',
        'method': 'POST'
    })
    try:
        data = request.get_json()
        logger.debug(f"Datos recibidos: {data}", extra={
            'type': 'product_data',
            'data': data
        })
        
        # Validar datos requeridos
        required_fields = ['nombre', 'sku', 'precio_costo', 'precio_venta']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            error_msg = f"Campos requeridos faltantes: {', '.join(missing_fields)}"
            logger.warning(error_msg, extra={
                'type': 'validation_error',
                'missing_fields': missing_fields,
                'data': data
            })
            return jsonify({"error": error_msg}), 400
        
        # Validar tipos de datos
        try:
            precio_costo = float(data['precio_costo'])
            precio_venta = float(data['precio_venta'])
            cantidad = int(data.get('cantidad', 0))
            umbral_reorden = int(data.get('umbral_reorden', 10))
            categoria_id = int(data['categoria_id']) if data.get('categoria_id') else None
        except ValueError as e:
            logger.warning(f"Error en tipos de datos: {str(e)}", extra={
                'type': 'validation_error',
                'error': str(e),
                'data': data
            })
            return jsonify({"error": f"Error en tipos de datos: {str(e)}"}), 400
        
        # Crear nuevo producto
        nuevo_producto = Producto(
            nombre=data['nombre'],
            sku=data['sku'],
            precio_costo=precio_costo,
            precio_venta=precio_venta,
            descripcion=data.get('descripcion', ''),
            cantidad=cantidad,
            umbral_reorden=umbral_reorden,
            categoria_id=categoria_id
        )
        
        db.session.add(nuevo_producto)
        db.session.commit()
        
        logger.info(f"Producto creado exitosamente: {nuevo_producto.to_dict()}", extra={
            'type': 'product_created',
            'product_id': nuevo_producto.id,
            'data': nuevo_producto.to_dict()
        })
        return jsonify(nuevo_producto.to_dict()), 201
        
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}", extra={
            'type': 'validation_error',
            'error': str(e),
            'data': data
        })
        return jsonify({"error": f"Error de validación: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error al crear producto: {str(e)}", extra={
            'type': 'server_error',
            'error': str(e),
            'data': data
        })
        db.session.rollback()
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@app.route('/api/productos/<int:id>', methods=['PUT'])
@require_jwt('admin')
def actualizar_producto(id):
    logger.info(f"Actualizando producto con ID: {id}", extra={
        'type': 'product_update',
        'method': 'PUT',
        'product_id': id
    })
    try:
        data = request.get_json()
        logger.debug(f"Datos recibidos para actualización: {data}", extra={
            'type': 'product_update',
            'product_id': id,
            'data': data
        })
        
        producto = Producto.query.get_or_404(id)
        
        # Validar datos
        try:
            producto.nombre = data['nombre']
            producto.sku = data['sku']
            producto.precio_costo = float(data['precio_costo'])
            producto.precio_venta = float(data['precio_venta'])
            producto.descripcion = data.get('descripcion', '')
            producto.cantidad = int(data.get('cantidad', 0))
            producto.umbral_reorden = int(data.get('umbral_reorden', 10))
            producto.categoria_id = int(data['categoria_id']) if data.get('categoria_id') else None
        except (ValueError, KeyError) as e:
            logger.warning(f"Error de validación al actualizar producto {id}: {str(e)}", extra={
                'type': 'validation_error',
                'error': str(e),
                'product_id': id,
                'data': data
            })
            return jsonify({"error": f"Error de validación: {str(e)}"}), 400
        
        db.session.commit()
        logger.info(f"Producto {id} actualizado exitosamente", extra={
            'type': 'product_updated',
            'product_id': id,
            'data': producto.to_dict()
        })
        return jsonify(producto.to_dict())
    except Exception as e:
        logger.error(f"Error al actualizar producto {id}: {str(e)}", extra={
            'type': 'server_error',
            'error': str(e),
            'product_id': id
        })
        db.session.rollback()
        return jsonify({"error": "Error al actualizar producto"}), 500

@app.route('/api/productos/<int:id>', methods=['DELETE'])
@require_jwt('admin')
def eliminar_producto(id):
    logger.info(f"Eliminando producto con ID: {id}", extra={
        'type': 'product_delete',
        'method': 'DELETE',
        'product_id': id
    })
    try:
        producto = Producto.query.get_or_404(id)
        db.session.delete(producto)
        db.session.commit()
        logger.info(f"Producto {id} eliminado exitosamente", extra={
            'type': 'product_deleted',
            'product_id': id
        })
        return '', 204
    except Exception as e:
        logger.error(f"Error al eliminar producto {id}: {str(e)}", extra={
            'type': 'server_error',
            'error': str(e),
            'product_id': id
        })
        db.session.rollback()
        return jsonify({"error": "Error al eliminar producto"}), 500

# Endpoints de Proveedores
@app.route('/api/proveedores', methods=['GET'])
def obtener_proveedores():
    proveedores = Proveedor.query.all()
    return jsonify([p.to_dict() for p in proveedores])

@app.route('/api/proveedores/<int:id>', methods=['GET'])
def obtener_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    return jsonify(proveedor.to_dict())

@app.route('/api/proveedores', methods=['POST'])
@require_jwt('admin')
def crear_proveedor():
    data = request.json
    nuevo = Proveedor(
        nombre=data['nombre'],
        email=data.get('email'),
        telefono=data.get('telefono')
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify(nuevo.to_dict()), 201

@app.route('/api/proveedores/<int:id>', methods=['PUT'])
@require_jwt('admin')
def actualizar_proveedor(id):
    data = request.json
    proveedor = Proveedor.query.get_or_404(id)
    proveedor.nombre = data['nombre']
    proveedor.email = data.get('email')
    proveedor.telefono = data.get('telefono')
    db.session.commit()
    return jsonify(proveedor.to_dict())

@app.route('/api/proveedores/<int:id>', methods=['DELETE'])
@require_jwt('admin')
def eliminar_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    db.session.delete(proveedor)
    db.session.commit()
    return '', 204

# Endpoints de Órdenes de Compra
@app.route('/api/ordenes-compra', methods=['GET'])
def obtener_ordenes_compra():
    ordenes = OrdenCompra.query.all()
    return jsonify([o.to_dict() for o in ordenes])

@app.route('/api/ordenes-compra/<int:id>', methods=['GET'])
def obtener_orden_compra(id):
    orden = OrdenCompra.query.get_or_404(id)
    return jsonify(orden.to_dict())

@app.route('/api/ordenes-compra', methods=['POST'])
@require_jwt('admin')
def crear_orden_compra():
    try:
        data = request.json
        # Validar datos
        errors = orden_compra_schema.validate(data)
        if errors:
            return jsonify({"error": "Datos inválidos", "detalles": errors}), 400
            
        logger.info(f"Creando nueva orden de compra para proveedor: {data['proveedor_id']}")
        
        with db.session.begin_nested():
            nueva_orden = OrdenCompra(
                proveedor_id=data['proveedor_id'],
                fecha_entrega=datetime.fromisoformat(data['fecha_entrega']) if data.get('fecha_entrega') else None,
                estado=data.get('estado', 'pendiente')
            )
            
            total = 0
            for item_data in data['items']:
                producto = Producto.query.get_or_404(item_data['producto_id'])
                subtotal = item_data['cantidad'] * item_data['precio_unitario']
                item = OrdenCompraItem(
                    producto_id=producto.id,
                    cantidad=item_data['cantidad'],
                    precio_unitario=item_data['precio_unitario'],
                    subtotal=subtotal
                )
                nueva_orden.items.append(item)
                total += subtotal
            
            nueva_orden.total = total
            db.session.add(nueva_orden)
            
        db.session.commit()
        logger.info(f"Orden de compra creada exitosamente: {nueva_orden.id}")
        return jsonify(nueva_orden.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al crear orden de compra: {str(e)}")
        print("ERROR REAL:", str(e))  # <-- AGREGA ESTO TEMPORALMENTE
        return jsonify({"error": "Error al crear la orden de compra"}), 500

@app.route('/api/ordenes-compra/<int:id>', methods=['PUT'])
@require_jwt('admin')
def actualizar_orden_compra(id):
    data = request.json
    orden = OrdenCompra.query.get_or_404(id)

    # Si solo se envía 'estado' (o si solo se quiere actualizar el estado)
    if 'estado' in data and len(data.keys()) == 1:
        orden.estado = data['estado']
        db.session.commit()
        return jsonify(orden.to_dict())

    # Si se envían más campos, realiza la actualización completa
    if 'proveedor_id' in data:
        orden.proveedor_id = data['proveedor_id']
    if 'fecha_entrega' in data:
        orden.fecha_entrega = datetime.fromisoformat(data['fecha_entrega']) if data.get('fecha_entrega') else None
    if 'estado' in data:
        orden.estado = data['estado']

    # Si se envían items, actualiza los items
    if 'items' in data:
        # Eliminar items existentes
        for item in orden.items:
            db.session.delete(item)
        # Agregar nuevos items
        total = 0
        for item_data in data['items']:
            producto = Producto.query.get_or_404(item_data['producto_id'])
            subtotal = item_data['cantidad'] * item_data['precio_unitario']
            item = OrdenCompraItem(
                orden_compra_id=orden.id,
                producto_id=producto.id,
                cantidad=item_data['cantidad'],
                precio_unitario=item_data['precio_unitario'],
                subtotal=subtotal
            )
            orden.items.append(item)
            total += subtotal
        orden.total = total

    db.session.commit()
    return jsonify(orden.to_dict())

@app.route('/api/ordenes-compra/<int:id>', methods=['DELETE'])
@require_jwt('admin')
def eliminar_orden_compra(id):
    orden = OrdenCompra.query.get_or_404(id)
    db.session.delete(orden)
    db.session.commit()
    return '', 204

@app.route('/api/reportes/movimientos')
def obtener_movimientos():
    from datetime import datetime
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        query = MovimientoInventario.query

        if fecha_inicio:
            query = query.filter(MovimientoInventario.fecha >= datetime.fromisoformat(fecha_inicio))
        if fecha_fin:
            query = query.filter(MovimientoInventario.fecha <= datetime.fromisoformat(fecha_fin))

        movimientos = query.order_by(MovimientoInventario.fecha.desc()).all()
        return jsonify([m.to_dict() for m in movimientos])
    except Exception as e:
        print("ERROR REAL EN REPORTE:", str(e))
        return jsonify({"error": "Error al obtener movimientos"}), 500

@app.route('/api/movimientos', methods=['POST'])
def registrar_movimiento():
    try:
        data = request.json
        producto = Producto.query.get_or_404(data['producto_id'])
        tipo = data['tipo']
        cantidad = int(data['cantidad'])
        usuario = data.get('usuario', 'admin')

        if tipo == 'entrada':
            producto.cantidad += cantidad
        elif tipo in ['venta', 'salida', 'uso']:
            if producto.cantidad < cantidad:
                return jsonify({"error": "Stock insuficiente"}), 400
            producto.cantidad -= cantidad
        else:
            return jsonify({"error": "Tipo de movimiento no válido"}), 400

        movimiento = MovimientoInventario(
            producto_id=producto.id,
            tipo=tipo,
            cantidad=cantidad,
            usuario=usuario
        )
        db.session.add(movimiento)
        db.session.commit()
        return jsonify(movimiento.to_dict()), 201

    except Exception as e:
        print("ERROR REAL EN MOVIMIENTO:", str(e))
        db.session.rollback()
        return jsonify({"error": "Error al registrar movimiento"}), 500

# Utilidad para crear JWT
def create_jwt(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'rol': user.rol,
        'exp': datetime.utcnow() + timedelta(hours=8)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

# Endpoint de login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Usuario y contraseña requeridos'}), 400
    user = Usuario.query.filter_by(username=username).first()
    if not user or not user.verify_password(password):
        return jsonify({'error': 'Credenciales inválidas'}), 401
    token = create_jwt(user)
    return jsonify({'token': token, 'user': user.to_dict()})

if __name__ == '__main__':
    logger.info("Iniciando aplicación")
    app.run(host='0.0.0.0', port=5000, debug=False)