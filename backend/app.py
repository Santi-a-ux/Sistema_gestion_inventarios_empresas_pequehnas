from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from elasticsearch import Elasticsearch
import requests
import json

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/inventario')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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

class ElasticsearchHandler(logging.Handler):
    def __init__(self, hosts):
        logging.Handler.__init__(self)
        self.es_url = hosts[0] if isinstance(hosts, list) else hosts

    def emit(self, record):
        log_entry = self.format(record)
        try:
            requests.post(f"{self.es_url}/logs/_doc", data=log_entry, headers={"Content-Type": "application/json"})
        except Exception as e:
            print("Error enviando log a Elasticsearch:", e)

# Configura el logger
es_handler = ElasticsearchHandler(['http://elasticsearch:9200'])
es_handler.setFormatter(jsonlogger.JsonFormatter())
logging.getLogger().addHandler(es_handler)
logging.getLogger().setLevel(logging.INFO)

def enviar_a_elasticsearch(indice, documento, pipeline):
    url = f"http://elasticsearch:9200/{indice}/_doc?pipeline={pipeline}"
    try:
        response = requests.post(url, json=documento)
        response.raise_for_status()
    except Exception as e:
        print(f"Error enviando a Elasticsearch: {e}")

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
def crear_categoria():
    data = request.json
    nueva = Categoria(nombre_categoria=data['nombre_categoria'])
    db.session.add(nueva)
    db.session.commit()
    return jsonify(nueva.to_dict()), 201

@app.route('/api/categorias/<int:id>', methods=['PUT'])
def actualizar_categoria(id):
    data = request.json
    categoria = Categoria.query.get_or_404(id)
    categoria.nombre_categoria = data['nombre_categoria']
    db.session.commit()
    return jsonify(categoria.to_dict())

@app.route('/api/categorias/<int:id>', methods=['DELETE'])
def eliminar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    db.session.delete(categoria)
    db.session.commit()
    return '', 204

# Endpoints de Productos
@app.route('/api/productos', methods=['GET'])
def obtener_productos():
    productos = Producto.query.all()
    return jsonify([p.to_dict() for p in productos])

@app.route('/api/productos/<int:id>', methods=['GET'])
def obtener_producto(id):
    producto = Producto.query.get_or_404(id)
    return jsonify(producto.to_dict())

@app.route('/api/productos', methods=['POST'])
def crear_producto():
    data = request.json
    nuevo = Producto(
        nombre=data['nombre'],
        sku=data['sku'],
        precio_costo=data['precio_costo'],
        precio_venta=data['precio_venta'],
        descripcion=data.get('descripcion', ''),
        cantidad=data.get('cantidad', 0),
        umbral_reorden=data.get('umbral_reorden', 10),
        categoria_id=data.get('categoria_id')
    )
    db.session.add(nuevo)
    db.session.commit()
    # Enviar a Elasticsearch
    enviar_a_elasticsearch("productos", nuevo.to_dict(), "Productos")
    app.logger.info("Producto creado", extra={"usuario": "admin", "producto": nuevo.nombre})
    return jsonify(nuevo.to_dict()), 201

@app.route('/api/productos/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    data = request.json
    producto = Producto.query.get_or_404(id)
    producto.nombre = data['nombre']
    producto.sku = data['sku']
    producto.precio_costo = data['precio_costo']
    producto.precio_venta = data['precio_venta']
    producto.descripcion = data.get('descripcion', '')
    producto.cantidad = data.get('cantidad', 0)
    producto.umbral_reorden = data.get('umbral_reorden', 10)
    producto.categoria_id = data.get('categoria_id')
    db.session.commit()
    return jsonify(producto.to_dict())

@app.route('/api/productos/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    return '', 204

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
def crear_proveedor():
    data = request.json
    nuevo = Proveedor(
        nombre=data['nombre'],
        email=data.get('email'),
        telefono=data.get('telefono')
    )
    db.session.add(nuevo)
    db.session.commit()
    # Enviar a Elasticsearch
    enviar_a_elasticsearch("proveedores", nuevo.to_dict(), "Proveedores")
    return jsonify(nuevo.to_dict()), 201

@app.route('/api/proveedores/<int:id>', methods=['PUT'])
def actualizar_proveedor(id):
    data = request.json
    proveedor = Proveedor.query.get_or_404(id)
    proveedor.nombre = data['nombre']
    proveedor.email = data.get('email')
    proveedor.telefono = data.get('telefono')
    db.session.commit()
    return jsonify(proveedor.to_dict())

@app.route('/api/proveedores/<int:id>', methods=['DELETE'])
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
def crear_orden_compra():
    data = request.json
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
    # Enviar a Elasticsearch
    enviar_a_elasticsearch("ordenes", nueva_orden.to_dict(), "Ordenes")
    return jsonify(nueva_orden.to_dict()), 201

@app.route('/api/ordenes-compra/<int:id>', methods=['PUT'])
def actualizar_orden_compra(id):
    data = request.json
    orden = OrdenCompra.query.get_or_404(id)
    
    orden.proveedor_id = data['proveedor_id']
    orden.fecha_entrega = datetime.fromisoformat(data['fecha_entrega']) if data.get('fecha_entrega') else None
    orden.estado = data.get('estado', orden.estado)
    
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
def eliminar_orden_compra(id):
    orden = OrdenCompra.query.get_or_404(id)
    db.session.delete(orden)
    db.session.commit()
    return '', 204

@app.route('/api/reportes/movimientos')
def obtener_movimientos():
    from datetime import datetime
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    query = MovimientoInventario.query

    if fecha_inicio:
        query = query.filter(MovimientoInventario.fecha >= datetime.fromisoformat(fecha_inicio))
    if fecha_fin:
        query = query.filter(MovimientoInventario.fecha <= datetime.fromisoformat(fecha_fin))

    movimientos = query.order_by(MovimientoInventario.fecha.desc()).all()
    return jsonify([m.to_dict() for m in movimientos])

@app.route('/api/movimientos', methods=['POST'])
def registrar_movimiento():
    data = request.json
    producto = Producto.query.get_or_404(data['producto_id'])
    tipo = data['tipo']  # 'venta', 'uso', 'ajuste_manual', etc.
    cantidad = int(data['cantidad'])
    usuario = data.get('usuario', 'admin')

    # Actualiza el stock según el tipo de movimiento
    if tipo in ['venta', 'uso']:
        if producto.cantidad < cantidad:
            return jsonify({'error': 'Stock insuficiente'}), 400
        producto.cantidad -= cantidad
    elif tipo == 'ajuste_manual':
        producto.cantidad += cantidad  # Puede ser positivo o negativo
    else:
        return jsonify({'error': 'Tipo de movimiento no soportado'}), 400

    # Registra el movimiento
    movimiento = MovimientoInventario(
        producto_id=producto.id,
        tipo=tipo,
        cantidad=cantidad,
        usuario=usuario
    )
    db.session.add(movimiento)
    db.session.commit()
    return jsonify(movimiento.to_dict()), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 