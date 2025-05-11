-- Crear tabla de usuarios
CREATE TABLE IF NOT EXISTS usuario (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL
);

-- Crear tabla de categorías
CREATE TABLE IF NOT EXISTS categoria (
    id SERIAL PRIMARY KEY,
    nombre_categoria VARCHAR(100) NOT NULL
);

-- Crear tabla de productos
CREATE TABLE IF NOT EXISTS producto (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    sku VARCHAR(50),
    precio_costo NUMERIC,
    precio_venta NUMERIC,
    descripcion TEXT,
    cantidad INTEGER,
    umbral_reorden INTEGER,
    categoria_id INTEGER REFERENCES categoria(id),
    fecha_creacion TIMESTAMP,
    fecha_actualizacion TIMESTAMP
);

-- Crear tabla de proveedores
CREATE TABLE IF NOT EXISTS proveedor (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    telefono VARCHAR(20),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de órdenes de compra
CREATE TABLE IF NOT EXISTS orden_compra (
    id SERIAL PRIMARY KEY,
    proveedor_id INTEGER REFERENCES proveedor(id) NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega TIMESTAMP,
    estado VARCHAR(20) DEFAULT 'pendiente',
    total NUMERIC(10, 2) DEFAULT 0
);

-- Crear tabla de items de órdenes de compra
CREATE TABLE IF NOT EXISTS orden_compra_item (
    id SERIAL PRIMARY KEY,
    orden_compra_id INTEGER REFERENCES orden_compra(id) ON DELETE CASCADE NOT NULL,
    producto_id INTEGER REFERENCES producto(id) NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario NUMERIC(10, 2) NOT NULL,
    subtotal NUMERIC(10, 2) NOT NULL
);

-- Insertar usuario admin (password: admin123)
INSERT INTO usuario (username, password_hash, rol) VALUES
('admin', 'scrypt:32768:8:1$garm1vZBJ2jlacjR$64ce010dbf779e6ba449623f1ece804c99898c488b30a791429d0a4dcd4cbc65bd9aa8704cbf7d77640a90a6f18831914a6f963ce2031e8b961295a3e8e1a948', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Insertar categorías de ejemplo
INSERT INTO categoria (nombre_categoria) VALUES
('Electrónica'), ('Ropa'), ('Alimentos')
ON CONFLICT DO NOTHING;

-- Insertar productos de ejemplo
INSERT INTO producto (nombre, sku, precio_costo, precio_venta, descripcion, cantidad, umbral_reorden, categoria_id, fecha_creacion, fecha_actualizacion)
VALUES
('Laptop', 'SKU001', 500, 700, 'Laptop de ejemplo', 10, 2, 1, NOW(), NOW()),
('Camiseta', 'SKU002', 5, 10, 'Camiseta de algodón', 50, 10, 2, NOW(), NOW())
ON CONFLICT DO NOTHING; 