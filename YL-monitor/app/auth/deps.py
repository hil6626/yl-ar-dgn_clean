from typing import Optional


def get_current_user() -> Optional[dict]:
    """
    预留的认证依赖，占位实现。
    后续可替换为 JWT / Session 等真实认证逻辑。
    """
    return None
