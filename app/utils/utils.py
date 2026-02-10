from uuid import UUID


def is_valid_uuid4(id: str) -> bool:
    """Validate if the user_id is a valid UUID4"""
    if not id or not isinstance(id, str):
        return False

    try:
        uuid_obj = UUID(id, version=4)
        return str(uuid_obj) == id
    except (ValueError, AttributeError):
        return False