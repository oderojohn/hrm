from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == user.Role.SUPER_ADMIN)


class IsHRManagerOrAbove(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role in {user.Role.SUPER_ADMIN, user.Role.HR_MANAGER}
        )


class IsDepartmentManagerOrAbove(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role
            in {user.Role.SUPER_ADMIN, user.Role.HR_MANAGER, user.Role.DEPARTMENT_MANAGER}
        )


class IsSelfOrManager(BasePermission):
    """Grants access to the resource owner's own record, or to HR/managers.

    Assumes the object either *is* an Employee, or exposes `.employee`.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role in {user.Role.SUPER_ADMIN, user.Role.HR_MANAGER}:
            return True

        employee = getattr(obj, "employee", obj)
        own_employee = getattr(user, "employee", None)

        if user.role == user.Role.DEPARTMENT_MANAGER:
            return bool(
                own_employee
                and getattr(employee, "department_id", None) == own_employee.department_id
            )

        return bool(own_employee and employee.pk == own_employee.pk)
