from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Tuple, List
from pathlib import Path
import os


class Settings(BaseSettings):
    ENV: str = 'local'
    DEBUG: bool = True
    SECRET_KEY: str = 'change-me'

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

    AUTHJWT_SECRET_KEY: str = 'change-me'
    AUTHJWT_ACCESS_TOKEN_EXPIRES: int = 3600 * 24 * 7
    AUTHJWT_TOKEN_LOCATION: List[str] = ['cookies', 'headers']
    AUTHJWT_COOKIE_SECURE: bool = True
    AUTHJWT_COOKIE_CSRF_PROTECT: bool = True
    AUTHJWT_COOKIE_SAMESITE: str = 'strict'
    AUTHJWT_ACCESS_COOKIE_KEY: str = 'creator_auth_cookie'
    AUTHJWT_ACCESS_CSRF_COOKIE_KEY: str = 'creator_auth_csrf_cookie'

    DEFAULT_TIMEZONE: str = 'Asia/Shanghai'

    PREFERRED_URL_SCHEME: str = 'http'
    EXTERNAL_URL: str = 'http://192.168.1.5:8000'

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

    # SIO_NAME: str = 'mingshu.socketio'
    # SIO_ASYNC_MODE: str = Field(
    #     'eventlet' if 'run_sio' in sys.argv else 'threading')

    # ali config
    ALY_SMS_DOMAIN: str = 'dysmsapi.aliyuncs.com'
    ALY_SMS_SIGN_NAME: str = 'creator'
    ALY_ACCESS_KEY_ID: str = ''
    ALY_ACCESS_KEY_SECRET: str = ''
    MESSAGE_SEND_ENABLED: bool = False

    # 阿里大模型调用
    ALY_MODEL_API_KEY: str = ''
    # 阿里大模型名称
    ALY_MODEL_NAME: str = 'qwen3-max'
    # base url
    ALY_API_URL: str = 'https://dashscope.aliyuncs.com/compatible-mode/v1'

    OCR_ALY_ACCESS_KEY_ID: str = ''
    OCR_ALY_ACCESS_KEY_SECRET: str = ''
    ALY_ACCESS_KEY_ID: str = ''
    ALY_ACCESS_KEY_SECRET: str = ''

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

    # 豆包视觉模型配置
    DOUBAO_API_URL: str = 'https://ark.cn-beijing.volces.com/api/v3'
    DOUBAO_API_KEY: str = ''
    DOUBAO_VISION_MODEL: str = 'doubao-1-5-thinking-vision-pro-250428'

    # 豆包1.6深度思考模型配置
    DOUBAO_16_API_KEY: str = ''
    DOUBAO_16_MODEL: str = 'doubao-seed-1-6-251015'
    DOUBAO_16_TIMEOUT: int = 180  # 深度思考模型超时时间（秒），默认30分钟
    DOUBAO_16_THINKING_MODE: str = 'enabled'  # 思考模式: disabled/enabled/auto

    # deepseek
    DEEPSEEK_API_KEY: str = ''

    # Whisper 本地部署配置
    WHISPER_USE_LOCAL: bool = True  # 使用本地 Whisper 模型（True）还是 OpenAI API（False）
    WHISPER_MODEL_NAME: str = 'medium'  # 本地模型名称：tiny, base, small, medium, large
    WHISPER_DEVICE: str = 'cpu'  # 计算设备：cpu 或 cuda（M1/M2 Mac 使用 cpu 即可，速度很快）
    WHISPER_COMPUTE_TYPE: str = 'int8'  # 计算精度：int8（快）, float16, float32（准）
    
    # OpenAI Whisper API 配置（当 WHISPER_USE_LOCAL=False 时使用）
    OPENAI_API_KEY: str = ''  # OpenAI API 密钥
    OPENAI_API_BASE: str = 'https://api.openai.com/v1'
    WHISPER_API_TIMEOUT: int = 300  # API 超时时间（秒）

    # 易学图片上传限制
    YI_MAX_IMAGE_COUNT: int = 3  # 易学预测每次最多上传图片数量

    # 是否使用豆包1.6进行图片识别（替代视觉模型阶段1），默认开启
    YI_USE_DOUBAO_16_FOR_VISION: bool = True


script_dir = os.path.dirname(__file__)  # 获取脚本所在目录
env_file_path = os.path.join(script_dir, 'local_config.env')
config = Settings(_env_file=env_file_path)
