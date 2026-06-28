from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from typing import Optional
from pydantic import BaseModel, field_validator

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
ALLOWED_AUDIO_EXTENSIONS = {
    # 常见音频格式
    "mp3",      # MPEG-1 Audio Layer 3
    "m4a",      # MPEG-4 Audio
    "wav",      # Waveform Audio File
    "ogg",      # Ogg Vorbis
    "webm",     # WebM（浏览器录音常用）
    "aac",      # Advanced Audio Coding
    "flac",     # Free Lossless Audio Codec
    "opus",     # Opus音频编码
}


class ImageForm(BaseModel):
    image: UploadFile

    @field_validator('image')
    def validate_image(cls, v, values):
        if not v.filename.split('.')[-1] in ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError('图片格式错误')
        return v


class AudioForm(BaseModel):
    audio: UploadFile

    @field_validator('audio')
    def validate_audio(cls, v, values):
        if not v.filename.split('.')[-1] in ALLOWED_AUDIO_EXTENSIONS:
            raise ValueError('音频格式错误')
        return v

