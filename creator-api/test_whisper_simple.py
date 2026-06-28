#!/usr/bin/env python
"""简单的 Whisper 转写测试脚本"""
import os
import sys
import time

# 设置日志级别
import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('numba').setLevel(logging.WARNING)
logging.getLogger('numba.core').setLevel(logging.WARNING)
os.environ['NUMBA_LOG_LEVEL'] = 'WARNING'

print("=" * 60)
print("🧪 简单 Whisper 转写测试")
print("=" * 60)

# 音频文件路径
audio_file = "./instance/audio_d56bd3103de047099500a0e3bdf9050a.webm"

print(f"\n📁 步骤1: 检查音频文件...")
if not os.path.exists(audio_file):
    print(f"❌ 错误: 文件不存在: {audio_file}")
    sys.exit(1)

file_size = os.path.getsize(audio_file)
print(f"✅ 文件存在，大小: {file_size} 字节 ({file_size/1024:.2f} KB)")
sys.stdout.flush()

print(f"\n📦 步骤2: 导入 whisper 模块...")
try:
    import whisper
    print(f"✅ whisper 模块导入成功")
except ImportError as e:
    print(f"❌ whisper 模块导入失败: {e}")
    sys.exit(1)
sys.stdout.flush()

print(f"\n📦 步骤3: 加载 Whisper 模型 (base)...")
print(f"   提示: 首次运行可能需要下载模型，请耐心等待...")
sys.stdout.flush()

try:
    start_time = time.time()
    model = whisper.load_model("base", device="cpu")
    load_time = time.time() - start_time
    print(f"✅ 模型加载成功，耗时: {load_time:.2f}秒")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
sys.stdout.flush()

print(f"\n🎤 步骤4: 开始转写...")
print(f"   音频文件: {audio_file}")
print(f"   语言: zh")
print(f"   请稍候，转写中...")
sys.stdout.flush()

try:
    start_time = time.time()
    result = model.transcribe(
        audio_file,
        language="zh",
        verbose=False,
        fp16=False
    )
    elapsed_time = time.time() - start_time
    
    print(f"\n✅ 转写完成！")
    print(f"⏱️  耗时: {elapsed_time:.2f}秒")
    print(f"📝 转写文本: {result['text']}")
    print(f"⏱️  音频时长: {result.get('duration', 0):.2f}秒")
    print(f"🌐 识别语言: {result.get('language', 'unknown')}")
    
    if result.get('segments'):
        print(f"\n📊 分段信息 (前5段):")
        for i, seg in enumerate(result['segments'][:5], 1):
            print(f"   段{i}: [{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text'][:50]}...")
        if len(result['segments']) > 5:
            print(f"   ... 还有 {len(result['segments']) - 5} 段")
    
    print(f"\n🎉 测试完成！")
    
except Exception as e:
    print(f"\n❌ 转写失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

