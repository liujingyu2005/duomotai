# 基于多模态的 AI 教学互助式智能体

这是一个基于项目文档落地的可运行版本，采用 `Flask + HTML/CSS/JavaScript` 实现。

## 功能

- 多会话管理：新建、切换、重命名、删除
- 历史消息查看
- 模型切换：DeepSeek、智谱、通义千问
- API Key 本地保存（浏览器 localStorage）
- 文本提问 + 图片题目解析
- AI 回复支持 Markdown 展示
- 后端统一代理模型接口，带输入校验和错误处理
- SQLite 持久化存储会话数据
- 环境变量配置与基础日志
- 基础接口测试

## 运行方式

```bash
pip install -r requirements.txt
python app.py
```

然后打开：`http://127.0.0.1:5000`

## 配置方式

可参考 `.env.example` 中的配置项：

- `APP_HOST`
- `APP_PORT`    
- `APP_DEBUG`
- `DATABASE_PATH`
- `REQUEST_TIMEOUT`
- `LOG_LEVEL`

## 安全说明

- API Key 仅保存在浏览器本地，后端不会持久化保存。
- 后端增加了基础输入校验、请求超时、统一错误响应和安全响应头。
- 当前会话数据已持久化到 SQLite，服务重启后不会丢失。

## 注意事项

- 图片限制为 5MB 以内。
- 当前版本已接入 SQLite 与基础测试，但仍未实现登录鉴权与多用户隔离。

## 测试

```bash
python -m unittest discover -s tests
```
