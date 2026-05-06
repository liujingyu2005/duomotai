export const state = {
    currentChatId: null,
    chats: [],
    currentChat: null,
    pendingImage: null,
    loading: false,
    sceneMode: "default",
    defaultKeyStatus: {},
    creatingNewChat: false,
    abortController: null,
    defensePromptInserted: false,
    lastManualInput: "",
    stoppedRequest: false,
};
