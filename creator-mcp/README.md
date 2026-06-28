# Creator MCP 配置说明

`creator-mcp` 是 Creator 与 **Codex / Cursor Agent** 之间的 MCP 桥接服务。它把 Creator 后端的 Codex 接口封装成 MCP 工具，让外部 Agent 可以：

- 创建一条脚本创作对话并发送首条需求
- 读取某脚本的 HyperFrames 素材交接清单（正文 + 封面 + 素材图）

---

## 前置条件

1. **Creator 后端已启动**（默认 `http://127.0.0.1:8000`）
2. 已在 `creator-api/creator/local_config.env` 中配置 `CREATOR_CODEX_TOKEN`（与 MCP 侧 token **保持一致**）
3. 本机已安装 **Node.js 18+**（用于运行 `server.mjs`）

---

## 一、后端配置（`local_config.env`）

在 `creator-api/creator/` 下复制示例并编辑：

```bash
cp creator/local_config.env.example creator/local_config.env
```

与 MCP 相关的关键项：

| 变量 | 说明 | 示例 |
|------|------|------|
| `CREATOR_CODEX_TOKEN` | Codex 调用 Creator API 的鉴权 token，**必须与 MCP 环境变量一致** | `codex-local` |
| `CREATOR_CODEX_USER_ID` | 可选。指定 Codex 代哪个 Creator 用户创建对话；不填则用库中第一个用户 | `1` |
| `CHAT_CODEX_MODEL_TYPE` | MCP 创建对话时使用的 AI 模型类型 | `openai_gpt` |

对话模型、生图 Key 等完整说明见：[模型与密钥配置](../docs/configuration/模型与密钥配置.md)。

---

## 二、在 Codex / Cursor 中注册 MCP

编辑 `~/.codex/config.toml`（或 Cursor 的 MCP 配置），增加：

```toml
[mcp_servers.creator]
command = "node"
args = ["/你的路径/creator/creator-mcp/server.mjs"]
env = { CREATOR_API_BASE = "http://127.0.0.1:8000", CREATOR_CODEX_TOKEN = "codex-local", CREATOR_FRONTEND_BASE = "http://localhost:8080" }
```

> 将 `args` 中的路径改为你本机 `creator-mcp/server.mjs` 的**绝对路径**。  
> `CREATOR_CODEX_TOKEN` 必须与 `local_config.env` 里相同。

修改配置后**重启 Codex / Cursor**，MCP 才会加载。

---

## 三、MCP 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CREATOR_API_BASE` | `http://127.0.0.1:8000` | Creator 后端地址（不含 `/v1`） |
| `CREATOR_CODEX_TOKEN` | `codex-local` | 与后端 `CREATOR_CODEX_TOKEN` 一致 |
| `CREATOR_FRONTEND_BASE` | `http://localhost:8080` | Web 前端地址，用于生成「继续创作」链接 |
| `CREATOR_CODEX_USER_ID` | 空 | 可选，等同后端 `CREATOR_CODEX_USER_ID` |
| `EVOFOUNDER_CONTEXT_PATH` | 空 | 可选。本地 Markdown 长期背景文件路径（勿提交 Git） |

---

## 四、可用工具

### `creator_start_script_conversation`

**用途**：在 Creator 中新建一条脚本创作对话，并发送第一条创作需求。

| 参数 | 必填 | 说明 |
|------|------|------|
| `topic` | 是 | 视频主题 / 选题标题 |
| `content` | 否 | 第一条创作需求；为空则用 `topic` |
| `title` | 否 | 对话标题；为空则用 `topic` |
| `user_id` | 否 | Creator 用户 ID |
| `os_context` | 否 | 当前业务/OS 上下文摘要（推荐由 Agent 动态传入） |

返回：对话 ID、Web 继续编辑链接、第一轮 AI 回复。

### `creator_get_hyperframes_manifest`

**用途**：只读获取某脚本的 HyperFrames 素材清单（正文、封面、素材图、使用建议），不创建对话、不触发渲染。

| 参数 | 必填 | 说明 |
|------|------|------|
| `script_id` | 二选一 | 脚本 ID |
| `title` | 二选一 | 按标题查找最近脚本 |
| `user_id` | 否 | Creator 用户 ID |

---

## 五、本地长期上下文（可选）

若你有固定的账号定位、合规约束等长期背景，可写入本地 Markdown，并通过 `EVOFOUNDER_CONTEXT_PATH` 指向该文件。

- 该文件**不应提交到 Git**（已在根目录 `.gitignore` 忽略 `.evofounder-context.md`）
- 调用 `creator_start_script_conversation` 时，仍建议 Agent 通过 `os_context` 传入**本次任务**的实时摘要；文件内容仅作长期默认约束

---

## 六、常见问题

**Q：MCP 报 401 / token 无效？**  
A：检查 `local_config.env` 与 MCP `env` 里的 `CREATOR_CODEX_TOKEN` 是否完全一致，并重启后端。

**Q：创建对话成功但链接打不开？**  
A：确认 `CREATOR_FRONTEND_BASE` 与 `creator-web` 实际端口一致。

**Q：Agent 没有调用 MCP 工具？**  
A：仅在用户明确要求「用 Creator 创建/开启脚本对话」等场景下才应调用；普通聊天不应触发。

---

## 相关文档

- [模型与密钥配置](../docs/configuration/模型与密钥配置.md)
- [Creator 后端 README](../creator-api/README.md)
