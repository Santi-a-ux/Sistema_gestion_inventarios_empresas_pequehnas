from werkzeug.security import generate_password_hash
 
# Generar hash para 'admin123'
password = 'admin123'
hash = generate_password_hash(password)
print("\nCopia este hash y reemplázalo en init.sql:")
print(hash) 