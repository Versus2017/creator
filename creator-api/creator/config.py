from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Tuple, List, Optional
from pathlib import Path
import os


class Settings(BaseSettings):
    ENV: str = 'local'
    DEBUG: bool = True
    SECRET_KEY: str = 'change-me-in-local-config'

    WECHAT_URL_PREFIX: str = ''

    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_DATABASE_URI: str = 'postgresql://@/creator'
    SQLALCHEMY_COMMIT_ON_TEARDOWN: bool = False
    SQLALCHEMY_ECHO: bool = False

    SECURITY_PASSWORD_HASH: str = 'bcrypt'
    SECURITY_PASSWORD_SALT: str = 'pass'
    SECURITY_SEND_PASSWORD_CHANGE_EMAIL: bool = False
    SECURITY_HASHING_SCHEMES: List[str] = ['bcrypt', 'hex_md5']
    SECURITY_CONFIRMABLE: bool = True
    SECURITY_TRACKABLE: bool = True
    SECURITY_TOKEN_AUTHENTICATION_HEADER: str = 'Authorization'
    WTF_CSRF_ENABLED: bool = False

    BO_AUTH_PASSWORD_HASH: str = 'pbkdf2:sha256'
    BO_AUTH_PASSWORD_SALT_LENGTH: int = 8
    BO_AUTH_2FA_EXPIRES: int = 300
    VERIFY_CODE_TTL: int = 300

    AUTHJWT_SECRET_KEY: str = 'change-me-in-local-config'
    AUTHJWT_ACCESS_TOKEN_EXPIRES: int = 3600 * 24 * 7
    AUTHJWT_TOKEN_LOCATION: List[str] = ['cookies', 'headers']
    AUTHJWT_COOKIE_SECURE: bool = True
    AUTHJWT_COOKIE_CSRF_PROTECT: bool = True
    AUTHJWT_COOKIE_SAMESITE: str = 'strict'
    AUTHJWT_ACCESS_COOKIE_KEY: str = 'creator_auth_cookie'
    AUTHJWT_ACCESS_CSRF_COOKIE_KEY: str = 'creator_auth_csrf_cookie'

    DEFAULT_TIMEZONE: str = 'Asia/Shanghai'

    PREFERRED_URL_SCHEME: str = 'http'
    EXTERNAL_URL: str = 'http://127.0.0.1:8000'

    HUEY_NAME: str = 'creator.huey'
    REDIS_HOST: str = '127.0.0.1'
    REDIS_PORT: int = 6379
    REDIS_DB: int = 10

    UPLOADS_DEFAULT_DEST: str = './instance'
    DEFAULT_THUMBNAIL_SIZE: Tuple[int, int] = (400, 400)

    SENSITIVE_KEYWORDS: Tuple[str, ...] = (
        'client_name',
        'client_mobile',
        'client_plate',
    )

    LOGGING_MAIL_SERVER: Tuple[str, int] = ('localhost', 10025)
    LOGGING_MAIL_FROM: str = 'reply@local.lan'
    LOGGING_MAIL_TO_LIST: List[str] = ['test@local.lan']

    AI_GENERATE_WORD_LIMIT: int = 10
    USER_GENERATE_WORD_MAX_COUNT: int = 50
    USER_EXCLUDE_WORD_MAX_COUNT: int = 500

    WECHAT_APP_ID: str = ''
    WECHAT_APP_SECRET: str = ''
    WECHAT_PAY_DEBUG: bool = True

    CACHE_TYPE: str = 'simple'
    CACHE_NO_NULL_WARNING: bool = True
    CACHE_DEFAULT_TIMEOUT: int = 300

    # ali config（密钥请写入 local_config.env，勿提交到 Git）
    ALY_SMS_DOMAIN: str = 'dysmsapi.aliyuncs.com'
    ALY_SMS_SIGN_NAME: str = 'creator'
    ALY_ACCESS_KEY_ID: str = ''
    ALY_ACCESS_KEY_SECRET: str = ''
    MESSAGE_SEND_ENABLED: bool = False

    ALY_MODEL_API_KEY: str = ''
    ALY_MODEL_NAME: str = 'qwen3-max'
    ALY_API_URL: str = 'https://dashscope.aliyuncs.com/compatible-mode/v1'

    OCR_ALY_ACCESS_KEY_ID: str = ''
    OCR_ALY_ACCESS_KEY_SECRET: str = ''

    BABEL_DEFAULT_LOCALE: str = 'zh'
    BABEL_SUPPORTED_LOCALES: List[str] = ['zh', 'en']

    GPT_TOKEN: str = ''
    GPT_PROXY: str = ''
    GPT_IMAGE_RESIZE_FACTOR: int = 1
    GPT_MODAL_NAME: str = 'gpt-4o-mini'
    GPT_ADVANCED_MODAL_NAME: str = 'gpt-4o'
    GPT_MAX_WINDOW_CONTEXT: int = 128000
    GPT_MAX_OUTPUT_TOKENS: int = 5000

    GEMINI_API_KEY: str = ''

    ZHIPU_API_KEY: str = ''

    DOUBAO_API_URL: str = 'https://ark.cn-beijing.volces.com/api/v3'
    DOUBAO_API_KEY: str = ''
    DOUBAO_VISION_MODEL: str = 'doubao-1-5-thinking-vision-pro-250428'

    DOUBAO_16_API_KEY: str = ''
    DOUBAO_16_MODEL: str = 'doubao-seed-1-6-251015'
    DOUBAO_16_TIMEOUT: int = 180
    DOUBAO_16_THINKING_MODE: str = 'enabled'

    DEEPSEEK_API_KEY: str = ''
    DEEPSEEK_MODEL_NAME: str = 'deepseek-v4-pro'

    OPENAI_GPT_API_KEY: str = ''
    OPENAI_GPT_API_BASE: str = 'https://api.laozhang.ai/v1'
    OPENAI_GPT_MODEL_NAME: str = 'gpt-5.5'

    CHAT_MAX_HISTORY_MESSAGES: int = 36
    CHAT_MAX_MESSAGE_CHARS: int = 6000
    CHAT_MAX_REFERENCED_SCRIPTS: int = 3
    CHAT_MAX_SCRIPT_REF_CHARS: int = 4000
    CHAT_MAX_SCRIPT_REF_TOTAL_CHARS: int = 10000

    # 创作对话 / 脚本生成 / 研究对话 默认模型
    # 可选: deepseek | openai_gpt | ali_chat | doubao_vision | doubao_16
    CHAT_CONVERSATION_MODEL_TYPE: str = 'openai_gpt'
    # Codex / MCP 首条创作对话
    CHAT_CODEX_MODEL_TYPE: str = 'openai_gpt'
    # 脚本 AI 生图前的规划分析
    CHAT_SCRIPT_MEDIA_PLAN_MODEL_TYPE: str = 'openai_gpt'
    # True 时前端 form.model_type 可覆盖 CHAT_CONVERSATION_MODEL_TYPE
    CHAT_ALLOW_REQUEST_MODEL_OVERRIDE: bool = False

    GPT_IMAGE_2_API_KEY: str = ''
    GPT_IMAGE_2_API_URL: str = 'https://api.laozhang.ai/v1'
    GPT_IMAGE_2_MODEL_NAME: str = 'gpt-image-2'
    GPT_IMAGE_2_ROUTE: str = 'enterprise'
    GPT_IMAGE_2_DEFAULT_SIZE_ICON: str = '1024x1024'
    GPT_IMAGE_2_DEFAULT_SIZE_COVER_LIST: str = '2048x1152'
    GPT_IMAGE_2_DEFAULT_SIZE_COVER_DETAIL: str = '2048x1152'
    GPT_IMAGE_2_DEFAULT_SIZE_COVER_SQUARE: str = '2048x2048'
    GPT_IMAGE_2_DEFAULT_SIZE_COVER_POSTER: str = '1024x1536'
    GPT_IMAGE_2_DEFAULT_QUALITY: str = 'high'
    GPT_IMAGE_2_REQUEST_TIMEOUT: int = 240

    WHISPER_USE_LOCAL: bool = True
    WHISPER_MODEL_NAME: str = 'medium'
    WHISPER_DEVICE: str = 'cpu'
    WHISPER_COMPUTE_TYPE: str = 'int8'
    VOICE_STREAM_MIN_DURATION_SEC: int = 15
    VOICE_TRANSCRIBE_USE_HUEY: bool = True

    OPENAI_API_KEY: str = ''
    OPENAI_API_BASE: str = 'https://api.openai.com/v1'
    WHISPER_API_TIMEOUT: int = 300

    YI_MAX_IMAGE_COUNT: int = 3
    YI_USE_DOUBAO_16_FOR_VISION: bool = True

    # Codex / MCP 外部调用（密钥写入 local_config.env）
    CREATOR_CODEX_TOKEN: str = 'codex-local'
    CREATOR_CODEX_USER_ID: Optional[int] = None


script_dir = os.path.dirname(__file__)
env_file_path = os.path.join(script_dir, 'local_config.env')
config = Settings(_env_file=env_file_path)
