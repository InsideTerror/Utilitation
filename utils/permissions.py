async def is_authorized(member, required_roles):
    """
    Checks if a user has at least one of the required Discord roles.
    """
    if member.guild is None:
        return False
    member_roles = [role.name for role in member.roles]
    return any(role in member_roles for role in required_roles)
