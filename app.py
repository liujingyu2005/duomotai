from __future__ import annotations

import base64
import binascii
import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

import requests
from flask import Flask, Response, jsonify, request, send_from_directory, stream_with_context

from backend.constants import MODEL_CONFIG, SCENE_PROMPTS
from backend.model_service import call_model_api as model_service_call_model_api
from backend.models import ChatSession
from backend.repository import close_db as repository_close_db
from backend.repository import fetch_all_chats as repository_fetch_all_chats
from backend.repository import fetch_chat_by_id as repository_fetch_chat_by_id
from backend.repository import init_db as repository_init_db
from backend.repository import remove_chat as repository_remove_chat
from backend.repository import save_chat as repository_save_chat
from backend.routes.chat_routes import chat_bp
from backend.routes.config_routes import config_bp
from backend.routes.defense_routes import defense_bp
from backend.services import build_defense_analysis
from backend.services import extract_latest_user_text
from backend.services import serialize_chat
from backend.services import serialize_chat_summary
from backend.services import trim_messages
from backend.services import utc_now as service_utc_now
from backend.services import upsert_chat as service_upsert_chat
from backend.services import with_scene_prompt
from backend.validators import ValidationError
from backend.validators import resolve_api_key
from backend.validators import validate_chat_id
from backend.validators import validate_messages
from backend.validators import validate_model
from backend.validators import validate_scene_mode

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
MAX_MESSAGE_COUNT = 40
MAX_TEXT_LENGTH = 4000
MAX_IMAGE_BYTES = 5 * 1024 * 1024
DEFAULT_REQUEST_TIMEOUT = 60

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["JSON_AS_ASCII"] = False
app.config["APP_HOST"] = os.getenv("APP_HOST", "127.0.0.1")
app.config["APP_PORT"] = int(os.getenv("APP_PORT", "5000"))
app.config["APP_DEBUG"] = os.getenv("APP_DEBUG", "false").lower() == "true"
app.config["DATABASE_PATH"] = os.path.join(
    BASE_DIR,
    os.getenv("DATABASE_PATH", os.path.join("instance", "teaching_agent.db")),
)
app.config["REQUEST_TIMEOUT"] = int(os.getenv("REQUEST_TIMEOUT", str(DEFAULT_REQUEST_TIMEOUT)))
app.config["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "INFO").upper()
app.config["MAX_MESSAGE_COUNT"] = MAX_MESSAGE_COUNT
app.config["MAX_TEXT_LENGTH"] = MAX_TEXT_LENGTH
app.config["MAX_IMAGE_BYTES"] = MAX_IMAGE_BYTES
app.config["DEFAULT_API_KEYS"] = {
    "deepseek": os.getenv("DEEPSEEK_API_KEY", "").strip(),
    "zhipu": os.getenv("ZHIPU_API_KEY", "").strip(),
    "tyqw": os.getenv("TYQW_API_KEY", "").strip(),
}
os.makedirs(os.path.dirname(app.config["DATABASE_PATH"]), exist_ok=True)
os.makedirs(INSTANCE_DIR, exist_ok=True)
logging.basicConfig(
    level=getattr(logging, app.config["LOG_LEVEL"], logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("teaching_agent")


chat_lock = threading.RLock()

app.extensions.setdefault("teaching_agent", {})
app.extensions["teaching_agent"].update(
    {
        "chat_lock": chat_lock,
        "call_model_api": lambda model, api_key, messages: call_model_api(model, api_key, messages),
        "trim_messages": trim_messages,
        "with_scene_prompt": with_scene_prompt,
        "upsert_chat": lambda chat_id, incoming_messages, reply: upsert_chat(chat_id, incoming_messages, reply),
        "fetch_chat_by_id": lambda chat_id: fetch_chat_by_id(chat_id),
        "fetch_all_chats": lambda: fetch_all_chats(),
        "save_chat": lambda chat: save_chat(chat),
        "remove_chat": lambda chat_id: remove_chat(chat_id),
        "utc_now": lambda: utc_now(),
        "extract_latest_user_text": extract_latest_user_text,
        "build_defense_analysis": build_defense_analysis,
    }
)


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "connect-src 'self' https://api.deepseek.com https://open.bigmodel.cn https://dashscope.aliyuncs.com;"
    )
    return response


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.get("/health")
def health():
    return jsonify({"status": "ok", "time": utc_now(), "database": app.config["DATABASE_PATH"]})


app.register_blueprint(chat_bp)
app.register_blueprint(config_bp)
app.register_blueprint(defense_bp)


def utc_now() -> str:
    return service_utc_now()


def call_model_api(model: str, api_key: str, messages: list[dict[str, Any]]) -> str:
    return model_service_call_model_api(model, api_key, messages, app.config["REQUEST_TIMEOUT"])


def upsert_chat(chat_id: str, incoming_messages: list[dict[str, Any]], reply: str) -> ChatSession:
    with chat_lock:
        return service_upsert_chat(chat_id, incoming_messages, reply, fetch_chat_by_id, save_chat)


def fetch_chat_by_id(chat_id: str) -> ChatSession | None:
    return repository_fetch_chat_by_id(app.config["DATABASE_PATH"], chat_id)


@app.teardown_appcontext
def close_db(error: Exception | None):
    repository_close_db()


def fetch_all_chats() -> list[ChatSession]:
    return repository_fetch_all_chats(app.config["DATABASE_PATH"])


def save_chat(chat: ChatSession):
    repository_save_chat(app.config["DATABASE_PATH"], chat)


def remove_chat(chat_id: str) -> bool:
    return repository_remove_chat(app.config["DATABASE_PATH"], chat_id)


def init_db(force: bool = False):
    repository_init_db(app.config["DATABASE_PATH"], force=force)


with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(
        host=app.config["APP_HOST"],
        port=app.config["APP_PORT"],
        debug=app.config["APP_DEBUG"],
    )
