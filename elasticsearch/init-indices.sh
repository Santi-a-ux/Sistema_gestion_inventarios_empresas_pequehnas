#!/bin/bash

# Esperar a que Elasticsearch esté listo
until curl -s http://elasticsearch:9200 > /dev/null; do
    echo "Esperando a que Elasticsearch esté listo..."
    sleep 1
done

# Crear política de retención
curl -X PUT "http://elasticsearch:9200/_ilm/policy/logs-policy" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_age": "7d",
            "max_size": "5gb"
          }
        }
      },
      "delete": {
        "min_age": "30d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}'

# Crear índice para logs con la política de retención
curl -X PUT "http://elasticsearch:9200/product-system-logs" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "lifecycle.name": "logs-policy"
  },
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "message": { "type": "text" },
      "level": { "type": "keyword" },
      "logger": { "type": "keyword" },
      "path": { "type": "keyword" },
      "line": { "type": "integer" },
      "function": { "type": "keyword" },
      "severity": { "type": "keyword" },
      "source": { "type": "keyword" },
      "service": { "type": "keyword" },
      "environment": { "type": "keyword" },
      "request_method": { "type": "keyword" },
      "request_path": { "type": "keyword" },
      "request_status": { "type": "keyword" }
    }
  }
}'

echo "Índices y políticas creados exitosamente" 