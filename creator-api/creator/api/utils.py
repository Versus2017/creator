import tiktoken
import json
import base64
import numpy as np
import soundfile as sf
from pathlib import Path
from datetime import datetime, timedelta
from enum import IntEnum as BaseIntEnum, Enum as BaseEnum
from pytz import timezone, utc
from aliyunsdkcore.client import AcsClient

from fastapi import HTTPException, Request
from creator.config import config


def num_tokens_from_messages(messages, model):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        for key, value in message.items():
            # if value is array, it's a list of messages
            if isinstance(value, list):
                num_tokens += num_tokens_from_messages(value, model)
                continue
            if isinstance(value, dict):
                num_tokens += num_tokens_from_messages([value], model)
                continue
            num_tokens += len(encoding.encode(value))
            if key == "name":  # if there's a name, the role is omitted
                num_tokens += -1  # role is always required and always 1 token
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens
  # See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")



# Converts Float32 numpy array to PCM16 byte array
def float_to_16bit_pcm(float32_array):
    pcm16_array = np.clip(float32_array, -1, 1) * 32767
    return pcm16_array.astype(np.int16).tobytes()


# Converts a Float32 numpy array to base64-encoded PCM16 data
def base64_encode_audio(float32_array):
    pcm16_data = float_to_16bit_pcm(float32_array)
    return base64.b64encode(pcm16_data).decode('utf-8')


def get_base64_audio_from_file():
    filename = 'gpt_start.mp3'
    path = Path(config.UPLOADS_DEFAULT_DEST) / filename
    if not path.exists():
        # Create audio file from text
        pass
        # gpt = ChatGPTModel()
        # gpt.create_audio_from_text('你好！', filename)

    #  check if file exists
    if not path.exists():
        return None

    # Using the "soundfile" library to read audio file and get raw audio bytes
    data, samplerate = sf.read(path, dtype='float32')
    if data.ndim == 1:
        # Mono audio
        channel_data = data
    else:
        # Stereo audio, use the first channel
        channel_data = data[:, 0]
    # channel_data = data[:, 0]  # only accepts mono
    return base64_encode_audio(channel_data)


def get_acs_client():
    return AcsClient(
        config.ALY_ACCESS_KEY_ID,
        config.ALY_ACCESS_KEY_SECRET,
        'cn-hangzhou')


def external_url_for(request: Request, endpoint: str):
    scheme = 'https' if config.EXTERNAL_URL.startswith('https') else 'http'
    return request.url_for(endpoint, _scheme=scheme)


def abort_json(code, message, errors=None, **extra):
    error = {"message": message}
    if errors:
        error['errors'] = errors
    resp = {"success": False, "error": error, **extra}
    raise HTTPException(status_code=code, detail=resp)


def convert_to_utc_daterange(daterange):
    ut = user_timezone()
    start, end = daterange.split('~')
    start = datetime.strptime(start.strip(), '%Y-%m-%d')
    start = ut.localize(start)
    start = to_utc_timezone(start)
    end = datetime.strptime(end.strip(), '%Y-%m-%d') + timedelta(days=1)
    end = ut.localize(end)
    end = to_utc_timezone(end)
    return start, end


def mask_value(value):
    if not isinstance(value, str):
        raise ValueError(
            f'only strings can be masked but was given "{value}"'
        )
    if not value:
        return value
    n = len(value)
    if n == 1:
        return '*'
    elif n <= 6:  # *****4
        return '*' * (n - 1) + value[-1]
    elif n <= 10:  # 12******34
        return value[:2] + ('*' * (n - 4)) + value[n - 2:n]
    else:  # 123***********123
        return value[:3] + ('*' * (n - 6)) + value[n - 3:n]


def get_settings():
    from .settings.settings import Settings
    rv = Settings()
    return rv


settings = get_settings()

#
#
# # TODO: 文案?
# abort_403 = partial(abort_json, code=403, message='你没有权限访问')
# abort_401 = partial(abort_json, code=401, message='请先登录')
#
# config = LocalProxy(lambda: current_app.config)
# settings = LocalProxy(get_settings)
# oab = LocalProxy(lambda: current_app.extensions['oab'])


def get_user_timezone():
    return timezone(config['DEFAULT_TIMEZONE'])


def user_timezone():
    return timezone(config['DEFAULT_TIMEZONE'])


def to_user_timezone(dt):
    utc_datetime = dt.replace(tzinfo=utc)
    user_tz = user_timezone()
    return utc_datetime.astimezone(user_tz)


def to_utc_timezone(dt):
    return dt.astimezone(utc)


def strptime_to_utc(time, fmt='%Y-%m-%d %H:%M:%S'):
    if not time:
        return None
    try:
        ret = datetime.strptime(time, fmt)
    except ValueError as e:
        print(e)
        return None
    ret = user_timezone().localize(ret)
    ret = to_utc_timezone(ret).replace(tzinfo=None)
    return ret


def strptime_to_local(time, fmt='%Y-%m-%d %H:%M:%S'):
    if isinstance(time, datetime):
        time = time.strftime(fmt)
    if not time:
        return None
    try:
        ret = datetime.strptime(time, fmt)
    except ValueError:
        return None
    ret = user_timezone().localize(ret)
    ret = to_user_timezone(ret).replace(tzinfo=None)
    return ret


class IntEnum(BaseIntEnum):
    @classmethod
    def init(cls, value):
        return next((item for item in cls if item.value == value), None)

    @classmethod
    def get_enum_by_label(cls, label):
        return next((item for item in cls if item.label == label), None)

    def dump(self):
        name = getattr(self, 'label', self.value)
        return dict(
            name=self.name,
            label=name,
            value=self.value,
        )


class Enum(BaseEnum):
    def dump(self):
        return dict(
            name=self.name,
            label=getattr(self, 'label', self.name),
            value=self.value,
        )
