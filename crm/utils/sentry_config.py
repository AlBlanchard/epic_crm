from __future__ import annotations

import os
import sys
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Literal

from dotenv import load_dotenv
import sentry_sdk
from sentry_sdk import add_breadcrumb, capture_exception, capture_message
from sentry_sdk.integrations.logging import LoggingIntegration

# Charge .env en dev (sans effet si absent)
load_dotenv()


# Logger "audit"
# ---------------------------------------------------------------------------

_AUDIT_LOGGER_NAME = "audit"
_logger_initialized = False


def get_audit_logger() -> logging.Logger:
    """Retourne un logger 'audit' configuré une seule fois."""
    global _logger_initialized
    logger = logging.getLogger(_AUDIT_LOGGER_NAME)
    if not _logger_initialized:
        logger.setLevel(logging.INFO)
        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
            )
            logger.addHandler(handler)
        _logger_initialized = True
    return logger


# Sentry init & sécurité
# ---------------------------------------------------------------------------

_sentry_initialized = False


def _before_send(event, hint):
    """
    Scrubbing *minimal* (à adapter):
    - Exemple: évite d'envoyer des emails tels quels dans event.message
    """
    msg = event.get("message")
    if msg and isinstance(msg, str):
        event["message"] = msg.replace("@", " [at] ")
    return event


def init_sentry():
    """Initialise Sentry si SENTRY_DSN est présent. Idempotent."""
    global _sentry_initialized
    if _sentry_initialized:
        return

    dsn = os.getenv("SENTRY_DSN")
    logger = get_audit_logger()

    if not dsn:
        logger.warning("Sentry désactivé (SENTRY_DSN manquant).")
        return

    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # tout >= INFO devient breadcrumb
        event_level=logging.ERROR,  # ERROR/CRITICAL => issue Sentry
    )

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("SENTRY_ENV", "prod"),
        release=os.getenv("SENTRY_RELEASE", "epic-crm@1.0.0"),
        integrations=[sentry_logging],
        traces_sample_rate=0.0,  # active si tu veux le APM
        send_default_pii=False,  # sécurité par défaut
        before_send=_before_send,
    )

    _sentry_initialized = True
    logger.info("Sentry initialisé.")


# Hook global des exceptions
# ---------------------------------------------------------------------------

_hook_installed = False


def install_global_exception_hook():
    """Capture toutes les exceptions non gérées et loggue en CRITICAL."""
    global _hook_installed
    if _hook_installed:
        return

    logger = get_audit_logger()

    def _global_exception_hook(exc_type, exc, tb):
        # Sentry (si init) + log local
        try:
            capture_exception(exc)
        except Exception:
            pass
        logger.critical("Unhandled exception", exc_info=(exc_type, exc, tb))

    sys.excepthook = _global_exception_hook
    _hook_installed = True


# API d'audit (breadcrumbs + events Sentry)
# ---------------------------------------------------------------------------


def audit_breadcrumb(
    category: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
):
    """Ajoute un breadcrumb structuré visible dans Sentry (timeline)."""
    add_breadcrumb(
        category=category,
        message=message,
        level="info",
        type="default",
        data=data or {},
        timestamp=datetime.utcnow().timestamp(),
    )


def audit_event(
    message: str,
    data: Optional[Dict[str, Any]] = None,
    level: Literal["fatal", "critical", "error", "warning", "info", "debug"] = "info",
):
    """
    Envoie un évènement explicite à Sentry.
    - level="info"/"warning" : événements visibles (pas forcément un "issue")
    - level="error"/"critical"/"fatal" : crée un "issue" Sentry
    """
    sentry_sdk.set_context("audit", data or {})
    capture_message(message, level=level)
