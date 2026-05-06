from __future__ import annotations

import logging
from typing import Any

import requests
from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context

from backend.model_service import chunk_text, to_ndjson
from backend.services import serialize_chat, serialize_chat_summary
from backend.validators import ValidationError, resolve_api_key, validate_chat_id, validate_messages, validate_model, validate_scene_mode

chat_bp = Blueprint("chat", __name__)
logger = logging.getLogger("teaching_agent")


def _stream_chat_response(model: str, api_key: str, chat_id: str, incoming_messages: list[dict[str, Any]], scene_mode: str):
    call_model_api = current_app.extensions["teaching_agent"]["call_model_api"]
    upsert_chat = current_app.extensions["teaching_agent"]["upsert_chat"]
    try:
        yield to_ndjson({"type": "status", "status": "started", "chat_id": chat_id})
        reply = call_model_api(model=model, api_key=api_key, messages=incoming_messages)
        chunks = chunk_text(reply, 24)
        assembled = ""
        for chunk in chunks:
            assembled += chunk
            yield to_ndjson({"type": "delta", "delta": chunk, "content": assembled})
        with current_app.app_context():
            saved_chat = upsert_chat(chat_id=chat_id, incoming_messages=incoming_messages, reply=reply)
            serialized_chat = serialize_chat(saved_chat)
        logger.info("chat_completed chat_id=%s model=%s scene_mode=%s message_count=%s stream=%s", chat_id, model, scene_mode, len(incoming_messages), True)
        yield to_ndjson({"type": "done", "status": "success", "reply": reply, "chat": serialized_chat})
    except ValidationError as exc:
        logger.warning("validation_error error=%s", exc)
        yield to_ndjson({"type": "error", "error": str(exc), "status": "fail"})
    except requests.Timeout:
        logger.warning("model_timeout")
        yield to_ndjson({"type": "error", "error": "模型请求超时，请稍后重试", "status": "fail"})
    except requests.RequestException as exc:
        logger.exception("model_request_failed")
        yield to_ndjson({"type": "error", "error": f"模型调用失败：{exc}", "status": "fail"})
    except Exception:
        logger.exception("internal_server_error")
        yield to_ndjson({"type": "error", "error": "服务器内部错误", "status": "fail"})


@chat_bp.get("/api/chats")
def get_chats():
    fetch_all_chats = current_app.extensions["teaching_agent"]["fetch_all_chats"]
    chat_lock = current_app.extensions["teaching_agent"]["chat_lock"]
    with chat_lock:
        chat_list = [serialize_chat_summary(chat) for chat in fetch_all_chats()]
    chat_list.sort(key=lambda item: item["updated_at"], reverse=True)
    return jsonify({"items": chat_list})


@chat_bp.get("/api/chats/<chat_id>")
def get_chat(chat_id: str):
    fetch_chat_by_id = current_app.extensions["teaching_agent"]["fetch_chat_by_id"]
    chat_lock = current_app.extensions["teaching_agent"]["chat_lock"]
    with chat_lock:
        chat = fetch_chat_by_id(chat_id)
        if chat is None:
            return jsonify({"error": "会话不存在"}), 404
        payload = serialize_chat(chat)
    return jsonify(payload)


@chat_bp.post("/api/chat")
def chat():
    call_model_api = current_app.extensions["teaching_agent"]["call_model_api"]
    trim_messages = current_app.extensions["teaching_agent"]["trim_messages"]
    with_scene_prompt = current_app.extensions["teaching_agent"]["with_scene_prompt"]
    upsert_chat = current_app.extensions["teaching_agent"]["upsert_chat"]
    max_message_count = current_app.config["MAX_MESSAGE_COUNT"]
    max_text_length = current_app.config["MAX_TEXT_LENGTH"]
    max_image_bytes = current_app.config["MAX_IMAGE_BYTES"]
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValidationError("请求体必须是 JSON 对象")

        model = validate_model(data.get("model"))
        scene_mode = validate_scene_mode(data.get("scene_mode"))
        api_key = resolve_api_key(data.get("api_key"), model, current_app.config.get("DEFAULT_API_KEYS", {}))
        chat_id = validate_chat_id(data.get("chat_id"))
        incoming_messages = validate_messages(data.get("messages"), max_message_count, max_text_length, max_image_bytes)
        message_window = trim_messages(with_scene_prompt(incoming_messages, scene_mode), max_message_count)
        stream = bool(data.get("stream"))

        if stream:
            return Response(
                stream_with_context(
                    _stream_chat_response(
                        model=model,
                        api_key=api_key,
                        chat_id=chat_id,
                        incoming_messages=message_window,
                        scene_mode=scene_mode,
                    )
                ),
                mimetype="application/x-ndjson",
            )

        reply = call_model_api(model=model, api_key=api_key, messages=message_window)
        saved_chat = upsert_chat(chat_id=chat_id, incoming_messages=message_window, reply=reply)
        logger.info("chat_completed chat_id=%s model=%s scene_mode=%s message_count=%s", chat_id, model, scene_mode, len(message_window))
        return jsonify({"status": "success", "chat": serialize_chat(saved_chat), "reply": reply})
    except ValidationError as exc:
        logger.warning("validation_error error=%s", exc)
        return jsonify({"status": "fail", "error": str(exc)}), 400
    except requests.Timeout:
        logger.warning("model_timeout")
        return jsonify({"status": "fail", "error": "模型请求超时，请稍后重试"}), 504
    except requests.RequestException as exc:
        logger.exception("model_request_failed")
        return jsonify({"status": "fail", "error": f"模型调用失败：{exc}"}), 502
    except Exception:
        logger.exception("internal_server_error")
        return jsonify({"status": "fail", "error": "服务器内部错误"}), 500


@chat_bp.delete("/api/chats/<chat_id>")
def delete_chat(chat_id: str):
    remove_chat = current_app.extensions["teaching_agent"]["remove_chat"]
    chat_lock = current_app.extensions["teaching_agent"]["chat_lock"]
    with chat_lock:
        deleted = remove_chat(chat_id)
    if not deleted:
        return jsonify({"error": "会话不存在"}), 404
    return jsonify({"status": "success"})


@chat_bp.patch("/api/chats/<chat_id>")
def rename_chat(chat_id: str):
    fetch_chat_by_id = current_app.extensions["teaching_agent"]["fetch_chat_by_id"]
    save_chat = current_app.extensions["teaching_agent"]["save_chat"]
    utc_now = current_app.extensions["teaching_agent"]["utc_now"]
    chat_lock = current_app.extensions["teaching_agent"]["chat_lock"]
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "标题不能为空"}), 400
    if len(title) > 60:
        return jsonify({"error": "标题长度不能超过 60 个字符"}), 400

    with chat_lock:
        chat = fetch_chat_by_id(chat_id)
        if chat is None:
            return jsonify({"error": "会话不存在"}), 404
        chat.title = title
        chat.updated_at = utc_now()
        save_chat(chat)
        payload = serialize_chat(chat)
    return jsonify({"status": "success", "chat": payload})
