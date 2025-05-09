from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import time
from sqlalchemy.exc import OperationalError
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuración de la base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/inventario')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')  # Change in production!
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Modelos
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    rol = db.Column(db.String(20), default='usuario')  # 'admin' o 'usuario'
    movimientos = db.relationship('MovimientoStock', backref='usuario', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'rol': self.rol
        }

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
    movimientos = db.relationship('MovimientoStock', backref='producto', lazy=True)
    items_orden_compra = db.relationship('ItemsOrdenCompra', backref='producto', lazy=True)

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

class MovimientoStock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad_cambio = db.Column(db.Integer, nullable=False)  # Positivo para entradas, negativo para salidas
    nueva_cantidad_stock = db.Column(db.Integer, nullable=False)
    tipo_movimiento = db.Column(db.String(20), nullable=False)  # 'compra', 'venta', 'ajuste_manual', 'inicial'
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    referencia_id = db.Column(db.Integer, nullable=True)  # ID de orden de compra, venta, etc.
    notas_adicionales = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'producto_id': self.producto_id,
            'cantidad_cambio': self.cantidad_cambio,
            'nueva_cantidad_stock': self.nueva_cantidad_stock,
            'tipo_movimiento': self.tipo_movimiento,
            'fecha_hora': self.fecha_hora.isoformat(),
            'usuario_id': self.usuario_id,
            'referencia_id': self.referencia_id,
            'notas_adicionales': self.notas_adicionales
        }

class Proveedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_proveedor = db.Column(db.String(100), nullable=False)
    contacto_email = db.Column(db.String(120))
    contacto_telefono = db.Column(db.String(20))
    ordenes_compra = db.relationship('OrdenCompra', backref='proveedor', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre_proveedor': self.nombre_proveedor,
            'contacto_email': self.contacto_email,
            'contacto_telefono': self.contacto_telefono
        }

class OrdenCompra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_esperada_entrega = db.Column(db.DateTime)
    estado = db.Column(db.String(20), default='pendiente')  # 'pendiente', 'parcialmente_recibida', 'recibida_completa'
    items = db.relationship('ItemsOrdenCompra', backref='orden_compra', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'proveedor_id': self.proveedor_id,
            'proveedor': self.proveedor.nombre_proveedor if self.proveedor else None,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_esperada_entrega': self.fecha_esperada_entrega.isoformat() if self.fecha_esperada_entrega else None,
            'estado': self.estado,
            'items': [item.to_dict() for item in self.items]
        }

