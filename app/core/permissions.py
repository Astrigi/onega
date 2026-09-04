def has_permission(user, permission_code: str) -> bool:
    if user is None:
        return False

    for role in user.roles:
        for permission in role.permissions:
            if permission.code == permission_code:
                return True

    return False
