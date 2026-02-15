from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: str
    name: str
    is_active: bool = True


def get_user(user_id: str) -> Optional[User]:
    """
    用户读取占位实现。
    """
    if not user_id:
        return None
    return User(id=user_id, name=f"user-{user_id}")
