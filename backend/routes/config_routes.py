from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from backend.constants import MODEL_CONFIG

config_bp = Blueprint("config", __name__)


@config_bp.get("/api/config/default-keys")
def get_default_key_status():
    default_keys = current_app.config.get("DEFAULT_API_KEYS", {})
    return jsonify({"items": {model: bool((default_keys.get(model) or "").strip()) for model in MODEL_CONFIG}})
