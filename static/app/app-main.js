import { DEFENSE_PROMPT, SCENE_MODE_LABELS, STORAGE_KEYS } from "./config.js";
import { elements } from "./dom.js";
import { state } from "./state.js";
import { fetchJson, fileToDataUrl } from "./utils.js";
import {
    highlightActiveChat,
    renderChatList,
    renderDefenseAnalysis,
    renderEmptyState,
    renderImagePreview,
    renderInlineError,
    renderMessages,
    renderSystemMessage,
    updateChatHeader,
} from "./renderers.js";

function init() {
    if (!elements.messages || !elements.messageInput || !elements.modelSelect || !elements.sceneModeSelect) {
        return;
    }
    restoreConfig();
    bindEvents();
    bindPromptActions();
    updateHeaderBadges();
    updateApiKeyStatus();
    renderEmptyState();
    void loadDefaultKeyStatus();
    void refreshChats();
}

function bindEvents() {
    elements.newChatBtn.addEventListener("click", createNewChat);
    elements.refreshChatsBtn.addEventListener("click", () => void refreshChats());
    elements.saveConfigBtn.addEventListener("click", saveConfig);
    elements.clearApiKeyBtn.addEventListener("click", clearCustomApiKey);
    elements.sendBtn.addEventListener("click", () => void sendMessage());
    elements.renameChatBtn.addEventListener("click", () => void renameCurrentChat());
    elements.deleteChatBtn.addEventListener("click", () => void deleteCurrentChat());
    elements.insertDefensePromptBtn.addEventListener("click", insertDefensePrompt);
    elements.generateDefenseAnalysisBtn.addEventListener("click", () => void generateDefenseAnalysis());
    elements.imageInput.addEventListener("change", handleImageSelect);
    elements.modelSelect.addEventListener("change", handleModelChange);
    elements.sceneModeSelect.addEventListener("change", handleSceneModeChange);
    elements.messageInput.addEventListener("input", handleComposerInput);
    elements.messageInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            void sendMessage();
        }
    });
    elements.clearInputBtn.addEventListener("click", clearComposer);
    elements.stopBtn.addEventListener("click", stopGeneration);
}

function bindPromptActions() {
    document.querySelectorAll("[data-prompt]").forEach((node) => {
        node.addEventListener("click", () => {
            const prompt = node.getAttribute("data-prompt") || "";
            const nextSceneMode = node.getAttribute("data-scene-mode") || "default";
            const action = node.getAttribute("data-prompt-action") || "fill";
            applyQuickPrompt({ prompt, nextSceneMode, action });
        });
    });

    document.querySelectorAll("[data-defense-action]").forEach((node) => {
        node.addEventListener("click", () => {
            void generateDefenseAnalysis(node.getAttribute("data-defense-action") || "");
        });
    });
}

function restoreConfig() {
    const currentModel = localStorage.getItem(STORAGE_KEYS.currentModel) || "deepseek";
    const sceneMode = localStorage.getItem(STORAGE_KEYS.sceneMode) || "default";
    const apiKeys = readApiKeys();
    const currentChatId = localStorage.getItem(STORAGE_KEYS.currentChatId);

    elements.modelSelect.value = currentModel;
    elements.sceneModeSelect.value = sceneMode;
    elements.apiKeyInput.value = apiKeys[currentModel] || "";
    state.currentChatId = currentChatId || null;
    state.sceneMode = sceneMode;
}

function readApiKeys() {
    try {
        const raw = localStorage.getItem(STORAGE_KEYS.apiKeys);
        return raw ? JSON.parse(raw) : {};
    } catch {
        return {};
    }
}

function saveConfig() {
    const currentModel = elements.modelSelect.value;
    const sceneMode = elements.sceneModeSelect.value;
    const apiKeys = readApiKeys();
    const customKey = elements.apiKeyInput.value.trim();
    if (customKey) {
        apiKeys[currentModel] = customKey;
    } else {
        delete apiKeys[currentModel];
    }
    localStorage.setItem(STORAGE_KEYS.currentModel, currentModel);
    localStorage.setItem(STORAGE_KEYS.sceneMode, sceneMode);
    localStorage.setItem(STORAGE_KEYS.apiKeys, JSON.stringify(apiKeys));
    state.sceneMode = sceneMode;
    updateHeaderBadges();
    updateApiKeyStatus();
    setStatus(customKey ? "自定义 API 已保存到本地浏览器" : "已清除自定义 API，优先使用默认 API");
}

