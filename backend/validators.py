from __future__ import annotations

import base64
import binascii
import uuid
from typing import Any

from backend.constants import MODEL_CONFIG, SCENE_PROMPTS


class ValidationError(ValueError):
    pass


def validate_model(value: Any) -> str:
    if value not in MODEL_CONFIG:
        raise ValidationError("不支持的模型类型")
    return value


def validate_api_key(value: Any, model: str) -> str:
    if not isinstance(value, str):
        raise ValidationError("API Key 格式错误")
    api_key = value.strip()
    if len(api_key) < 8 or len(api_key) > 200:
        raise ValidationError(f"{model} 的 API Key 长度不合法")
    return api_key


def resolve_api_key(value: Any, model: str, default_api_keys: dict[str, str]) -> str:
    if isinstance(value, str) and value.strip():
        return validate_api_key(value, model)
    default_key = (default_api_keys.get(model) or "").strip()
    if default_key:
        return validate_api_key(default_key, model)
    raise ValidationError(f"{model} 尚未配置可用的 API Key")


def validate_scene_mode(value: Any) -> str:
    if value is None or value == "":
        return "default"
    if not isinstance(value, str):
        raise ValidationError("scene_mode 格式错误")
    scene_mode = value.strip()
    if scene_mode not in SCENE_PROMPTS:
        raise ValidationError("不支持的教学模式")
    return scene_mode


def validate_chat_id(value: Any) -> str:
    if value is None or value == "":
        return str(uuid.uuid4())
    if not isinstance(value, str):
        raise ValidationError("chat_id 格式错误")
    chat_id = value.strip()
    if not chat_id or len(chat_id) > 64:
        raise ValidationError("chat_id 不合法")
    return chat_id


def validate_image(value: Any, max_image_bytes: int) -> str:
    if not isinstance(value, str):
        raise ValidationError("图片数据格式错误")
    image_data = value.strip()
    if not image_data:
        raise ValidationError("图片数据不能为空")
    if not image_data.startswith("data:image/") or ";base64," not in image_data:
        raise ValidationError("图片必须是 base64 Data URL")
    try:
        encoded = image_data.split(",", 1)[1]
        decoded = base64.b64decode(encoded, validate=True)
    except (IndexError, ValueError, binascii.Error):
        raise ValidationError("图片编码无效")
    if len(decoded) > max_image_bytes:
        raise ValidationError("图片不能超过 5MB")
    return image_data


def validate_messages(value: Any, max_message_count: int, max_text_length: int, max_image_bytes: int) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValidationError("messages 不能为空")
    if len(value) > max_message_count:
        raise ValidationError(f"单次请求消息数不能超过 {max_message_count} 条")

    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValidationError("消息格式错误")
        role = item.get("role")
        if role not in {"user", "assistant", "system"}:
            raise ValidationError("消息角色不合法")

        content = item.get("content")
        image = item.get("image")
        if not isinstance(content, str):
            raise ValidationError("消息内容必须为字符串")
        content = content.strip()
        if not content and not image:
            raise ValidationError("文本和图片不能同时为空")
        if len(content) > max_text_length:
            raise ValidationError(f"文本长度不能超过 {max_text_length} 个字符")

        normalized_item: dict[str, Any] = {"role": role, "content": content}
        if image is not None:
            normalized_item["image"] = validate_image(image, max_image_bytes)
        normalized.append(normalized_item)
    return normalized
