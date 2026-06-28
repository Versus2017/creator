import json
from datetime import datetime
from typing import Optional

from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...db import sm
from ...config import config
from .. import router as app
from ..ai.openai_api import _resolve_api_user, get_chat_ai_model, resolve_codex_model_type
from ..conversations.api import _build_chat_messages, _user_profile_for_prompt
from ..conversations.constants import ConversationStatus, MessageRole
from ..conversations.models import Conversation, Message
from ..conversations.tasks import persist_assistant_reply
from ..users.models import User


class CodexStartScriptConversationForm(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    user_id: Optional[int] = Field(None, gt=0)
    frontend_base_url: Optional[str] = Field(default='http://localhost:8080')


def _verify_codex_token(x_codex_token: Optional[str]):
    expected = config.CREATOR_CODEX_TOKEN
    if not expected:
        raise HTTPException(status_code=500, detail='CREATOR_CODEX_TOKEN 未配置')
    if x_codex_token != expected:
        raise HTTPException(status_code=401, detail='Codex token 无效')


def _resolve_codex_user(db: Session, user_id: Optional[int]) -> User:
    target_user_id = user_id if user_id is not None else config.CREATOR_CODEX_USER_ID

    if target_user_id is not None:
        user = db.query(User).filter(User.id == target_user_id).first()
    else:
        user = db.query(User).order_by(User.id.asc()).first()

    if not user:
        raise HTTPException(status_code=404, detail='未找到可用于 Codex 的 Creator 用户')
    return user


def _build_frontend_url(base_url: Optional[str], conversation_id: int) -> str:
    base = (base_url or 'http://localhost:8080').rstrip('/')
    return f'{base}/#/creativity?conversation_id={conversation_id}'


def _parse_sse_payload(chunk: str) -> Optional[dict]:
    text = (chunk or '').strip()
    if not text:
        return None
    if text.startswith('data:'):
        text = text[5:].strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


@app.post('/codex/creator/start-script-conversation')
async def codex_start_script_conversation(
    form: CodexStartScriptConversationForm,
    x_codex_token: Optional[str] = Header(None, alias='X-Codex-Token'),
    db: Session = Depends(sm.get_db),
):
    """Codex 入口：创建创作对话，发送第一条消息，等待 AI 第一轮回复并返回前端地址。"""
    _verify_codex_token(x_codex_token)
    current_user = _resolve_codex_user(db, form.user_id)

    user_content = (form.content or form.topic).strip()
    title = (form.title or form.topic).strip()[:200]

    with sm.transaction_scope() as sa:
        conversation = Conversation.create(
            sa,
            user_id=current_user.id,
            title=title,
            topic=form.topic,
            status=ConversationStatus.IN_PROGRESS,
        )
        conversation.message_count = 0
        conversation.total_tokens = 0
        conversation.context_summary = {}
        conversation_id = conversation.id

    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=500, detail='Codex 创建会话失败')

    user_profile = _user_profile_for_prompt(current_user)
    chat_messages = _build_chat_messages(
        conversation,
        [],
        user_content,
        current_snapshots=None,
        user_profile=user_profile,
    )

    with sm.transaction_scope() as sa:
        Message.create(
            sa,
            conversation_id=conversation_id,
            role=MessageRole.USER.value,
            content=user_content,
        )

    codex_model_type = resolve_codex_model_type()
    ai_model = get_chat_ai_model(codex_model_type)
    ai_model.reply = ''
    api_user_mobile = _resolve_api_user(current_user)
    stream_text_parts = []
    stream_error = ''
    async for chunk in ai_model.reply_stream_text(
        chat_messages,
        user_mobile=api_user_mobile,
    ):
        payload = _parse_sse_payload(chunk)
        if not payload:
            continue
        if payload.get('type') == 'input' and payload.get('content'):
            stream_text_parts.append(payload.get('content') or '')
        elif payload.get('type') == 'error':
            stream_error = payload.get('content') or 'AI 回复失败'

    ai_text = ''.join(stream_text_parts).strip()
    if not ai_text:
        ai_text = (getattr(ai_model, 'reply', None) or '').strip()
    if not ai_text and not stream_error:
        fallback_text = await ai_model.reply_text(
            chat_messages,
            user_mobile=api_user_mobile,
        )
        ai_text = (fallback_text or '').strip()

    if ai_text:
        persist_assistant_reply(conversation_id, ai_text, count_delta=2)
    else:
        with sm.transaction_scope() as sa:
            conv = Conversation.get_or_404(sa, conversation_id)
            conv.message_count = (conv.message_count or 0) + 1
            conv.updated_at = datetime.utcnow()

    db.expire_all()
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()

    db.refresh(conversation)
    return {
        'success': True,
        'data': {
            'conversation': conversation.dump(),
            'messages': [msg.dump() for msg in messages],
            'first_reply': ai_text,
            'ai_error': stream_error,
            'url': _build_frontend_url(form.frontend_base_url, conversation_id),
        },
    }