function handleModelChange() {
    const currentModel = elements.modelSelect.value;
    const apiKeys = readApiKeys();
    localStorage.setItem(STORAGE_KEYS.currentModel, currentModel);
    elements.apiKeyInput.value = apiKeys[currentModel] || "";
    updateApiKeyStatus();
    updateHeaderBadges();
}

function handleSceneModeChange() {
    state.sceneMode = elements.sceneModeSelect.value || "default";
    localStorage.setItem(STORAGE_KEYS.sceneMode, state.sceneMode);
    if (state.sceneMode !== "defense") {
        state.defensePromptInserted = false;
    }
    updateHeaderBadges();
    updateDefensePanelVisibility();
    updateDefensePromptButton();
}

function clearCustomApiKey() {
    const currentModel = elements.modelSelect.value;
    const apiKeys = readApiKeys();
    delete apiKeys[currentModel];
    localStorage.setItem(STORAGE_KEYS.apiKeys, JSON.stringify(apiKeys));
    elements.apiKeyInput.value = "";
    updateApiKeyStatus();
    setStatus("已清除自定义 API，当前将优先使用默认 API");
}

async function loadDefaultKeyStatus() {
    try {
        const response = await fetchJson("/api/config/default-keys");
        state.defaultKeyStatus = response.items || {};
        updateApiKeyStatus();
    } catch {
        state.defaultKeyStatus = {};
        updateApiKeyStatus("无法读取默认 API 配置状态");
    }
}

function updateApiKeyStatus(fallbackMessage = "") {
    if (!elements.apiKeyStatus) {
        return;
    }
    const currentModel = elements.modelSelect.value;
    const apiKeys = readApiKeys();
    const hasCustomKey = Boolean((apiKeys[currentModel] || "").trim());
    const hasDefaultKey = Boolean(state.defaultKeyStatus[currentModel]);
    if (hasCustomKey) {
        elements.apiKeyStatus.textContent = "当前使用浏览器本地保存的自定义 API。";
        return;
    }
    if (hasDefaultKey) {
        elements.apiKeyStatus.textContent = "当前模型已配置本机默认 API，可直接使用。";
        return;
    }
    elements.apiKeyStatus.textContent = fallbackMessage || "当前模型尚未配置默认 API，如需使用请填写自定义 API。";
}

function createNewChat() {
    state.creatingNewChat = true;
    state.currentChatId = null;
    state.currentChat = null;
    localStorage.removeItem(STORAGE_KEYS.currentChatId);
    clearComposer({ preserveStatus: true });
    updateChatHeader(null, updateDefensePanelVisibility, updateHeaderBadges);
    renderEmptyState();
    highlightActiveChat();
    resetDefenseAnalysis();
    setStatus("已创建空白会话");
}

async function refreshChats() {
    try {
        const response = await fetchJson("/api/chats");
        state.chats = Array.isArray(response.items) ? response.items : [];
        renderChatList(loadChat, deleteChat);

        if (state.creatingNewChat) {
            highlightActiveChat();
            return;
        }

        if (state.currentChatId) {
            const exists = state.chats.some((item) => item.chat_id === state.currentChatId);
            if (exists) {
                await loadChat(state.currentChatId);
                return;
            }
        }

        if (state.chats.length > 0) {
            const fallbackChatId = state.currentChatId || state.chats[0].chat_id;
            await loadChat(fallbackChatId);
        } else {
            createNewChat();
        }
    } catch (error) {
        renderSystemMessage(error.message || "加载会话失败");
        setStatus("加载会话失败");
    }
}

async function loadChat(chatId) {
    try {
        const chat = await fetchJson(`/api/chats/${encodeURIComponent(chatId)}`);
        state.creatingNewChat = false;
        state.currentChatId = chat.chat_id;
        state.currentChat = chat;
        localStorage.setItem(STORAGE_KEYS.currentChatId, chat.chat_id);
        updateChatHeader(chat, updateDefensePanelVisibility, updateHeaderBadges);
        renderMessages(chat.messages || []);
        highlightActiveChat();
        updateDefensePanelVisibility();
        setStatus("会话已加载");
    } catch (error) {
        setStatus(error.message || "加载会话失败");
    }
}

