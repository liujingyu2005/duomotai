import { elements } from "./dom.js";
import { state } from "./state.js";
import { SCENE_MODE_LABELS } from "./config.js";
import { escapeHtml, formatRelativeTime, formatTimeLabel } from "./utils.js";

export function renderChatList(loadChat, deleteChat) {
    if (!elements.chatList) {
        return;
    }
    elements.chatList.innerHTML = "";

    if (state.chats.length === 0) {
        const empty = document.createElement("div");
        empty.className = "helper-text";
        empty.textContent = "暂无历史会话，点击“新建对话”开始使用。";
        elements.chatList.appendChild(empty);
        return;
    }

    state.chats.forEach((chat) => {
        const item = document.createElement("div");
        item.className = `chat-item ${chat.chat_id === state.currentChatId ? "active" : ""}`;

        const title = document.createElement("div");
        title.className = "chat-item-title";
        title.textContent = chat.title;

        const meta = document.createElement("div");
        meta.className = "chat-item-meta";
        meta.textContent = `消息 ${chat.message_count} 条 · ${formatRelativeTime(chat.updated_at)}`;

        const preview = document.createElement("div");
        preview.className = "chat-item-meta";
        preview.textContent = chat.last_message_preview || "点击继续当前学习对话";

        const actions = document.createElement("div");
        actions.className = "chat-item-actions";

        const openBtn = document.createElement("button");
        openBtn.className = "ghost-btn";
        openBtn.type = "button";
        openBtn.textContent = "打开";
        openBtn.addEventListener("click", () => void loadChat(chat.chat_id));

        const deleteBtn = document.createElement("button");
        deleteBtn.className = "danger-btn";
        deleteBtn.type = "button";
        deleteBtn.textContent = "删除";
        deleteBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            void deleteChat(chat.chat_id);
        });

        actions.append(openBtn, deleteBtn);
        item.append(title, meta, preview, actions);
        item.addEventListener("click", () => void loadChat(chat.chat_id));
        elements.chatList.appendChild(item);
    });
}

export function updateChatHeader(chat, updateDefensePanelVisibility, updateHeaderBadges) {
    if (!chat) {
        elements.chatTitle.textContent = "新对话";
        elements.chatMeta.textContent = `${SCENE_MODE_LABELS[state.sceneMode] || "通用答疑"} · 准备开始提问`;
        updateHeaderBadges();
        updateDefensePanelVisibility();
        return;
    }
    elements.chatTitle.textContent = chat.title || "新对话";
    elements.chatMeta.textContent = `消息 ${Array.isArray(chat.messages) ? chat.messages.length : 0} 条 · 最近更新 ${formatRelativeTime(chat.updated_at)}`;
    updateHeaderBadges();
    updateDefensePanelVisibility();
}

export function renderMessages(messages) {
    elements.messages.innerHTML = "";
    if (!Array.isArray(messages) || messages.length === 0) {
        renderEmptyState();
        return;
    }

    messages.forEach((message, index) => {
        const previousMessage = index > 0 ? messages[index - 1] : null;
        elements.messages.appendChild(buildMessageNode(message, previousMessage));
    });
    elements.messages.scrollTop = elements.messages.scrollHeight;
}

function buildMessageNode(message, previousMessage = null) {
    const wrapper = document.createElement("div");
    const role = message.role === "user" ? "user" : "assistant";
    wrapper.className = `message ${role}`;
    if (message.pending) {
        wrapper.classList.add("pending");
    }
    const isGrouped = previousMessage && previousMessage.role === message.role;
    if (isGrouped) {
        wrapper.classList.add("grouped");
    }

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = role === "user" ? "你" : "AI";
    if (isGrouped) {
        avatar.classList.add("hidden");
    }

    const body = document.createElement("div");
    body.className = "message-body";

    const meta = document.createElement("div");
    meta.className = "message-meta";
    meta.textContent = `${role === "user" ? "你" : "AI 教学助手"}${message.time ? ` · ${formatTimeLabel(message.time)}` : ""}`;
    if (isGrouped) {
        meta.classList.add("hidden");
    }
    body.appendChild(meta);

    const text = document.createElement("div");
    text.className = "message-content";
    renderMessageContent(text, message, role);
    body.appendChild(text);

    if (message.image) {
        const image = document.createElement("img");
        image.className = "message-image";
        image.src = message.image;
        image.alt = "用户上传的题目图片";
        body.appendChild(image);
    }

    wrapper.append(avatar, body);
    return wrapper;
}

function renderMessageContent(container, message, role) {
    const content = message.content || (message.image ? "[图片消息]" : "");
    if (role === "assistant" && window.marked && typeof window.marked.parse === "function") {
        container.innerHTML = window.marked.parse(content, { breaks: true });
        return;
    }
    container.textContent = content;
}

export function renderEmptyState() {
    elements.messages.innerHTML = "";
    if (elements.welcomePanel) {
        elements.messages.appendChild(elements.welcomePanel);
        return;
    }
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "你可以输入文本问题，或上传题目图片让 AI 进行解析。";
    elements.messages.appendChild(empty);
}

