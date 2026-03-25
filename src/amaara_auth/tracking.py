"""Cross-agent user tracking — records authenticated user access to GAMA's Firestore.

When an agent sets `tracking_service_name` in its AmaaraAuthSettings, this module
records each authenticated user's access in the GAMA Firestore project so that
GAMA's Users tab can show who is using which agents across the org.

Firestore collections (in the GAMA project):
  - users/{email}                              — user profile + aggregate stats
  - user_agent_access/{email}::{service_name}  — per-user, per-agent access record
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

logger = logging.getLogger(__name__)

# Minimum gap between session increments for the same user+agent.
_SESSION_GAP = timedelta(minutes=5)

# Module-level Firestore client, lazily initialized.
_firestore_client = None
_firestore_project: str | None = None


def _get_firestore(project: str):
    """Lazily initialize and return the Firestore client for the GAMA project."""
    global _firestore_client, _firestore_project

    if _firestore_client and _firestore_project == project:
        return _firestore_client

    try:
        from google.cloud import firestore

        _firestore_client = firestore.Client(project=project)
        _firestore_project = project
        return _firestore_client
    except Exception:
        logger.debug("Could not initialize Firestore client for tracking", exc_info=True)
        return None


def record_access(email: str, service_name: str, gcp_project: str) -> None:
    """Record that a user accessed an agent in GAMA's Firestore.

    Debounces: only increments session_count if the last recorded activity for
    this user+agent was more than _SESSION_GAP ago. Request count always increments.
    """
    db = _get_firestore(gcp_project)
    if not db:
        return

    try:
        from google.cloud import firestore

        now = datetime.now(UTC)

        # Upsert user document.
        user_ref = db.collection("users").document(email)
        user_doc = user_ref.get()

        if user_doc.exists:
            last = user_doc.to_dict().get("last_active")
            is_new_session = not last or not hasattr(last, "timestamp") or (now - last) > _SESSION_GAP
            update: dict = {"last_active": now}
            if is_new_session:
                update["total_sessions"] = firestore.Increment(1)
            user_ref.update(update)
        else:
            user_ref.set({
                "email": email,
                "first_seen": now,
                "last_active": now,
                "total_sessions": 1,
            })

        # Upsert per-agent access record.
        access_id = f"{email}::{service_name}"
        access_ref = db.collection("user_agent_access").document(access_id)
        access_doc = access_ref.get()

        if access_doc.exists:
            last = access_doc.to_dict().get("last_active")
            is_new_session = not last or not hasattr(last, "timestamp") or (now - last) > _SESSION_GAP
            update = {
                "last_active": now,
                "request_count": firestore.Increment(1),
            }
            if is_new_session:
                update["session_count"] = firestore.Increment(1)
            access_ref.update(update)
        else:
            access_ref.set({
                "email": email,
                "service_name": service_name,
                "first_seen": now,
                "last_active": now,
                "session_count": 1,
                "request_count": 1,
            })
    except Exception:
        logger.debug("Failed to record user tracking for %s on %s", email, service_name, exc_info=True)
