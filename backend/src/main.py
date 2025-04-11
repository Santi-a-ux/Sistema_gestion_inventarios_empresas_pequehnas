from fastapi import FastAPI, Path

app = FastAPI(title="Sistema de Gestión - API", version="1.0")

@app.get("/", summary="Página principal", description="Devuelve un mensaje de bienvenida al sistema.")
def read_root():
    return {"mensaje": "¡Bienvenido a la API del sistema de gestión!"}

@app.get("/clientes/{id}", summary="Obtener cliente", description="Devuelve los datos de un cliente dado su ID.")
def leer_cliente(id: int = Path(..., description="ID del cliente a buscar", gt=0)):
    return {"id": id, "nombre": f"Cliente {id}"}
