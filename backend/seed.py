from app import db, Categoria, Producto, Proveedor
import logging

def seed_database():
    try:
        # Crear categorías
        categorias = [
            Categoria(nombre_categoria='Electrónicos'),
            Categoria(nombre_categoria='Ropa'),
            Categoria(nombre_categoria='Alimentos'),
            Categoria(nombre_categoria='Hogar')
        ]
        
        for categoria in categorias:
            db.session.add(categoria)
        db.session.commit()
        
        # Crear productos
        productos = [
            Producto(
                nombre='Laptop HP',
                sku='LAP-001',
                precio_costo=800.00,
                precio_venta=1000.00,
                descripcion='Laptop HP 15.6"',
                cantidad=10,
                umbral_reorden=5,
                categoria_id=1
            ),
            Producto(
                nombre='Camisa Polo',
                sku='POL-001',
                precio_costo=20.00,
                precio_venta=35.00,
                descripcion='Camisa Polo talla M',
                cantidad=50,
                umbral_reorden=10,
                categoria_id=2
            )
        ]
        
        for producto in productos:
            db.session.add(producto)
        db.session.commit()
        
        # Crear proveedores
        proveedores = [
            Proveedor(
                nombre='Distribuidora XYZ',
                email='contacto@xyz.com',
                telefono='123-456-7890'
            ),
            Proveedor(
                nombre='Electrónicos ABC',
                email='ventas@abc.com',
                telefono='098-765-4321'
            )
        ]
        
        for proveedor in proveedores:
            db.session.add(proveedor)
        db.session.commit()
        
        logging.info("Datos iniciales creados exitosamente")
        
    except Exception as e:
        logging.error(f"Error al crear datos iniciales: {str(e)}")
        db.session.rollback()
        raise

if __name__ == '__main__':
    seed_database() 