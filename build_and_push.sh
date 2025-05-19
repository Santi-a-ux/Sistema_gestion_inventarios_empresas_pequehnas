#!/bin/bash

# Configuración
DOCKER_USERNAME="santiagoaux"
VERSION="1.0.1"

# Construir imágenes
echo "Construyendo imágenes..."
docker build -t $DOCKER_USERNAME/product-system-frontend:$VERSION ./frontend
docker build -t $DOCKER_USERNAME/product-system-backend:$VERSION ./backend

# Subir imágenes a Docker Hub
echo "Subiendo imágenes a Docker Hub..."
docker push $DOCKER_USERNAME/product-system-frontend:$VERSION
docker push $DOCKER_USERNAME/product-system-backend:$VERSION

echo "¡Proceso completado!" 