async function sendMessage() {
    if (state.loading) {
        return;
    }

    const content = elements.messageInput.value.trim();
    const image = state.pendingImage;
    const model = elements.modelSelect.value;
    const apiKeys = readApiKeys();
    const apiKey = (apiKeys[model] || elements.apiKeyInput.value || "").trim();

    if (!content && !image) {
        setStatus("请输入文本或上传图片");
        return;
    }
    if (!apiKey && !state.defaultKeyStatus[model]) {
        setStatus("当前模型既没有自定义 API，也没有默认 API，请先配置其一");
        return;
    }

    saveConfig();

    const messages = buildOutgoingMessages(content, image);
    const history = state.currentChat?.messages || [];
    const payload = {
        model,
        scene_mode: state.sceneMode,
        chat_id: state.currentChatId,
        stream: true,
        messages: [...history, ...messages],
    };
    if (apiKey) {
        payload.api_key = apiKey;
    }

    state.loading = true;
    state.stoppedRequest = false;
    state.abortController = new AbortController();
    setLoadingState(true);

    const optimistic = [...history, ...messages];
    renderMessages([...optimistic, buildPendingAssistantMessage()]);

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            signal: state.abortController.signal,
            body: JSON.stringify(payload),
        });
        await consumeChatStream(response, optimistic);
    } catch (error) {
        renderMessages(optimistic);
        if (error.name === "AbortError") {
            renderInlineError("本次生成已终止");
            setStatus("已终止当前生成");
        } else {
            renderInlineError(error.message || "发送失败");
            setStatus(error.message || "发送失败");
        }
    } finally {
        state.abortController = null;
        state.loading = false;
        setLoadingState(false);
    }
}

function buildOutgoingMessages(content, image) {
    return [{
        role: "user",
        content,
        ...(image ? { image } : {}),
    }];
}

async function refreshChatListOnly() {
    const response = await fetchJson("/api/chats");
    state.chats = Array.isArray(response.items) ? response.items : [];
    renderChatList(loadChat, deleteChat);
    highlightActiveChat();
}

