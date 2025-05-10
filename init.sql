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