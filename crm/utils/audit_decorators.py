from functools import wraps
from typing import Callable, Literal
from crm.utils.sentry_config import audit_breadcrumb, audit_event, get_audit_logger


def audit_command(
    category: str,
    action: str,
    issue_level_on_error: Literal["error", "critical", "fatal"] = "error",
    event_level_on_success: Literal["info", "warning"] = "info",
):
    """
    - Breadcrumb "start" avant exécution
    - Event "ok" si succès
    - Event + issue Sentry si exception
    """

    def deco(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            audit_breadcrumb(
                category, f"{action}: start", {"args": str(args), "kwargs": kwargs}
            )
            try:
                result = func(*args, **kwargs)
                audit_event(
                    f"{action}: ok", {"kwargs": kwargs}, level=event_level_on_success
                )
                return result
            except Exception as e:
                # Event + issue (via level error/critical/fatal)
                audit_event(
                    f"{action}: error",
                    {"kwargs": kwargs, "error": str(e)},
                    level=issue_level_on_error,
                )
                get_audit_logger().error("%s failed: %s", action, e, exc_info=True)
                raise

        return wrapper

    return deco
