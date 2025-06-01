def has_role_permission(member, allowed_roles):
    """Check if a Discord member has any role in allowed_roles (case-insensitive)."""
    member_roles = [role.name.lower() for role in member.roles]
    allowed = [role.lower() for role in allowed_roles]
    return any(role in member_roles for role in allowed)
