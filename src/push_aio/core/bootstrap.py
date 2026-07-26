from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select

from ..models import Channel
from ..services.channels import registry
from .db import session_scope


BASE_DIR = Path(__file__).resolve().parents[3]
BOOTSTRAP_FILE = BASE_DIR / "data" / "bootstrap_channels.json"


def bootstrap_channels_if_needed() -> None:
    if not BOOTSTRAP_FILE.exists():
        return

    with session_scope() as db:
        has_channel = db.scalar(select(Channel.id).limit(1))
        if has_channel:
            return

        payload = json.loads(BOOTSTRAP_FILE.read_text(encoding="utf-8"))
        for item in payload:
            channel = Channel(
                name=item["name"],
                type=item["type"],
                enabled=item.get("enabled", True),
                default_target=item.get("default_target"),
                config=registry.validate(item["type"], item["config"]),
                backup_channel_ids=item.get("backup_channel_ids", []),
                is_emergency=item.get("is_emergency", False),
                priority=item.get("priority", 100),
            )
            db.add(channel)
