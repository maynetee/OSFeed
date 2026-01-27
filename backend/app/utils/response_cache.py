from typing import Callable, Any
from urllib.parse import parse_qsl, urlencode

from fastapi_cache.decorator import cache

from app.config import get_settings

settings = get_settings()


def user_aware_key_builder(
    func: Callable[..., Any],
    namespace: str,
    request,
    response,
    *args,
    **kwargs,
) -> str:
    user = kwargs.get("user")
    user_id = getattr(user, "id", "anonymous")
    sorted_query = urlencode(sorted(parse_qsl(str(request.url.query))))
    return f"{namespace}:{user_id}:{request.url.path}?{sorted_query}"


def response_cache(expire: int, namespace: str):
    if not settings.enable_response_cache or not settings.redis_url:
        def passthrough(func: Callable[..., Any]):
            return func

        return passthrough

    return cache(expire=expire, namespace=namespace, key_builder=user_aware_key_builder)
