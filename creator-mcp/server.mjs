#!/usr/bin/env node

import fs from 'node:fs';

const apiBase = (process.env.CREATOR_API_BASE || 'http://127.0.0.1:8000').replace(/\/$/, '');
const codexToken = process.env.CREATOR_CODEX_TOKEN || 'codex-local';
const frontendBase = process.env.CREATOR_FRONTEND_BASE || 'http://localhost:8080';
const evoFounderContextPath = process.env.EVOFOUNDER_CONTEXT_PATH || '';
const defaultUserId = process.env.CREATOR_CODEX_USER_ID
  ? Number(process.env.CREATOR_CODEX_USER_ID)
  : null;

function readEvoFounderContext() {
  if (!evoFounderContextPath) {
    return '';
  }
  try {
    if (fs.existsSync(evoFounderContextPath)) {
      return fs.readFileSync(evoFounderContextPath, 'utf8').trim();
    }
  } catch (_err) {
    return '';
  }
  return '';
}

const tools = [
  {
    name: 'creator_start_script_conversation',
    description: '仅当用户明确要求“用 Creator 创建/开启/新建一条脚本创作对话”时使用。不要用于解释 Creator 配置、端口、链接、登录、调试、复盘、选题分析或普通聊天。',
    inputSchema: {
      type: 'object',
      properties: {
        topic: {
          type: 'string',
          description: '视频主题或选题标题。',
        },
        content: {
          type: 'string',
          description: '发送给 Creator AI 的第一条创作需求。为空时使用 topic。',
        },
        title: {
          type: 'string',
          description: 'Creator 对话标题。为空时使用 topic。',
        },
        user_id: {
          type: 'integer',
          description: '可选 Creator 用户 ID。不传则由后端 CREATOR_CODEX_USER_ID 或第一个用户决定。',
        },
        os_context: {
          type: 'string',
          description: '可选。Codex 从 02 自媒体内容线当前对话中总结的 EvoFounder OS 当前状态、进度、约束和本次视频意图。',
        },
      },
      required: ['topic'],
      additionalProperties: false,
    },
  },
  {
    name: 'creator_get_hyperframes_manifest',
    description: '获取 Creator 某个脚本的 HyperFrames 素材交接清单。只读工具，不创建对话、不触发渲染。用于 Codex 准备调用 HyperFrames 前读取脚本正文、封面图、素材图和使用建议。',
    inputSchema: {
      type: 'object',
      properties: {
        script_id: {
          type: 'integer',
          description: 'Creator 脚本 ID。',
        },
        title: {
          type: 'string',
          description: '可选脚本标题。传入后按标题查找最近脚本；与 script_id 二选一。',
        },
        user_id: {
          type: 'integer',
          description: '可选 Creator 用户 ID。不传则由 CREATOR_CODEX_USER_ID 决定。',
        },
      },
      anyOf: [
        { required: ['script_id'] },
        { required: ['title'] },
      ],
      additionalProperties: false,
    },
  },
];

function buildCreatorContent(args) {
  const baseContext = readEvoFounderContext();
  const liveContext = args.os_context ? String(args.os_context).trim() : '';
  const userContent = args.content || args.topic;
  const contextBlocks = [
    baseContext ? `长期背景与默认约束：\n${baseContext}` : '',
    liveContext ? `本次调用前，Codex 从 02 自媒体内容线总结的当前状态：\n${liveContext}` : '',
  ].filter(Boolean).join('\n\n---\n\n');

  return `${contextBlocks || '暂无外部上下文，请根据本次创作任务自行判断。'}

本次创作任务：
${userContent}

请注意：
1. 不要机械复述长期背景，要根据“当前状态”和“本次创作任务”决定重点。
2. 如果本次主题涉及 EvoFounder OS，再介绍 OS 的定位、模块和当前进展；如果不涉及，就只把它作为账号背景。
3. 如果本次主题需要演示 02 调用 Creator，再体现这个现场流程；否则不要强行塞演示。
4. 口播要真实、接地气，像一个全栈开发者在公开搭建自己的事业操作系统，而不是工具广告。`;
}

function send(message) {
  process.stdout.write(JSON.stringify(message) + '\n');
}

function result(id, payload) {
  send({ jsonrpc: '2.0', id, result: payload });
}

function error(id, code, message) {
  send({ jsonrpc: '2.0', id, error: { code, message } });
}

async function postJson(path, body) {
  const response = await fetch(apiBase + path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Codex-Token': codexToken,
    },
    body: JSON.stringify(body),
  });

  const text = await response.text();
  let payload = null;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch (_err) {
    payload = { raw: text };
  }

  if (!response.ok) {
    const detail = payload && (payload.detail || payload.message || payload.raw);
    throw new Error(detail || `Creator API request failed: ${response.status}`);
  }
  return payload;
}

