from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/inventario')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 