async function renameCurrentChat() {
    if (!state.currentChatId) {
        setStatus("当前没有可重命名的会话");
        return;
    }
    const title = window.prompt("请输入新的会话标题", state.currentChat?.title || "");
    if (title === null) {
        return;
    }
    const nextTitle = title.trim();
    if (!nextTitle) {
        setStatus("标题不能为空");
        return;
    }

    try {
        const response = await fetchJson(`/api/chats/${encodeURIComponent(state.currentChatId)}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title: nextTitle }),
        });
        state.currentChat = response.chat;
        updateChatHeader(state.currentChat, updateDefensePanelVisibility, updateHeaderBadges);
        await refreshChatListOnly();
        setStatus("重命名成功");
    } catch (error) {
        setStatus(error.message || "重命名失败");
    }
}

async function deleteCurrentChat() {
    if (!state.currentChatId) {
        setStatus("当前没有可删除的会话");
        return;
    }
    await deleteChat(state.currentChatId);
}

async function deleteChat(chatId) {
    const confirmed = window.confirm("确认删除该会话吗？此操作不可恢复。");
    if (!confirmed) {
        return;
    }

    try {
        await fetchJson(`/api/chats/${encodeURIComponent(chatId)}`, { method: "DELETE" });
        if (state.currentChatId === chatId) {
            state.currentChatId = null;
            state.currentChat = null;
            localStorage.removeItem(STORAGE_KEYS.currentChatId);
        }
        await refreshChats();
        setStatus("会话已删除");
    } catch (error) {
        setStatus(error.message || "删除失败");
    }
}

async function handleImageSelect(event) {
    const file = event.target.files?.[0];
    if (!file) {
        clearPendingImage();
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        setStatus("图片不能超过 5MB");
        event.target.value = "";
        return;
    }

    const dataUrl = await fileToDataUrl(file);
    state.pendingImage = dataUrl;
    renderImagePreview(file.name, dataUrl, clearPendingImage);
    setStatus(`已选择图片：${file.name}`);
}

function clearPendingImage() {
    state.pendingImage = null;
    elements.imageInput.value = "";
    elements.imagePreview.innerHTML = "";
    elements.imagePreview.classList.add("hidden");
}

function clearComposer(options = {}) {
    elements.messageInput.value = "";
    clearPendingImage();
    state.defensePromptInserted = false;
    state.lastManualInput = "";
    updateDefensePromptButton();
    if (!options.preserveStatus) {
        setStatus("已清空输入内容");
    }
}

function setLoadingState(loading) {
    if (elements.sendBtn) {
        elements.sendBtn.disabled = loading;
        elements.sendBtn.textContent = loading ? "发送中..." : "发送";
        elements.sendBtn.classList.toggle("is-loading", loading);
    }
    elements.stopBtn?.classList.toggle("hidden", !loading);
    elements.messages?.classList.toggle("is-loading", loading);
}

function setStatus(message) {
    if (elements.statusText) {
        elements.statusText.textContent = message;
    }
}

function updateHeaderBadges() {
    const modelLabel = elements.modelSelect?.options[elements.modelSelect.selectedIndex]?.text || "当前模型";
    if (elements.activeModelBadge) {
        elements.activeModelBadge.textContent = modelLabel;
    }
    if (elements.activeModeBadge) {
        elements.activeModeBadge.textContent = SCENE_MODE_LABELS[state.sceneMode] || "通用答疑";
    }
}

function updateDefensePanelVisibility() {
    if (!elements.defensePanel) {
        return;
    }
    const shouldShow = state.sceneMode === "defense";
    elements.defensePanel.classList.toggle("hidden", !shouldShow);
    if (!shouldShow) {
        resetDefenseAnalysis();
    }
}

function resetDefenseAnalysis() {
    if (elements.defenseOverall) {
        elements.defenseOverall.innerHTML = "";
    }
    if (elements.defenseOpening) {
        elements.defenseOpening.textContent = "";
    }
    if (elements.defenseSummary) {
        elements.defenseSummary.textContent = "";
    }
    if (elements.defenseQuestions) {
        elements.defenseQuestions.innerHTML = "";
    }
    if (elements.defenseScores) {
        elements.defenseScores.innerHTML = "";
    }
    if (elements.defenseFollowups) {
        elements.defenseFollowups.innerHTML = "";
    }
    if (elements.defenseOutline) {
        elements.defenseOutline.innerHTML = "";
    }
    if (elements.defenseTeachingValue) {
        elements.defenseTeachingValue.innerHTML = "";
    }
    if (elements.defenseStrategy) {
        elements.defenseStrategy.innerHTML = "";
    }
    if (elements.defenseImprovementPlan) {
        elements.defenseImprovementPlan.innerHTML = "";
    }
    if (elements.defenseDemoScript) {
        elements.defenseDemoScript.innerHTML = "";
    }
    if (elements.defenseQAChecklist) {
        elements.defenseQAChecklist.innerHTML = "";
    }
    if (elements.defenseTemplates) {
        elements.defenseTemplates.innerHTML = "";
    }
    if (elements.defenseSuggestions) {
        elements.defenseSuggestions.innerHTML = "";
    }
}

function insertDefensePrompt() {
    if (state.defensePromptInserted && elements.messageInput.value.trim() === DEFENSE_PROMPT) {
        elements.messageInput.value = state.lastManualInput;
        state.defensePromptInserted = false;
        if (state.sceneMode === "defense") {
            elements.sceneModeSelect.value = "default";
            state.sceneMode = "default";
            localStorage.setItem(STORAGE_KEYS.sceneMode, state.sceneMode);
            updateHeaderBadges();
            updateDefensePanelVisibility();
        }
        updateDefensePromptButton();
        elements.messageInput.focus();
        setStatus("已关闭答辩提示词");
        return;
    }
    state.lastManualInput = elements.messageInput.value;
    elements.messageInput.value = DEFENSE_PROMPT;
    elements.sceneModeSelect.value = "defense";
    state.sceneMode = "defense";
    state.defensePromptInserted = true;
    localStorage.setItem(STORAGE_KEYS.sceneMode, state.sceneMode);
    updateHeaderBadges();
    updateDefensePanelVisibility();
    updateDefensePromptButton();
    elements.messageInput.focus();
    setStatus("已插入答辩模式提示词");
}

function applyQuickPrompt({ prompt, nextSceneMode, action }) {
    if (action === "new-chat") {
        createNewChat();
        const chatListPanel = document.getElementById("chatList");
        chatListPanel?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
    elements.sceneModeSelect.value = nextSceneMode;
    state.sceneMode = nextSceneMode;
    localStorage.setItem(STORAGE_KEYS.sceneMode, state.sceneMode);
    updateHeaderBadges();
    updateDefensePanelVisibility();
    elements.messageInput.value = prompt;
    state.defensePromptInserted = nextSceneMode === "defense";
    state.lastManualInput = "";
    updateDefensePromptButton();
    elements.messageInput.focus();
    scrollToComposer();
    flashComposer();
    setStatus(action === "new-chat" ? "已进入新会话并填入提示词" : "已填入快捷提示词");
}

function handleComposerInput() {
    if (elements.messageInput.value.trim() !== DEFENSE_PROMPT) {
        state.defensePromptInserted = false;
        state.lastManualInput = elements.messageInput.value;
        updateDefensePromptButton();
    }
}

function updateDefensePromptButton() {
    if (!elements.insertDefensePromptBtn) {
        return;
    }
    elements.insertDefensePromptBtn.textContent = state.defensePromptInserted ? "关闭答辩提示" : "插入答辩提示";
}

function stopGeneration() {
    if (!state.loading || !state.abortController) {
        setStatus("当前没有可终止的生成任务");
        return;
    }
    state.stoppedRequest = true;
    renderMessages(state.currentChat?.messages || buildOutgoingMessages(elements.messageInput.value.trim(), state.pendingImage));
    renderInlineError("本次生成已终止");
    state.loading = false;
    setLoadingState(false);
    state.abortController.abort();
}

function buildPendingAssistantMessage() {
    return {
        role: "assistant",
        content: "正在思考中...",
        pending: true,
        time: new Date().toISOString(),
    };
}

async function consumeChatStream(response, optimistic) {
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || `请求失败：${response.status}`);
    }
    if (!response.body) {
        throw new Error("当前浏览器不支持流式响应");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let streamedContent = "";

    while (true) {
        const { value, done } = await reader.read();
        if (done) {
            break;
        }
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
            if (!line.trim()) {
                continue;
            }
            const event = JSON.parse(line);
            if (event.type === "delta") {
                streamedContent = event.content || `${streamedContent}${event.delta || ""}`;
                renderMessages([...optimistic, { role: "assistant", content: streamedContent, time: new Date().toISOString(), pending: true }]);
                setStatus("正在生成回答...");
                continue;
            }
            if (event.type === "error") {
                throw new Error(event.error || "发送失败");
            }
            if (event.type === "done") {
                state.currentChat = event.chat;
                state.currentChatId = event.chat.chat_id;
                localStorage.setItem(STORAGE_KEYS.currentChatId, state.currentChatId);
                updateChatHeader(state.currentChat, updateDefensePanelVisibility, updateHeaderBadges);
                renderMessages(state.currentChat.messages || []);
                clearComposer();
                await refreshChatListOnly();
                setStatus("回答已生成");
            }
        }
    }
}

function scrollToComposer() {
    const composer = document.querySelector(".floating-composer");
    composer?.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function flashComposer() {
    const composer = document.querySelector(".floating-composer");
    if (!composer) {
        return;
    }
    composer.classList.add("composer-flash");
    window.setTimeout(() => composer.classList.remove("composer-flash"), 900);
}

async function generateDefenseAnalysis(focus = "") {
    const messages = state.currentChat?.messages || buildOutgoingMessages(elements.messageInput.value.trim(), state.pendingImage);
    const latestMessages = Array.isArray(messages) ? messages : [];
    if (!latestMessages.length) {
        setStatus("请先输入你的课题、项目背景或答辩内容");
        return;
    }

    try {
        const response = await fetchJson("/api/defense-analysis", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ messages: latestMessages }),
        });
        renderDefenseAnalysis(response.analysis, focus, updateDefensePanelVisibility);
        setStatus("答辩分析已生成");
    } catch (error) {
        setStatus(error.message || "答辩分析生成失败");
    }
}

window.addEventListener("DOMContentLoaded", init);
