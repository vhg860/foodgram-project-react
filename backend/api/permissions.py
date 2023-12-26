from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrAdminOrReadOnly(BasePermission):
    """Кастомное разрешение для проверки доступа к объектам."""

    def has_permission(self, request, view):
        """Проверяет разрешение на уровне представления."""
        return (request.method in SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """Проверяет разрешение для конкретного объекта."""
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
        )
