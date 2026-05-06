from __future__ import annotations

MODEL_CONFIG = {
    "deepseek": {
        "url": "https://api.deepseek.com/chat/completions",
        "type": "openai",
        "model": "deepseek-chat",
    },
    "zhipu": {
        "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "type": "openai",
        "model": "glm-4-flash",
    },
    "tyqw": {
        "url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
        "type": "qwen",
        "model": "qwen-max",
    },
}

SCENE_PROMPTS = {
    "default": "你是一名耐心、严谨、善于循序渐进讲解的 AI 教学助手。请优先给出清晰结论，再补充步骤、原因和常见误区。",
    "lecture": "你是一名大学老师。请按照概念定义、核心原理、步骤拆解、例子说明、易错点总结的结构回答，语言清楚，适合课堂讲授。",
    "practice": "你是一名助教。请优先引导学生思考，不要直接只给最终答案。请按题目理解、解题思路、逐步提示、答案总结的结构回答。",
    "defense": "你是一名课程答辩评审老师。请从研究背景、研究意义、方法设计、实验结果、创新点、局限性和改进方向等角度进行追问和点评，输出尽量结构化。",
}
