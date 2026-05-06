from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.constants import SCENE_PROMPTS
from backend.models import ChatSession


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def extract_latest_user_text(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return (message.get("content") or "").strip()
    return ""


def build_defense_analysis(topic: str) -> dict[str, Any]:
    subject = topic[:80]
    return {
        "opening": f"各位老师好，我的汇报主题是《{subject}》。本项目聚焦实际教学或课程场景中的核心问题，围绕需求分析、方案设计、实现验证与结果评估展开，希望证明该方案在可用性与教学价值上的有效性。",
        "summary": f"该项目围绕“{subject}”展开，核心目标是解决真实教学或课程任务中的痛点问题；方法上通过系统设计、功能实现与效果验证形成完整闭环；最终输出面向课程答辩可展示的成果与改进方向。",
        "questions": [
            "你的选题背景和实际意义是什么？为什么值得做？",
            "你的方案与传统做法相比，核心改进点体现在哪里？",
            "系统或方法设计时，最关键的技术路线是什么？为什么这样选？",
            "你如何验证最终结果是有效的？评价指标或观察依据是什么？",
            "如果继续迭代，你认为当前方案最需要补强的部分是什么？",
        ],
        "scores": [
            {"name": "选题价值", "score": 8, "focus": "是否面向真实问题，应用场景是否清晰"},
            {"name": "方案设计", "score": 8, "focus": "技术路线、功能拆分与实现逻辑是否完整"},
            {"name": "结果展示", "score": 7, "focus": "是否有可运行成果、流程演示与效果说明"},
            {"name": "创新与反思", "score": 7, "focus": "是否能说明亮点、局限与后续优化方向"},
        ],
        "total_score": 30,
        "overall_comment": "整体具备较完整的答辩表达基础，方案主线较清晰，适合课程答辩展示。当前最需要加强的是结果验证的说服力、创新点提炼的明确度，以及面对追问时的标准化回答稳定性。",
        "followups": [
            {"question": "如果老师质疑你的创新性不足，你会如何回应？", "followup": "请从与传统方案对比、具体改进点和实际价值三个层面回答。"},
            {"question": "如果老师追问你的验证方式不充分，你会怎么解释？", "followup": "重点说明评价指标、样例结果和后续补充实验计划。"},
            {"question": "如果老师问项目落地场景，你准备如何展开？", "followup": "可以从目标用户、使用流程、效果提升和推广可行性四点说明。"},
        ],
        "outline": [
            "研究背景与问题定义",
            "项目目标与总体方案",
            "系统设计与核心实现",
            "结果展示与效果验证",
            "创新点、不足与未来改进",
        ],
        "answer_templates": [
            {"scene": "创新点被质疑", "template": "我的创新不只体现在技术名称，而是体现在把已有能力结合到具体教学场景中，并形成了更完整、可运行、可演示的解决方案。"},
            {"scene": "结果说服力不足", "template": "当前结果主要通过功能闭环、页面演示和典型使用场景进行了验证；如果继续完善，我会增加更系统的对比实验和用户反馈数据。"},
            {"scene": "为什么这样选型", "template": "我优先考虑了实现成本、可运行性、课程展示效果和后续扩展性，因此选择了当前这套技术组合。"},
        ],
        "suggestions": [
            "准备 1 分钟版本和 3 分钟版本两套开场陈述，分别对应时间宽松与时间紧张场景。",
            "把“问题背景 - 设计目标 - 方案实现 - 结果验证 - 不足与展望”做成稳定答辩主线。",
            "针对技术选型、效果验证、创新点不足三类问题，提前准备标准回答模板。",
            "尽量准备真实页面截图、核心流程图和关键结果对比，让回答更有说服力。",
        ],
        "teaching_value": {
            "target_users": ["课程教师", "学生", "课程答辩评审"],
            "learning_goals": [
                "帮助学生快速梳理课题背景与研究主线",
                "提升课程项目讲解、演示与答辩表达能力",
                "形成从问题定义到结果验证的完整学习闭环",
            ],
            "classroom_fit": "适合用于课程项目辅导、课后答疑、阶段汇报预演和课程答辩准备。",
        },
        "defense_strategy": {
            "high_frequency_focus": ["研究意义", "方案设计", "结果验证", "创新点", "局限性"],
            "response_structure": ["先给结论", "再讲依据", "最后补充改进计划"],
            "teacher_followup_style": "老师通常会先确认你是否真的理解项目目标，再追问设计取舍、验证依据和创新边界，因此回答时要避免空泛表达。",
        },
        "improvement_plan": [
            {"phase": "短期", "goal": "补强结果说服力", "actions": ["增加对比样例", "整理关键指标", "准备一页结果总结图"]},
            {"phase": "中期", "goal": "提升教学适配度", "actions": ["补充典型教学场景", "设计学生使用流程", "总结教师使用价值"]},
            {"phase": "长期", "goal": "形成可持续迭代产品", "actions": ["沉淀通用答辩问答库", "扩展课程模式模板", "增加真实反馈闭环"]},
        ],
        "demo_script": [
            "先用一句话说明课题背景和要解决的问题。",
            "展示系统首页或主流程，说明核心功能入口。",
            "演示一次典型任务闭环：输入问题、系统响应、结果分析。",
            "补充结果价值、教学意义和后续优化方向。",
        ],
        "qa_checklist": [
            "是否能在 30 秒内解释清楚选题价值？",
            "是否准备好了技术路线选择理由？",
            "是否有证据支撑结果有效性？",
            "是否能明确说出系统局限和下一步计划？",
        ],
    }


def trim_messages(messages: list[dict[str, Any]], max_message_count: int) -> list[dict[str, Any]]:
    return messages[-max_message_count:]


def with_scene_prompt(messages: list[dict[str, Any]], scene_mode: str) -> list[dict[str, Any]]:
    prompt = SCENE_PROMPTS.get(scene_mode, SCENE_PROMPTS["default"])
    system_message = {"role": "system", "content": prompt}
    if messages and messages[0].get("role") == "system":
        return [system_message, *messages[1:]]
    return [system_message, *messages]


def comparable_message(message: dict[str, Any]) -> dict[str, Any]:
    comparable = {
        "role": message.get("role"),
        "content": message.get("content", ""),
    }
    if message.get("image"):
        comparable["image"] = message["image"]
    return comparable


def strip_message_metadata(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [comparable_message(message) for message in messages]


def derive_title(messages: list[dict[str, Any]]) -> str:
    for message in messages:
        if message.get("role") == "user":
            text = (message.get("content") or "").strip()
            if text:
                return text[:20] + ("..." if len(text) > 20 else "")
            if message.get("image"):
                return "图片答疑"
    return "新对话"


def upsert_chat(chat_id: str, incoming_messages: list[dict[str, Any]], reply: str, fetch_chat_by_id, save_chat) -> ChatSession:
    now = utc_now()
    chat = fetch_chat_by_id(chat_id)
    if chat is None:
        chat = ChatSession(
            chat_id=chat_id,
            title=derive_title(incoming_messages),
            created_at=now,
            updated_at=now,
            messages=[],
        )
    else:
        chat.updated_at = now

    stored_comparable = strip_message_metadata(chat.messages)
    incoming_comparable = strip_message_metadata(incoming_messages)
    deduplicated = incoming_messages.copy()
    if stored_comparable and incoming_comparable[: len(stored_comparable)] == stored_comparable:
        deduplicated = incoming_messages[len(stored_comparable):]

    chat.messages.extend(deduplicated)
    chat.messages.append({"role": "assistant", "content": reply, "time": now})
    if not chat.title or chat.title == "新对话":
        chat.title = derive_title(chat.messages)
    save_chat(chat)
    return chat


def serialize_chat_summary(chat: ChatSession) -> dict[str, Any]:
    last_message_preview = ""
    for message in reversed(chat.messages):
        if message.get("role") != "system":
            last_message_preview = (message.get("content") or "").strip()
            if last_message_preview:
                break
    return {
        "chat_id": chat.chat_id,
        "title": chat.title,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
        "message_count": len(chat.messages),
        "last_message_preview": last_message_preview[:50] + ("..." if len(last_message_preview) > 50 else ""),
    }


def serialize_chat(chat: ChatSession) -> dict[str, Any]:
    return {
        "chat_id": chat.chat_id,
        "title": chat.title,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
        "messages": [message for message in chat.messages if message.get("role") != "system"],
    }
