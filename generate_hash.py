from werkzeug.security import generate_password_hash, check_password_hash

# Generar hash para 'admin123'
password = 'admin123'
hash = generate_password_hash(password)
print("Hash generado:", hash)

# Verificar que el hash es válido
is_valid = check_password_hash(hash, password)
print("Verificación:", is_valid)

# Verificar con el hash actual
current_hash = 'pbkdf2:sha256:600000$X7URIFnX$8c5d0f1e2c3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0'
is_valid_current = check_password_hash(current_hash, password)
print("Verificación del hash actual:", is_valid_current) 