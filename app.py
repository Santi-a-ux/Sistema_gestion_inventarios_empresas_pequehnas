from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventario.db'
db = SQLAlchemy(app)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    cantidad = db.Column(db.Integer, default=0)
    umbral_reorden = db.Column(db.Integer, default=5)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'cantidad': self.cantidad,
            'umbral_reorden': self.umbral_reorden,
            'fecha_creacion': self.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_actualizacion': self.fecha_actualizacion.strftime('%Y-%m-%d %H:%M:%S')
        }

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    productos = Producto.query.all()
    return render_template('inventario.html', productos=productos)

@app.route('/productos/nuevo', methods=['GET', 'POST'])
def nuevo_producto():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        cantidad = int(request.form.get('cantidad', 0))
        umbral_reorden = int(request.form.get('umbral_reorden', 5))

        if not nombre:
            flash('El nombre del producto es requerido', 'error')
            return redirect(url_for('nuevo_producto'))

        producto = Producto(
            nombre=nombre,
            descripcion=descripcion,
            cantidad=cantidad,
            umbral_reorden=umbral_reorden
        )

        db.session.add(producto)
        db.session.commit()
        flash('Producto agregado exitosamente', 'success')
        return redirect(url_for('index'))

    return render_template('agregar_producto.html')

@app.route('/productos/<int:id>/editar', methods=['GET', 'POST'])
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    
    if request.method == 'POST':
        producto.nombre = request.form.get('nombre')
        producto.descripcion = request.form.get('descripcion')
        producto.cantidad = int(request.form.get('cantidad', 0))
        producto.umbral_reorden = int(request.form.get('umbral_reorden', 5))
        
        db.session.commit()
        flash('Producto actualizado exitosamente', 'success')
        return redirect(url_for('index'))
    
    return render_template('editar_producto.html', producto=producto)

@app.route('/productos/<int:id>/eliminar', methods=['POST'])
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    flash('Producto eliminado exitosamente', 'success')
    return redirect(url_for('index'))

@app.route('/productos/<int:id>/salida', methods=['POST'])
def registrar_salida(id):
    producto = Producto.query.get_or_404(id)
    
    if producto.cantidad > 0:
        producto.cantidad -= 1
        db.session.commit()
        flash(f'Salida registrada. Quedan {producto.cantidad} unidades de {producto.nombre}', 'success')
    else:
        flash('No hay unidades disponibles para sacar', 'error')
    
    return redirect(url_for('index'))

@app.route('/productos/reordenar')
def productos_reordenar():
    productos = Producto.query.filter(Producto.cantidad <= Producto.umbral_reorden).all()
    return render_template('reordenar.html', productos=productos)

if __name__ == '__main__':
    app.run(debug=True) 