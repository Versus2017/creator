import uuid
from fastapi import UploadFile, File
from ...db import sm
from .. import router as app
from ..jwt import login_required, get_user
from ..utils import abort_json
from .forms import ImageForm, AudioForm, ALLOWED_IMAGE_EXTENSIONS, ALLOWED_AUDIO_EXTENSIONS
from .models import MediaModel
from ...config import config


@app.post('/media')
@login_required
async def upload_media(file: UploadFile = File(...)):
    """
    统一的媒体文件上传接口
    
    支持：
    - 图片：png, jpg, jpeg, gif
    - 音频：mp3, m4a, wav, ogg, webm, aac, flac, opus
    
    自动识别文件类型并处理
    """
    # 获取文件扩展名
    ext = file.filename.split('.')[-1].lower()
    
    # 判断文件类型
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        file_type = "image"
    elif ext in ALLOWED_AUDIO_EXTENSIONS:
        file_type = "audio"
    else:
        raise abort_json(400, f'不支持的文件格式: {ext}')
    
    # 生成安全的文件名
    key = uuid.uuid4().hex
    secure_filename = f"{file_type}_{key}.{ext}"
    filepath = config.UPLOADS_DEFAULT_DEST
    
    # 保存文件
    full_path = f"{filepath}/{secure_filename}"
    with open(full_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # 创建数据库记录
    with sm.transaction_scope() as sa:
        m = MediaModel.create(sa, profile={})
        m.filename = secure_filename
        
        # 图片需要生成缩略图
        if file_type == "image":
            m.save_thumbnail(secure_filename)
        
        sa.commit()
        data = m.dump()
    
    return dict(
        success=True,
        data=data,
        file_type=file_type
    )



