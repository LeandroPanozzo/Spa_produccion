#!/usr/bin/env bash
# Exit on error
set -o errexit

# Instala los paquetes requeridos
pip install -r requirements.txt

# Convierte los archivos de estáticos
python manage.py collectstatic --no-input

# Aplica las migraciones pendientes
python manage.py migrate

#creacion de usuario admin 
#export DJANGO_SUPERUSER_USERNAME=admin
#export DJANGO_SUPERUSER_EMAIL=test@test.com
#export DJANGO_SUPERUSER_PASSWORD=testpass123498765
#python manage.py createsuperuser --no-input