class ItemsOrdenCompra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    orden_compra_id = db.Column(db.Integer, db.ForeignKey('orden_compra.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad_pedida = db.Column(db.Integer, nullable=False)
    cantidad_recibida = db.Column(db.Integer, default=0)
    precio_costo_unitario = db.Column(db.Numeric(10, 2), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'orden_compra_id': self.orden_compra_id,
            'producto_id': self.producto_id,
            'producto': self.producto.nombre if self.producto else None,
            'cantidad_pedida': self.cantidad_pedida,
            'cantidad_recibida': self.cantidad_recibida,
            'precio_costo_unitario': float(self.precio_costo_unitario)
        }

# Decorador para requerir autenticación
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token no proporcionado'}), 401
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = Usuario.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'Usuario no encontrado'}), 401
        except:
            return jsonify({'error': 'Token inválido'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Decorador para requerir rol admin
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token no proporcionado'}), 401
        try:
            token = token.split(' ')[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = Usuario.query.get(data['user_id'])
            if not current_user or current_user.rol != 'admin':
                return jsonify({'error': 'Se requiere rol de administrador'}), 403
        except:
            return jsonify({'error': 'Token inválido'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

def init_db():
    max_retries = 5
    retry_delay = 5  # segundos
    
    for attempt in range(max_retries):
        try:
            with app.app_context():
                db.create_all()
            print(f"Base de datos inicializada correctamente usando {DATABASE_URL}")
            return True
        except OperationalError as e:
            if attempt < max_retries - 1:
                print(f"Error al conectar con la base de datos (intento {attempt + 1}/{max_retries}). Reintentando en {retry_delay} segundos...")
                print(f"Error detallado: {str(e)}")
                time.sleep(retry_delay)
            else:
                print(f"No se pudo conectar con la base de datos después de {max_retries} intentos")
                print(f"Error final: {str(e)}")
                raise e

# Inicializar la base de datos
init_db()

# API Routes
@app.route('/categorias', methods=['GET'])
def obtener_categorias():
    categorias = Categoria.query.all()
    return jsonify([categoria.to_dict() for categoria in categorias])

@app.route('/categorias', methods=['POST'])
def crear_categoria():
    datos = request.get_json()
    if not datos or 'nombre_categoria' not in datos:
        return jsonify({'error': 'Se requiere el nombre de la categoría'}), 400
    
    categoria = Categoria(nombre_categoria=datos['nombre_categoria'])
    db.session.add(categoria)
    db.session.commit()
    return jsonify(categoria.to_dict()), 201

@app.route('/productos', methods=['GET', 'POST'])
def productos():
    if request.method == 'GET':
        productos = Producto.query.all()
        return jsonify([producto.to_dict() for producto in productos])
    
    elif request.method == 'POST':
        datos = request.get_json()
        if not datos or 'nombre' not in datos or 'sku' not in datos:
            return jsonify({'error': 'Se requiere el nombre y SKU del producto'}), 400
        
        producto = Producto(
            nombre=datos['nombre'],
            sku=datos['sku'],
            precio_costo=datos.get('precio_costo', 0),
            precio_venta=datos.get('precio_venta', 0),
            descripcion=datos.get('descripcion', ''),
            cantidad=datos.get('cantidad', 0),
            umbral_reorden=datos.get('umbral_reorden', 10),
            categoria_id=datos.get('categoria_id')
        )
        
        db.session.add(producto)
        db.session.commit()
        return jsonify(producto.to_dict()), 201

@app.route('/productos/<int:id>', methods=['GET'])
def obtener_producto(id):
    producto = Producto.query.get_or_404(id)
    return jsonify(producto.to_dict())

@app.route('/productos/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    producto = Producto.query.get_or_404(id)
    datos = request.get_json()
    
    if 'nombre' in datos:
        producto.nombre = datos['nombre']
    if 'sku' in datos:
        producto.sku = datos['sku']
    if 'precio_costo' in datos:
        producto.precio_costo = datos['precio_costo']
    if 'precio_venta' in datos:
        producto.precio_venta = datos['precio_venta']
    if 'descripcion' in datos:
        producto.descripcion = datos['descripcion']
    if 'cantidad' in datos:
        producto.cantidad = datos['cantidad']
    if 'umbral_reorden' in datos:
        producto.umbral_reorden = datos['umbral_reorden']
    if 'categoria_id' in datos:
        producto.categoria_id = datos['categoria_id']
    
    db.session.commit()
    return jsonify(producto.to_dict())

@app.route('/productos/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    return '', 204

@app.route('/productos/<int:id>/salida', methods=['POST'])
def registrar_salida(id):
    producto = Producto.query.get_or_404(id)
    datos = request.get_json()
    
    if not datos or 'cantidad' not in datos:
        return jsonify({'error': 'Se requiere la cantidad'}), 400
    
    cantidad = datos['cantidad']
    if cantidad > producto.cantidad:
        return jsonify({'error': 'No hay suficiente stock'}), 400
    
    producto.cantidad -= cantidad
    db.session.commit()
    return jsonify(producto.to_dict())

@app.route('/productos/reordenar', methods=['GET'])
def productos_reordenar():
    productos = Producto.query.filter(Producto.cantidad <= Producto.umbral_reorden).all()
    return jsonify([producto.to_dict() for producto in productos])

# Authentication routes
@app.route('/auth/login', methods=['POST'])
def login():
    datos = request.get_json()
    if not datos or 'username' not in datos or 'password' not in datos:
        return jsonify({'error': 'Se requiere username y password'}), 400
    
    usuario = Usuario.query.filter_by(username=datos['username']).first()
    if not usuario or not usuario.check_password(datos['password']):
        return jsonify({'error': 'Credenciales inválidas'}), 401
    
    token = jwt.encode({
        'user_id': usuario.id,
        'rol': usuario.rol,
        'exp': datetime.utcnow() + timedelta(days=1)
    }, app.config['SECRET_KEY'])
    
    return jsonify({
        'token': token,
        'usuario': usuario.to_dict()
    })

@app.route('/auth/register', methods=['POST'])
@token_required
def register(current_user):
    if current_user.rol != 'admin':
        return jsonify({'error': 'Solo los administradores pueden registrar usuarios'}), 403
    
    datos = request.get_json()
    if not datos or 'username' not in datos or 'password' not in datos:
        return jsonify({'error': 'Se requiere username y password'}), 400
    
    if Usuario.query.filter_by(username=datos['username']).first():
        return jsonify({'error': 'El username ya existe'}), 400
    
    usuario = Usuario(
        username=datos['username'],
        rol=datos.get('rol', 'usuario')
    )
    usuario.set_password(datos['password'])
    
    db.session.add(usuario)
    db.session.commit()
    
    return jsonify(usuario.to_dict()), 201

# New routes for stock movements
@app.route('/productos/<int:id>/ajustar_stock', methods=['POST'])
@token_required
def ajustar_stock(current_user, id):
    producto = Producto.query.get_or_404(id)
    datos = request.get_json()
    
    if not datos or 'cantidad' not in datos or 'tipo_movimiento' not in datos:
        return jsonify({'error': 'Se requiere cantidad y tipo de movimiento'}), 400
    
    cantidad = datos['cantidad']
    tipo_movimiento = datos['tipo_movimiento']
    notas = datos.get('notas_adicionales', '')
    
    # Crear el movimiento
    movimiento = MovimientoStock(
        producto_id=producto.id,
        cantidad_cambio=cantidad,
        nueva_cantidad_stock=producto.cantidad + cantidad,
        tipo_movimiento=tipo_movimiento,
        usuario_id=current_user.id,
        notas_adicionales=notas
    )
    
    # Actualizar la cantidad del producto
    producto.cantidad += cantidad
    
    db.session.add(movimiento)
    db.session.commit()
    
    return jsonify({
        'producto': producto.to_dict(),
        'movimiento': movimiento.to_dict()
    })

@app.route('/productos/<int:id>/historial_movimientos', methods=['GET'])
@token_required
def historial_movimientos(current_user, id):
    movimientos = MovimientoStock.query.filter_by(producto_id=id).order_by(MovimientoStock.fecha_hora.desc()).all()
    return jsonify([mov.to_dict() for mov in movimientos])

# Routes for suppliers
@app.route('/proveedores', methods=['GET'])
@token_required
def obtener_proveedores(current_user):
    proveedores = Proveedor.query.all()
    return jsonify([p.to_dict() for p in proveedores])

@app.route('/proveedores', methods=['POST'])
@admin_required
def crear_proveedor(current_user):
    datos = request.get_json()
    if not datos or 'nombre_proveedor' not in datos:
        return jsonify({'error': 'Se requiere el nombre del proveedor'}), 400
    
    proveedor = Proveedor(
        nombre_proveedor=datos['nombre_proveedor'],
        contacto_email=datos.get('contacto_email'),
        contacto_telefono=datos.get('contacto_telefono')
    )
    
    db.session.add(proveedor)
    db.session.commit()
    
    return jsonify(proveedor.to_dict()), 201

# Routes for purchase orders
@app.route('/ordenes_compra', methods=['GET'])
@token_required
def obtener_ordenes_compra(current_user):
    ordenes = OrdenCompra.query.all()
    return jsonify([o.to_dict() for o in ordenes])

@app.route('/ordenes_compra', methods=['POST'])
@admin_required
def crear_orden_compra(current_user):
    datos = request.get_json()
    if not datos or 'proveedor_id' not in datos or 'items' not in datos:
        return jsonify({'error': 'Se requiere proveedor_id y items'}), 400
    
    orden = OrdenCompra(
        proveedor_id=datos['proveedor_id'],
        fecha_esperada_entrega=datetime.fromisoformat(datos['fecha_esperada_entrega']) if 'fecha_esperada_entrega' in datos else None
    )
    
    for item_data in datos['items']:
        item = ItemsOrdenCompra(
            producto_id=item_data['producto_id'],
            cantidad_pedida=item_data['cantidad_pedida'],
            precio_costo_unitario=item_data['precio_costo_unitario']
        )
        orden.items.append(item)
    
    db.session.add(orden)
    db.session.commit()
    
    return jsonify(orden.to_dict()), 201

@app.route('/ordenes_compra/<int:id>/recibir_items', methods=['POST'])
@admin_required
def recibir_items_orden_compra(current_user, id):
    orden = OrdenCompra.query.get_or_404(id)
    datos = request.get_json()
    
    if not datos or 'items' not in datos:
        return jsonify({'error': 'Se requiere la lista de items recibidos'}), 400
    
    for item_data in datos['items']:
        item = next((i for i in orden.items if i.id == item_data['item_id']), None)
        if not item:
            continue
        
        cantidad_recibida = item_data['cantidad_recibida']
        item.cantidad_recibida += cantidad_recibida
        
        # Crear movimiento de stock
        movimiento = MovimientoStock(
            producto_id=item.producto_id,
            cantidad_cambio=cantidad_recibida,
            nueva_cantidad_stock=item.producto.cantidad + cantidad_recibida,
            tipo_movimiento='compra',
            usuario_id=current_user.id,
            referencia_id=orden.id,
            notas_adicionales=f'Recepción de orden de compra #{orden.id}'
        )
        
        # Actualizar stock del producto
        item.producto.cantidad += cantidad_recibida
        
        db.session.add(movimiento)
    
    # Actualizar estado de la orden
    total_items = len(orden.items)
    items_completos = sum(1 for item in orden.items if item.cantidad_recibida >= item.cantidad_pedida)
    
    if items_completos == 0:
        orden.estado = 'pendiente'
    elif items_completos == total_items:
        orden.estado = 'recibida_completa'
    else:
        orden.estado = 'parcialmente_recibida'
    
    db.session.commit()
    
    return jsonify(orden.to_dict())

# Report routes
@app.route('/reportes/inventario_actual_valorado', methods=['GET'])
@token_required
def reporte_inventario_valorado(current_user):
    productos = Producto.query.all()
    total_valor = 0
    resultado = []
    
    for producto in productos:
        valor_producto = float(producto.cantidad * producto.precio_costo)
        total_valor += valor_producto
        
        resultado.append({
            'producto': producto.to_dict(),
            'valor_total': valor_producto
        })
    
    return jsonify({
        'productos': resultado,
        'valor_total_inventario': total_valor
    })

@app.route('/reportes/ventas_uso', methods=['GET'])
@token_required
def reporte_ventas_uso(current_user):
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    
    query = MovimientoStock.query.filter(
        MovimientoStock.tipo_movimiento.in_(['venta', 'uso'])
    )
    
    if fecha_inicio:
        query = query.filter(MovimientoStock.fecha_hora >= datetime.fromisoformat(fecha_inicio))
    if fecha_fin:
        query = query.filter(MovimientoStock.fecha_hora <= datetime.fromisoformat(fecha_fin))
    
    movimientos = query.order_by(MovimientoStock.fecha_hora.desc()).all()
    
    return jsonify([mov.to_dict() for mov in movimientos])

# Search and filter routes
@app.route('/productos/buscar', methods=['GET'])
@token_required
def buscar_productos(current_user):
    query = Producto.query
    
    # Filtros
    nombre = request.args.get('nombre')
    sku = request.args.get('sku')
    categoria_id = request.args.get('categoria_id')
    
    if nombre:
        query = query.filter(Producto.nombre.ilike(f'%{nombre}%'))
    if sku:
        query = query.filter(Producto.sku.ilike(f'%{sku}%'))
    if categoria_id:
        query = query.filter(Producto.categoria_id == categoria_id)
    
    productos = query.all()
    return jsonify([p.to_dict() for p in productos])

# CSV import/export routes
@app.route('/productos/importar_csv', methods=['POST'])
@admin_required
def importar_csv(current_user):
    if 'file' not in request.files:
        return jsonify({'error': 'No se proporcionó archivo'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'El archivo debe ser CSV'}), 400
    
    # Implementar lógica de importación CSV
    # Por ahora solo un placeholder
    return jsonify({'message': 'Importación CSV no implementada aún'}), 501

@app.route('/productos/exportar_csv', methods=['GET'])
@token_required
def exportar_csv(current_user):
    productos = Producto.query.all()
    # Implementar lógica de exportación CSV
    # Por ahora solo un placeholder
    return jsonify({'message': 'Exportación CSV no implementada aún'}), 501

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True) 