async function getJson(path) {
  const response = await fetch(apiBase + path, {
    method: 'GET',
    headers: {
      'X-Codex-Token': codexToken,
    },
  });

  const text = await response.text();
  let payload = null;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch (_err) {
    payload = { raw: text };
  }

  if (!response.ok) {
    const detail = payload && (payload.detail || payload.message || payload.raw);
    throw new Error(detail || `Creator API request failed: ${response.status}`);
  }
  return payload;
}

function asToolText(data) {
  const payload = data && data.data ? data.data : data;
  const conversation = payload && payload.conversation ? payload.conversation : {};
  const lines = [
    'Creator 创作对话已创建。',
    '',
    `标题：${conversation.title || ''}`,
    `Conversation ID：${conversation.id || ''}`,
    `继续创作：${payload.url || ''}`,
  ];

  if (payload.first_reply) {
    lines.push('', '第一轮 AI 回复：', payload.first_reply);
  }

  return lines.join('\n');
}

async function callTool(name, args) {
  if (name === 'creator_get_hyperframes_manifest') {
    const userId = args.user_id || defaultUserId;
    const queryParts = [];
    if (userId) queryParts.push(`user_id=${encodeURIComponent(userId)}`);
    let path = '';
    if (args.script_id) {
      path = `/v1/codex/creator/scripts/${encodeURIComponent(args.script_id)}/hyperframes-manifest`;
    } else {
      queryParts.push(`title=${encodeURIComponent(args.title)}`);
      path = `/v1/codex/creator/scripts/hyperframes-manifest`;
    }
    const query = queryParts.length ? `?${queryParts.join('&')}` : '';
    const data = await getJson(path + query);
    const manifest = data && data.data ? data.data : data;
    const script = manifest.script || {};
    const assets = manifest.assets || [];
    return {
      content: [
        {
          type: 'text',
          text: [
            'Creator HyperFrames manifest 已获取。',
            '',
            `脚本：${script.title || ''}`,
            `Script ID：${script.id || args.script_id}`,
            `素材数量：${assets.length}`,
            '',
            '下一步：可将 structuredContent 交给 HyperFrames 生成片头、转场、B-roll 或结构动画。',
          ].join('\n'),
        },
      ],
      structuredContent: manifest,
    };
  }

  if (name !== 'creator_start_script_conversation') {
    throw new Error(`Unknown tool: ${name}`);
  }

  const payload = {
    topic: args.topic,
    content: buildCreatorContent(args),
    title: args.title || args.topic,
    frontend_base_url: frontendBase,
  };
  if (args.user_id) {
    payload.user_id = args.user_id;
  } else if (defaultUserId) {
    payload.user_id = defaultUserId;
  }

  const data = await postJson('/v1/codex/creator/start-script-conversation', payload);
  return {
    content: [
      {
        type: 'text',
        text: asToolText(data),
      },
    ],
    structuredContent: data && data.data ? data.data : data,
  };
}

async function handle(request) {
  const { id, method, params } = request;

  if (method === 'initialize') {
    result(id, {
      protocolVersion: params && params.protocolVersion ? params.protocolVersion : '2025-06-18',
      capabilities: {
        tools: {},
      },
      serverInfo: {
        name: 'creator-mcp',
        version: '0.1.0',
      },
      instructions: 'Creator MCP 是 EvoFounder OS 的自媒体内容线工具。只有用户明确要求在 Creator 中创建新的脚本创作对话时，才调用 creator_start_script_conversation。不要因为用户提到 Creator、端口、链接、登录、调试、复盘、选题分析或普通自媒体讨论就创建 Creator 对话。创建对话会写入 Creator 数据库，应谨慎使用。调用时应尽量传入 os_context，总结 02 自媒体内容线当前状态、进度、约束和本次视频意图。本服务器会读取外部 EvoFounder 上下文文件作为兜底，不会把某一次视频主题写死。',
    });
    return;
  }

  if (method === 'notifications/initialized') {
    return;
  }

  if (method === 'tools/list') {
    result(id, { tools });
    return;
  }

  if (method === 'tools/call') {
    try {
      const toolResult = await callTool(params.name, params.arguments || {});
      result(id, toolResult);
    } catch (err) {
      result(id, {
        isError: true,
        content: [
          {
            type: 'text',
            text: err && err.message ? err.message : String(err),
          },
        ],
      });
    }
    return;
  }

  error(id, -32601, `Method not found: ${method}`);
}

let buffer = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
  buffer += chunk;
  let newlineIndex = buffer.indexOf('\n');
  while (newlineIndex >= 0) {
    const line = buffer.slice(0, newlineIndex).trim();
    buffer = buffer.slice(newlineIndex + 1);
    newlineIndex = buffer.indexOf('\n');
    if (!line) continue;

    let request = null;
    try {
      request = JSON.parse(line);
    } catch (_err) {
      error(null, -32700, 'Parse error');
      continue;
    }

    handle(request).catch(err => {
      error(request.id, -32603, err && err.message ? err.message : String(err));
    });
  }
});
