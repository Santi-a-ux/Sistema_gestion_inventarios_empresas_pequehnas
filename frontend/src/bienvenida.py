import tkinter as tk
from tkinter import ttk

# Crear ventana principal
ventana = tk.Tk()
ventana.title("Sistema de Gestión")
ventana.geometry("500x200")
ventana.configure(bg="#e0e7ff")

# Contenedor principal
frame = ttk.Frame(ventana, padding=20)
frame.pack(expand=True)

# Título
titulo = ttk.Label(frame, text="¡Bienvenido!", font=("Segoe UI", 20))
titulo.pack(pady=10)

# Mensaje
mensaje = ttk.Label(frame, text="Esta es tu aplicación de gestión para inventario en pequeñas empresas.", wraplength=500)
mensaje.pack()

# Ejecutar la app
ventana.mainloop()
