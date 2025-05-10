from werkzeug.security import generate_password_hash
import os

# Generar hash para 'admin123'
password = 'admin123'
hash = generate_password_hash(password)

# Leer el archivo init.sql desde el directorio raíz
with open('../init.sql', 'r') as f:
    content = f.read()

# Reemplazar el hash actual con el nuevo
new_content = content.replace(
    "'pbkdf2:sha256:600000$X7URIFnX$8c5d0f1e2c3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0'",
    f"'{hash}'"
)

# Guardar el archivo actualizado
with open('../init.sql', 'w') as f:
    f.write(new_content)

print("Hash actualizado en init.sql") 