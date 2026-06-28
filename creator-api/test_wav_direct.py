#!/usr/bin/env python
"""测试 WAV 格式是否可以直接转写（不卡住）"""

import os
import sys
import subprocess
import shutil

# 先创建一个 WAV 文件（从 webm 转换）
print("=" * 60)
print("🧪 WAV 格式直接转写测试")
print("=" * 60)

# 1. 使用已存在的 WAV 文件
wav_file = "./instance/audio_d56bd3103de047099500a0e3bdf9050a_converted.wav"

# 如果文件不存在，尝试转换
if not os.path.exists(wav_file):
    webm_file = "./instance/audio_d56bd3103de047099500a0e3bdf9050a.webm"
    if not os.path.exists(webm_file):
        print(f"❌ 源文件不存在: {webm_file}")
        sys.exit(1)
    
    print(f"\n📋 步骤1: 转换 webm 为 wav...")
    ffmpeg_bin = shutil.which('ffmpeg') or '/usr/local/bin/ffmpeg'
    print(f"   命令: {ffmpeg_bin} -i {webm_file} -ar 16000 -ac 1 {wav_file}")
    
    result = subprocess.run(
        [ffmpeg_bin, '-y', '-i', webm_file, '-ar', '16000', '-ac', '1', wav_file],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"❌ 转换失败: {result.stderr}")
        sys.exit(1)
    
    print(f"✅ WAV 文件创建成功: {wav_file}")
else:
    print(f"\n📋 步骤1: 使用已存在的 WAV 文件")
    print(f"   文件: {wav_file}")

print(f"   文件大小: {os.path.getsize(wav_file)} 字节")

# 2. 测试直接转写 WAV
print(f"\n📋 步骤2: 测试 WAV 格式直接转写...")
print(f"   这应该使用文件路径输入，不经过数组转换")

import time
from creator.api.conversations.whisper_service import get_whisper_service

# 设置 CLI 模式
os.environ['DISABLE_OUTPUT_REDIRECT'] = '1'

whisper_service = get_whisper_service()

print(f"\n📋 步骤3: 开始转写...")
start_time = time.time()

try:
    result = whisper_service.transcribe(
        audio_path=wav_file,
        language="zh",
        word_timestamps=True
    )
    
    elapsed_time = time.time() - start_time
    
    print(f"\n✅ 转写成功！")
    print(f"⏱️  耗时: {elapsed_time:.2f}秒")
    print(f"📝 转写文本: {result['text']}")
    print(f"⏱️  音频时长: {result.get('duration', 0):.2f}秒")
    print(f"🌐 识别语言: {result.get('language', 'unknown')}")
    
    if result.get('segments'):
        print(f"\n📊 分段信息:")
        for i, seg in enumerate(result['segments'][:3], 1):
            print(f"   段{i}: [{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text'][:50]}...")
    
    print(f"\n🎉 测试完成！")
    
except Exception as e:
    elapsed_time = time.time() - start_time
    print(f"\n❌ 转写失败（耗时: {elapsed_time:.2f}秒）")
    print(f"   错误: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    # 注意：不删除已存在的 converted.wav 文件，因为可能是其他测试产生的
    # 如果文件是临时创建的（不存在于 instance 目录），可以选择清理
    pass

