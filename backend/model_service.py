from __future__ import annotations

import json
from typing import Any

import requests

from backend.constants import MODEL_CONFIG
from backend.validators import ValidationError


def to_ndjson(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False) + "\n"


def chunk_text(text: str, chunk_size: int) -> list[str]:
    if not text:
        return [""]
    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]


def to_openai_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in messages:
        content = item["content"]
        image = item.get("image")
        if image:
            result.append(
                {
                    "role": item["role"],
                    "content": [
                        {"type": "text", "text": content or "请解析这张题目图片。"},
                        {"type": "image_url", "image_url": {"url": image}},
                    ],
                }
            )
        else:
            result.append({"role": item["role"], "content": content})
    return result


def to_qwen_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in messages:
        image = item.get("image")
        content = item["content"] or "请解析这张题目图片。"
        if image:
            result.append(
                {
                    "role": item["role"],
                    "content": [
                        {"text": content},
                        {"image": image},
                    ],
                }
            )
        else:
            result.append({"role": item["role"], "content": content})
    return result


def extract_qwen_text(body: dict[str, Any]) -> str:
    output = body.get("output")
    if not isinstance(output, dict):
        return ""

    text = output.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    choices = output.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return ""

    message = first_choice.get("message")
    if not isinstance(message, dict):
        return ""

    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                part = item.get("text") or item.get("content")
                if isinstance(part, str) and part.strip():
                    text_parts.append(part.strip())
        return "\n".join(text_parts).strip()
    return ""


def extract_qwen_error_message(response: requests.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return f"通义千问调用失败：HTTP {response.status_code}"

    message = body.get("message") or body.get("error_message")
    code = body.get("code") or body.get("error_code")
    if response.status_code in {401, 403}:
        return f"通义千问鉴权失败：{message or code or '请检查 API Key 或账号权限'}"
    if response.status_code in {429, 502, 503}:
        return f"通义千问调用受限：{message or code or '可能是额度不足、限流或服务繁忙'}"
    return f"通义千问调用失败：{message or code or f'HTTP {response.status_code}'}"


def call_model_api(model: str, api_key: str, messages: list[dict[str, Any]], request_timeout: int) -> str:
    config = MODEL_CONFIG[model]
    headers = {"Content-Type": "application/json"}

    if config["type"] == "qwen":
        headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": config["model"],
            "input": {"messages": to_qwen_messages(messages)},
            "parameters": {"temperature": 0.5},
        }
    else:
        headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": config["model"],
            "messages": to_openai_messages(messages),
            "temperature": 0.5,
            "stream": False,
        }

    response = requests.post(
        config["url"],
        headers=headers,
        json=payload,
        timeout=request_timeout,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        if config["type"] == "qwen":
            detail = extract_qwen_error_message(response)
            raise ValidationError(detail) from exc
        raise

    body = response.json()

    if config["type"] == "qwen":
        parsed_text = extract_qwen_text(body)
        if parsed_text:
            return parsed_text
        raise ValidationError("通义千问返回数据格式异常，请检查接口版本或账号权限")

    try:
        return body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError):
        raise ValidationError("模型返回数据格式异常")
