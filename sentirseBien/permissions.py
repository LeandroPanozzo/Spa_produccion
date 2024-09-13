from rest_framework import permissions

class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    """
    def has_permission(self, request, view):
        # Solo permite métodos de lectura si no es administrador
        if request.method in permissions.SAFE_METHODS:
            return True
        # Si el usuario es administrador, permite todos los métodos
        return request.user and request.user.is_staff


class IsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        # Permitir GET, HEAD, OPTIONS (lectura) para todos
        if request.method in permissions.SAFE_METHODS:
            return True

        # Permitir POST, PUT, PATCH, DELETE solo para staff
        if request.user.is_staff and request.method in ['POST','PUT', 'PATCH', 'DELETE']:
            return True
        
class IsStaffAndReadOrEditOnly(permissions.BasePermission):
    """
    Custom permission to allow staff to read, edit, and delete appointments, but not create new ones.
    """

    def has_permission(self, request, view):
        # Permitir GET, HEAD, OPTIONS (lectura) para todos
        if request.method in permissions.SAFE_METHODS:
            return True

        # Permitir PUT, PATCH, DELETE (editar y eliminar) solo para staff
        if request.user.is_staff and request.method in ['PUT', 'PATCH', 'DELETE']:
            return True

        # Bloquear POST (crear) para staff
        if request.user.is_staff and request.method == 'POST':
            return False

        # Permitir todas las acciones para usuarios que no son staff
        return not request.user.is_staff