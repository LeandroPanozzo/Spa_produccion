#!/usr/bin/env bash
# Exit on error
set -o errexit

# Instala los paquetes requeridos
pip install -r requirements.txt

# Convierte los archivos de estáticos
python manage.py collectstatic --no-input

# Aplica las migraciones pendientes
python manage.py migrate

# Crear un superusuario automáticamente si no existe
if [ -z "$(echo "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).exists())" | python manage.py shell)" ]; then
    echo "Creando superusuario..."
    python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')"
else
    echo "Superusuario ya existe."
fi
# 'admin', 'admin@example.com' y 'adminpassword'