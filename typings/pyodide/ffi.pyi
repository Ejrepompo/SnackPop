from typing import Any, Callable


def create_proxy(
    callback: Callable[..., Any],
    /,
    *,
    capture_this: bool = False,
) -> Any: ...
