# AI 文字创作平台

AI 辅助的文字创作工作台，支持小说、剧本、分镜脚本创作。

## 快速启动

```bash
# 一键安装 + 启动开发模式
./deploy.sh --run

# 或生产模式（单端口 0.0.0.0:8000）
./deploy.sh --prod
```

打开浏览器访问 `http://localhost:5173`（dev）或 `http://localhost:8000`（prod）。

默认账号：`admin / admin123`

## 公网访问

生产模式绑定 `0.0.0.0:8000`，可通过以下方式公网访问：

- 直接访问 `http://<公网IP>:8000`
- ngrok / cloudflare tunnel 内网穿透
- 部署到云服务器

## 配置 AI

在 `.env` 中配置 LLM：

```
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

支持任何 OpenAI 兼容接口（Claude、GPT、国产模型等）。

## 技术栈

- 后端：Python / FastAPI / SQLAlchemy / SQLite
- 前端：React / TypeScript / Vite / Zustand
- AI：OpenAI 兼容接口 + WebSocket 流式对话
