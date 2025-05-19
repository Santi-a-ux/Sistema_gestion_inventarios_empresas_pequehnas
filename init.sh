#!/bin/bash

# Crear directorios necesarios
mkdir -p elasticsearch/config
mkdir -p logstash/config
mkdir -p logstash/pipeline
mkdir -p kibana/config

# Copiar archivos de configuración
cp elasticsearch/config/elasticsearch.yml elasticsearch/config/
cp logstash/config/logstash.yml logstash/config/
cp logstash/pipeline/logstash.conf logstash/pipeline/
cp kibana/config/kibana.yml kibana/config/

# Dar permisos necesarios
chmod -R 777 elasticsearch/config
chmod -R 777 logstash/config
chmod -R 777 logstash/pipeline
chmod -R 777 kibana/config

# Iniciar los servicios
docker-compose up -d

# Esperar a que los servicios estén listos
echo "Esperando a que los servicios estén listos..."
sleep 30

# Verificar el estado de los servicios
docker-compose ps

echo "Sistema inicializado correctamente" 