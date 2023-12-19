from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrAdminOrReadOnly(BasePermission):
    """
    Кастомное разрешение для проверки доступа к объектам.
    Разрешает только владельцам или администраторам выполнять изменения,
    в противном случае разрешены только безопасные методы (GET, HEAD, OPTIONS).
    """

    def has_permission(self, request, view):
        """Проверяет разрешение на уровне представления"""

        return (request.method in SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """Проверяет разрешение для конкретного объекта"""

        if request.method in SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        return obj.author == request.user
