from sqlalchemy import select

from app.db.session import SessionLocal
from app.modules.users.models import Permission, Role


PERMISSIONS = [
    ("users.read", "Просмотр пользователей"),
    ("users.write", "Управление пользователями"),

    ("members.read", "Просмотр членов СНТ"),
    ("members.write", "Управление членами СНТ"),

    ("plots.read", "Просмотр участков"),
    ("plots.write", "Управление участками"),

    ("finance.read", "Просмотр финансов"),
    ("finance.write", "Управление финансами"),

    ("requests.read", "Просмотр заявок"),
    ("requests.write", "Управление заявками"),

    ("works.read", "Просмотр работ"),
    ("works.write", "Управление работами"),

    ("meetings.read", "Просмотр собраний"),
    ("meetings.write", "Управление собраниями"),

    ("documents.read", "Просмотр документов"),
    ("documents.write", "Управление документами"),

    ("announcements.read", "Просмотр объявлений"),
    ("announcements.write", "Управление объявлениями"),

    ("audit.read", "Просмотр журнала аудита"),
]


ROLES = [
    ("ADMIN", "Администратор"),
    ("BOARD", "Правление"),
    ("AUDIT", "Ревизионная комиссия"),
    ("CONTRACTOR", "Подрядчик"),
    ("MEMBER", "Член СНТ"),
]


def seed_rbac() -> None:
    with SessionLocal() as db:
        # Permissions
        permissions = {}

        for code, description in PERMISSIONS:
            permission = db.scalar(
                select(Permission).where(Permission.code == code)
            )

            if permission is None:
                permission = Permission(
                    code=code,
                    description=description,
                )
                db.add(permission)

            permissions[code] = permission

        # Flush so newly created permissions receive IDs
        db.flush()

        # Roles
        roles = {}

        for name, description in ROLES:
            role = db.scalar(
                select(Role).where(Role.name == name)
            )

            if role is None:
                role = Role(
                    name=name,
                    description=description,
                )
                db.add(role)

            roles[name] = role

        db.flush()

        # ADMIN gets all permissions
        roles["ADMIN"].permissions = list(permissions.values())

        # BOARD
        roles["BOARD"].permissions = [
            permissions["members.read"],
            permissions["members.write"],
            permissions["plots.read"],
            permissions["plots.write"],
            permissions["finance.read"],
            permissions["finance.write"],
            permissions["requests.read"],
            permissions["requests.write"],
            permissions["works.read"],
            permissions["works.write"],
            permissions["meetings.read"],
            permissions["meetings.write"],
            permissions["documents.read"],
            permissions["documents.write"],
            permissions["announcements.read"],
            permissions["announcements.write"],
        ]

        # AUDIT
        roles["AUDIT"].permissions = [
            permissions["finance.read"],
            permissions["documents.read"],
            permissions["audit.read"],
        ]

        # CONTRACTOR
        roles["CONTRACTOR"].permissions = [
            permissions["works.read"],
            permissions["works.write"],
            permissions["documents.read"],
            permissions["documents.write"],
        ]

        # MEMBER
        roles["MEMBER"].permissions = [
            permissions["members.read"],
            permissions["plots.read"],
            permissions["finance.read"],
            permissions["requests.read"],
            permissions["requests.write"],
            permissions["works.read"],
            permissions["meetings.read"],
            permissions["documents.read"],
            permissions["announcements.read"],
        ]

        db.commit()


if __name__ == "__main__":
    seed_rbac()
    print("RBAC seed completed.")
