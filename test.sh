#!/bin/bash
for i in {1..1000}; do
    echo "Hola ($i/10)"  # El contador (i/10) es opcional
    echo "Mensaje de prueba" | msmtp montapetro@gmail.com
    sleep 2  # Espera 1 segundo
done
echo "¡Listo!"  # Mensaje final (opcional)
