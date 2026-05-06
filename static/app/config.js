export const STORAGE_KEYS = {
    currentModel: "teaching-agent.currentModel",
    apiKeys: "teaching-agent.apiKeys",
    currentChatId: "teaching-agent.currentChatId",
    sceneMode: "teaching-agent.sceneMode",
};

export const SCENE_MODE_LABELS = {
    default: "通用答疑",
    lecture: "讲解模式",
    practice: "练习模式",
    defense: "答辩模式",
};

export const DEFENSE_PROMPT = "请模拟课程答辩现场。先根据我的题目背景生成 5 个由浅入深的问题；每次我回答后，请继续追问，并从研究意义、方法设计、实验结果、创新点、局限性五个角度给出改进建议。";
