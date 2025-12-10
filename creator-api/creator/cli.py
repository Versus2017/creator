import os
import typer

app = typer.Typer()


@app.command("dev")
def dev_server(host: str = typer.Option("0.0.0.0", "-h", "--host",
                                        help="The interface to bind to."),
               port: int = typer.Option(5002, "-p", "--port",
                                        help="The port to bind to.")):
    """Runs a customized development server."""
    # 延迟导入，避免对其他命令造成初始化开销
    import uvicorn
    os.environ.setdefault('FASTAPI_DEBUG', '1')
    uvicorn.run("creator.app:app", host=host, port=port, reload=True)


@app.command("test_whisper")
def test_whisper(
    audio_file: str = typer.Option(
        "./instance/audio_d56bd3103de047099500a0e3bdf9050a.webm",
        "-f", "--file",
        help="音频文件路径"
    ),
    use_array: bool = typer.Option(
        True, "--array/--no-array", help="使用 numpy 数组绕过 ffmpeg 读流，需先转 WAV"
    )
):
    """测试 Whisper 转写功能"""
    import sys
    import time
    import logging
    import shutil
    import subprocess
    
    # ========== 环境诊断 ==========
    typer.echo(f"\n{'='*60}")
    typer.echo(f"🔍 环境诊断")
    typer.echo(f"{'='*60}")
    
    # 1. 检查 PATH 环境变量
    current_path = os.environ.get('PATH', '')
    typer.echo(f"\n📋 PATH 环境变量:")
    typer.echo(f"   {current_path}")
    
    # 2. 检查 shutil.which 是否能找到 ffmpeg/ffprobe
    ffmpeg_path = shutil.which('ffmpeg')
    ffprobe_path = shutil.which('ffprobe')
    typer.echo(f"\n🔍 shutil.which() 结果:")
    typer.echo(f"   ffmpeg:  {ffmpeg_path if ffmpeg_path else '❌ 未找到'}")
    typer.echo(f"   ffprobe: {ffprobe_path if ffprobe_path else '❌ 未找到'}")
    
    # 3. 直接调用 /usr/local/bin/ffmpeg -version
    typer.echo(f"\n🔍 直接调用 /usr/local/bin/ffmpeg -version:")
    try:
        result = subprocess.run(
            ['/usr/local/bin/ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0] if result.stdout else '未知版本'
            typer.echo(f"   ✅ 成功: {version_line[:80]}...")
        else:
            typer.echo(f"   ❌ 失败: returncode={result.returncode}")
            typer.echo(f"   stderr: {result.stderr[:200]}")
    except FileNotFoundError:
        typer.echo(f"   ❌ 文件不存在: /usr/local/bin/ffmpeg")
    except subprocess.TimeoutExpired:
        typer.echo(f"   ❌ 超时（5秒）")
    except Exception as e:
        typer.echo(f"   ❌ 异常: {str(e)}")
    
    # 4. 检查 /usr/local/bin 是否存在
    typer.echo(f"\n🔍 文件系统检查:")
    for bin_path in ['/usr/local/bin/ffmpeg', '/usr/local/bin/ffprobe', '/opt/homebrew/bin/ffmpeg', '/opt/homebrew/bin/ffprobe']:
        exists = os.path.exists(bin_path)
        typer.echo(f"   {bin_path}: {'✅ 存在' if exists else '❌ 不存在'}")
    
    typer.echo(f"\n{'='*60}\n")
    sys.stdout.flush()
    
    # 设置日志级别，抑制 numba 的 DEBUG 日志
    logging.getLogger('numba').setLevel(logging.WARNING)
    logging.getLogger('numba.core').setLevel(logging.WARNING)
    os.environ['NUMBA_LOG_LEVEL'] = 'WARNING'
    
    # 在 CLI 环境中禁用输出重定向，允许显示进度条
    os.environ['DISABLE_OUTPUT_REDIRECT'] = '1'
    
    typer.echo(f"🧪 开始测试 Whisper 转写功能")
    typer.echo(f"📁 音频文件: {audio_file}")
    
    # 检查文件是否存在
    if not os.path.exists(audio_file):
        typer.echo(f"❌ 错误: 文件不存在: {audio_file}", err=True)
        raise typer.Exit(code=1)
    
    file_size = os.path.getsize(audio_file)
    typer.echo(f"📊 文件大小: {file_size} 字节 ({file_size/1024:.2f} KB)")
    
    try:
        # 获取 WhisperService 实例
        typer.echo(f"\n🔍 步骤1: 获取 WhisperService 实例...")
        sys.stdout.flush()
        
        from creator.api.conversations.whisper_service import get_whisper_service
        
        typer.echo(f"   导入完成，正在获取实例...")
        sys.stdout.flush()
        
        whisper_service = get_whisper_service()
        
        typer.echo(f"✅ WhisperService 实例获取成功")
        typer.echo(f"   - use_local: {whisper_service.use_local}")
        typer.echo(f"   - model: {whisper_service.model is not None}")
        typer.echo(f"   - api_client: {whisper_service.api_client is not None}")
        sys.stdout.flush()
        
        if whisper_service.model is None:
            typer.echo(f"⚠️  警告: 模型未加载，可能需要一些时间加载模型...")
            sys.stdout.flush()
        
        # 调用转写
        typer.echo(f"\n🔍 步骤2: 开始转写...")
        typer.echo(f"   音频文件: {audio_file}")
        typer.echo(f"   语言: zh")
        typer.echo(f"   正在调用 transcribe()，请稍候...")
        sys.stdout.flush()
        
        start_time = time.time()
        
        if use_array:
            # 方案A：先用 ffmpeg 显式转 WAV，再用 soundfile 加载成数组，最后走 model.transcribe(array)
            typer.echo("   模式: 数组输入 (ffmpeg -> wav -> soundfile -> numpy)")
            sys.stdout.flush()
            import shutil
            import subprocess
            import soundfile as sf
            import numpy as np
            tmp_wav = os.path.join(os.path.dirname(audio_file) or ".", "_cli_tmp_16k.wav")
            ffmpeg_bin = shutil.which('ffmpeg') or '/usr/local/bin/ffmpeg'
            cmd = [ffmpeg_bin, '-y', '-i', audio_file, '-ar', '16000', '-ac', '1', tmp_wav]
            typer.echo("   转换命令: " + " ".join(cmd))
            sys.stdout.flush()
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if p.returncode != 0:
                    typer.echo("   ⚠️  ffmpeg 转换失败，stderr: " + (p.stderr or ""))
                    raise RuntimeError("ffmpeg 转换失败")
                data, sr = sf.read(tmp_wav, dtype='float32')
                if data.ndim > 1:
                    data = data.mean(axis=1)
                typer.echo(f"   wav 已加载: shape={data.shape}, sr={sr}")
                sys.stdout.flush()
                result = whisper_service.model.transcribe(
                    data, language="zh", fp16=False, verbose=False
                )
            finally:
                try:
                    os.path.exists(tmp_wav) and os.remove(tmp_wav)
                except Exception:
                    pass
        else:
            # 方案B：直接走服务层路径输入
            result = whisper_service.transcribe(
                audio_path=audio_file,
                language="zh",
                word_timestamps=True
            )
        
        elapsed_time = time.time() - start_time
        sys.stdout.flush()
        
        typer.echo(f"\n✅ 转写成功！")
        typer.echo(f"⏱️  耗时: {elapsed_time:.2f}秒")
        typer.echo(f"📝 转写文本: {result['text']}")
        typer.echo(f"⏱️  音频时长: {result.get('duration', 0):.2f}秒")
        typer.echo(f"🌐 识别语言: {result.get('language', 'unknown')}")
        
        if result.get('segments'):
            typer.echo(f"\n📊 分段信息:")
            for i, seg in enumerate(result['segments'][:5], 1):  # 只显示前5段
                typer.echo(f"   段{i}: [{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text'][:50]}...")
            if len(result['segments']) > 5:
                typer.echo(f"   ... 还有 {len(result['segments']) - 5} 段")
        
        typer.echo(f"\n🎉 测试完成！")
        
    except Exception as e:
        typer.echo(f"\n❌ 转写失败: {str(e)}", err=True)
        import traceback
        typer.echo(f"\n详细错误信息:", err=True)
        typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(code=1)


@app.command("bo_create_user")
def bo_create_user(name: str = typer.Option(..., "-n", "--name",
                                            help="Name of the user."),
                   password: str = typer.Option(..., prompt=True,
                                                hide_input=True,
                                                confirmation_prompt=True)):
    """Create a user."""
    # 延迟导入，避免对其他命令造成初始化开销
    from creator.db import sm as sa
    from creator.api.bo_user.models import BoUser
    from creator.api.bo_user.security import generate_hash_password

    with sa.transaction_scope() as db:
        u = BoUser.create(db, username=name,
                          password=generate_hash_password(password))
        typer.echo(f'Created user {name}: id {u.id}')


@app.command("bo_create_role")
def bo_create_role(name: str = typer.Option(..., "-n", "--name",
                                            help="Name of the role."),
                   description: str = typer.Option(None, "-d", "--description",
                                                   help="Description of the role.")):
    """Create a role."""
    # 延迟导入
    from creator.db import sm as sa
    from creator.api.bo_user.models import BoRole

    with sa.transaction_scope() as db:
        r = BoRole.create(db, name=name, description=description)
        typer.echo(f'Created role {name}: id {r.id}')


@app.command("bo_set_role")
def bo_set_role(
        user: str = typer.Option(..., "-u", "--user", help="Username."),
        role: str = typer.Option(..., "-r", "--role", help="Role name.")):
    """Set role of user."""
    # 延迟导入
    from creator.db import sm as sa
    from creator.api.bo_user.models import BoRole, BoUser

    with sa.transaction_scope() as db:
        r = db.query(BoRole).filter_by(name=role).first()
        if not r:
            typer.echo(f'Role "{role}" does not exist', err=True)
            raise typer.Exit(code=1)
        u = db.query(BoUser).filter_by(username=user).first()
        if not u:
            typer.echo(f'User "{user}" does not exist', err=True)
            raise typer.Exit(code=1)
        u.role = r
        typer.echo(f'Set role "{role}" to user "{user}"')


@app.command("bo_set_perm")
def bo_set_perm(
        role: str = typer.Option(..., "-r", "--role", help="Role name."),
        perm: list[str] = typer.Option(..., "-p", "--perm",
                                       help='Permissions to set. Use "all" for all permissions.')):
    """Set permissions of a role."""
    # 延迟导入
    from creator.db import sm as sa
    from creator.api.bo_user.models import BoRole
    from creator.api.constants import BoPermission

    with sa.transaction_scope() as db:
        r = db.query(BoRole).filter_by(name=role).first()
        if not r:
            typer.echo(f'Role "{role}" does not exist', err=True)
            raise typer.Exit(code=1)
        perms = BoPermission.__members__.keys() if 'all' in perm else perm
        for p in perms:
            r.add_perm(p)
        typer.echo(f'Set permissions {", ".join(perms)} to role "{role}"')



if __name__ == "__main__":
    app()
