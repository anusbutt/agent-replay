"""Fire-and-forget delivery to POST /ingest (constitution V — SDK never raises).

Every transport/recording error is swallowed and logged locally only. A
recording failure must be invisible to the host agent (pinned decision 5).
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger("agentreplay")


def send_batch(base_url: str, api_key: str, batch: dict[str, Any]) -> None:
    try:
        resp = httpx.post(
            f"{base_url}/ingest",
            json=batch,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=5.0,
        )
        if resp.status_code >= 400:
            logger.warning("agentreplay: ingest rejected batch (%s): %s", resp.status_code, resp.text)
    except Exception as exc:  # noqa: BLE001 — swallow every transport error, never raise into host code
        logger.warning("agentreplay: failed to deliver batch: %s", exc)
