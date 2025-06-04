-- Crear tabla de usuarios
CREATE TABLE IF NOT EXISTS usuario (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL
);

-- Crear tabla de categorías con restricción UNIQUE
CREATE TABLE IF NOT EXISTS categoria (
    id SERIAL PRIMARY KEY,
    nombre_categoria VARCHAR(100) NOT NULL UNIQUE
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

-- Crear tabla de movimientos de inventario
CREATE TABLE IF NOT EXISTS movimiento_inventario (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER REFERENCES producto(id) ON DELETE SET NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo VARCHAR(20) NOT NULL,
    cantidad INTEGER NOT NULL,
    usuario VARCHAR(100)
);

-- Insertar usuario admin (password: admin123)
INSERT INTO usuario (username, password_hash, rol) VALUES
('admin', 'scrypt:32768:8:1$garm1vZBJ2jlacjR$64ce010dbf779e6ba449623f1ece804c99898c488b30a791429d0a4dcd4cbc65bd9aa8704cbf7d77640a90a6f18831914a6f963ce2031e8b961295a3e8e1a948', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Insertar categorías de ejemplo
INSERT INTO categoria (nombre_categoria) VALUES
('Electrónica'), ('Ropa'), ('Alimentos'), ('Hogar'), ('Deportes')
ON CONFLICT (nombre_categoria) DO NOTHING;

-- Insertar productos de ejemplo
INSERT INTO producto (nombre, sku, precio_costo, precio_venta, descripcion, cantidad, umbral_reorden, categoria_id, fecha_creacion, fecha_actualizacion)
VALUES
('Laptop HP', 'SKU001', 500, 700, 'Laptop HP de última generación', 10, 2, 1, NOW(), NOW()),
('Camiseta Nike', 'SKU002', 5, 10, 'Camiseta Nike de algodón', 50, 10, 2, NOW(), NOW()),
('Arroz 1kg', 'SKU003', 2, 3, 'Arroz blanco premium', 100, 20, 3, NOW(), NOW()),
('Sofá 3 plazas', 'SKU004', 300, 450, 'Sofá moderno 3 plazas', 5, 2, 4, NOW(), NOW()),
('Balón de fútbol', 'SKU005', 15, 25, 'Balón profesional', 30, 5, 5, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Insertar proveedores de ejemplo
INSERT INTO proveedor (nombre, email, telefono)
VALUES
('Tech Supplies', 'tech@example.com', '123-456-7890'),
('Ropa Express', 'ropa@example.com', '234-567-8901'),
('Alimentos SA', 'alimentos@example.com', '345-678-9012'),
('Muebles y Más', 'muebles@example.com', '456-789-0123'),
('Deportes Pro', 'deportes@example.com', '567-890-1234')
ON CONFLICT DO NOTHING;