export function renderInlineError(message) {
    const node = document.createElement("div");
    node.className = "message assistant error";
    node.textContent = message;
    elements.messages.appendChild(node);
    elements.messages.scrollTop = elements.messages.scrollHeight;
}

export function renderSystemMessage(message) {
    elements.messages.innerHTML = "";
    const node = document.createElement("div");
    node.className = "message assistant error";
    node.textContent = message;
    elements.messages.appendChild(node);
}

export function highlightActiveChat() {
    document.querySelectorAll(".chat-item").forEach((item, index) => {
        const chat = state.chats[index];
        item.classList.toggle("active", chat?.chat_id === state.currentChatId);
    });
}

export function renderImagePreview(name, dataUrl, clearPendingImage) {
    elements.imagePreview.innerHTML = "";
    elements.imagePreview.classList.remove("hidden");

    const image = document.createElement("img");
    image.className = "message-image";
    image.src = dataUrl;
    image.alt = name;

    const text = document.createElement("div");
    text.textContent = name;

    const removeBtn = document.createElement("button");
    removeBtn.className = "ghost-btn";
    removeBtn.type = "button";
    removeBtn.textContent = "移除图片";
    removeBtn.addEventListener("click", clearPendingImage);

    elements.imagePreview.append(image, text, removeBtn);
}

export function renderDefenseAnalysis(analysis, focus = "", updateDefensePanelVisibility) {
    updateDefensePanelVisibility();
    elements.defenseOverall.innerHTML = `<strong>总分：${escapeHtml(analysis.total_score || "-")}/40</strong><br>${escapeHtml(analysis.overall_comment || "")}`;
    elements.defenseOpening.textContent = analysis.opening || "";
    elements.defenseSummary.textContent = analysis.summary || "";
    elements.defenseQuestions.innerHTML = renderList(analysis.questions || []);
    elements.defenseScores.innerHTML = renderScoreList(analysis.scores || []);
    elements.defenseFollowups.innerHTML = renderFollowupList(analysis.followups || []);
    elements.defenseOutline.innerHTML = renderList(analysis.outline || []);
    elements.defenseTemplates.innerHTML = renderTemplateList(analysis.answer_templates || []);
    elements.defenseSuggestions.innerHTML = renderList(analysis.suggestions || []);

    // 新增字段渲染
    const tv = analysis.teaching_value || {};
    elements.defenseTeachingValue.innerHTML = `
        <p><strong>适用对象</strong>：${renderInlineList(tv.target_users || [])}</p>
        <p><strong>学习目标</strong>：</p>${renderList(tv.learning_goals || [])}
        <p><strong>课堂适配</strong>：${escapeHtml(tv.classroom_fit || "")}</p>
    `;

    const ds = analysis.defense_strategy || {};
    elements.defenseStrategy.innerHTML = `
        <p><strong>高频关注点</strong>：${renderInlineList(ds.high_frequency_focus || [])}</p>
        <p><strong>回答结构</strong>：${renderInlineList(ds.response_structure || [])}</p>
        <p><strong>老师追问风格</strong>：${escapeHtml(ds.teacher_followup_style || "")}</p>
    `;

    const ip = analysis.improvement_plan || [];
    elements.defenseImprovementPlan.innerHTML = ip.map(item => 
        `<div class="improvement-phase">
            <strong>${escapeHtml(item.phase || "")}：${escapeHtml(item.goal || "")}</strong>
            <ul>${(item.actions || []).map(act => `<li>${escapeHtml(act)}</li>`).join("")}</ul>
        </div>`
    ).join("");

    elements.defenseDemoScript.innerHTML = renderList(analysis.demo_script || []);

    elements.defenseQAChecklist.innerHTML = renderList(analysis.qa_checklist || [], "checkbox");

    if (focus === "opening") {
        elements.defenseOpening.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
}

function renderList(items, type = "ol") {
    const tag = type === "checkbox" ? "ul" : "ol";
    const inner = items.map((item) => {
        if (type === "checkbox") {
            return `<li><input type="checkbox" disabled> ${escapeHtml(item)}</li>`;
        }
        return `<li>${escapeHtml(item)}</li>`;
    }).join("");
    return `<${tag}>${inner}</${tag}>`;
}

function renderInlineList(items) {
    return items.length ? items.map(escapeHtml).join("、") : "";
}

function renderScoreList(items) {
    return `<ul>${items.map((item) => `<li><strong>${escapeHtml(item.name || "")}</strong>${item.score ? `（${escapeHtml(item.score)}/10）` : ""}：${escapeHtml(item.focus || "")}</li>`).join("")}</ul>`;
}

function renderFollowupList(items) {
    return `<ul>${items.map((item) => `<li><strong>${escapeHtml(item.question || "")}</strong><br>${escapeHtml(item.followup || "")}</li>`).join("")}</ul>`;
}

function renderTemplateList(items) {
    return `<ul>${items.map((item) => `<li><strong>${escapeHtml(item.scene || "")}</strong>：${escapeHtml(item.template || "")}</li>`).join("")}</ul>`;
}
