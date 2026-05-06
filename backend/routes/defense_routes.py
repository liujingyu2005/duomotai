from __future__ import annotations

import logging

from flask import Blueprint, current_app, jsonify, request

from backend.validators import ValidationError, validate_messages

logger = logging.getLogger("teaching_agent")
defense_bp = Blueprint("defense", __name__)


@defense_bp.post("/api/defense-analysis")
def defense_analysis():
    extract_latest_user_text = current_app.extensions["teaching_agent"]["extract_latest_user_text"]
    build_defense_analysis = current_app.extensions["teaching_agent"]["build_defense_analysis"]
    max_message_count = current_app.config["MAX_MESSAGE_COUNT"]
    max_text_length = current_app.config["MAX_TEXT_LENGTH"]
    max_image_bytes = current_app.config["MAX_IMAGE_BYTES"]
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValidationError("请求体必须是 JSON 对象")

        messages = validate_messages(data.get("messages"), max_message_count, max_text_length, max_image_bytes)
        latest_user_message = extract_latest_user_text(messages)
        if not latest_user_message:
            raise ValidationError("请先提供课程项目、课题背景或答辩内容")
        payload = build_defense_analysis(latest_user_message)
        return jsonify({"status": "success", "analysis": payload})
    except ValidationError as exc:
        logger.warning("validation_error error=%s", exc)
        return jsonify({"status": "fail", "error": str(exc)}), 400
    except Exception:
        logger.exception("internal_server_error")
        return jsonify({"status": "fail", "error": "服务器内部错误"}), 500
