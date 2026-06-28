#!/usr/bin/env python
"""Whisper ffmpeg 调用问题排查脚本

用于逐步排查为什么 Whisper 内部调用 ffmpeg 会卡住
"""

import os
import sys
import time
import subprocess
import signal
import threading
from pathlib import Path

def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}\n")

def test_ffmpeg_basic():
    """测试1: 基础 ffmpeg 调用测试"""
    print_section("测试1: 基础 ffmpeg 调用")
    
    ffmpeg_path = "/usr/local/bin/ffmpeg"
    
    tests = [
        ("直接调用 -version", [ffmpeg_path, '-version']),
        ("shell=True 调用", ffmpeg_path + ' -version'),
        ("使用 Popen", [ffmpeg_path, '-version']),
    ]
    
    for name, cmd in tests:
        print(f"\n📋 测试: {name}")
        print(f"   命令: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
        
        start_time = time.time()
        timeout_occurred = False
        
        def timeout_handler(signum, frame):
            nonlocal timeout_occurred
            timeout_occurred = True
            print(f"   ⚠️  超时（5秒）")
        
        try:
            if isinstance(cmd, str):
                # shell=True
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            elif name == "使用 Popen":
                # Popen + communicate
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                try:
                    stdout, stderr = proc.communicate(timeout=5)
                    result = type('obj', (object,), {'returncode': proc.returncode, 'stdout': stdout, 'stderr': stderr})()
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                    raise
            else:
                # 普通 subprocess.run
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            
            elapsed = time.time() - start_time
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0] if result.stdout else '未知'
                print(f"   ✅ 成功（耗时: {elapsed:.2f}秒）")
                print(f"   版本: {version_line[:60]}...")
            else:
                print(f"   ❌ 失败: returncode={result.returncode}")
                if result.stderr:
                    print(f"   stderr: {result.stderr[:200]}")
                    
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            print(f"   ❌ 超时（耗时: {elapsed:.2f}秒）")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   ❌ 异常: {str(e)}（耗时: {elapsed:.2f}秒）")

def test_ffmpeg_permissions():
    """测试2: 检查 ffmpeg 权限和属性"""
    print_section("测试2: ffmpeg 权限和属性检查")
    
    ffmpeg_path = "/usr/local/bin/ffmpeg"
    
    # 检查文件是否存在
    print(f"📋 文件存在性:")
    print(f"   {ffmpeg_path}: {'✅ 存在' if os.path.exists(ffmpeg_path) else '❌ 不存在'}")
    
    # 检查文件权限
    if os.path.exists(ffmpeg_path):
        stat_info = os.stat(ffmpeg_path)
        print(f"\n📋 文件权限:")
        print(f"   mode: {oct(stat_info.st_mode)}")
        print(f"   uid: {stat_info.st_uid}")
        print(f"   gid: {stat_info.st_gid}")
        print(f"   可读: {'✅' if os.access(ffmpeg_path, os.R_OK) else '❌'}")
        print(f"   可写: {'✅' if os.access(ffmpeg_path, os.W_OK) else '❌'}")
        print(f"   可执行: {'✅' if os.access(ffmpeg_path, os.X_OK) else '❌'}")
        
        # 检查 macOS 扩展属性
        print(f"\n📋 macOS 扩展属性:")
        try:
            result = subprocess.run(
                ['xattr', '-l', ffmpeg_path],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0 and result.stdout.strip():
                print(f"   {result.stdout}")
            else:
                print(f"   ✅ 无扩展属性")
        except Exception as e:
            print(f"   ⚠️  检查失败: {e}")
        
        # 检查代码签名
        print(f"\n📋 代码签名:")
        try:
            result = subprocess.run(
                ['codesign', '-dv', ffmpeg_path],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0:
                print(f"   {result.stderr}")  # codesign 输出到 stderr
            else:
                print(f"   ⚠️  未签名或检查失败")
        except Exception as e:
            print(f"   ⚠️  检查失败: {e}")

def test_ffmpeg_dependencies():
    """测试3: 检查 ffmpeg 依赖"""
    print_section("测试3: ffmpeg 依赖检查")
    
    ffmpeg_path = "/usr/local/bin/ffmpeg"
    
    if not os.path.exists(ffmpeg_path):
        print("❌ ffmpeg 文件不存在，跳过依赖检查")
        return
    
    # macOS 使用 otool 检查依赖
    print(f"📋 动态库依赖:")
    try:
        result = subprocess.run(
            ['otool', '-L', ffmpeg_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            libs = result.stdout.strip().split('\n')[1:]  # 跳过第一行（文件路径）
            print(f"   找到 {len(libs)} 个依赖库:")
            for lib in libs[:10]:  # 只显示前10个
                print(f"   - {lib.strip()}")
            if len(libs) > 10:
                print(f"   ... 还有 {len(libs) - 10} 个")
        else:
            print(f"   ⚠️  检查失败: {result.stderr}")
    except Exception as e:
        print(f"   ⚠️  检查失败: {e}")

def test_whisper_internal_call():
    """测试4: 模拟 Whisper 内部调用"""
    print_section("测试4: 模拟 Whisper 内部调用")
    
    audio_file = "./instance/audio_d56bd3103de047099500a0e3bdf9050a.webm"
    
    if not os.path.exists(audio_file):
        print(f"❌ 音频文件不存在: {audio_file}")
        print("   请先运行: python -m creator.cli test_whisper")
        return
    
    print(f"📋 测试音频文件:")
    print(f"   路径: {audio_file}")
    print(f"   大小: {os.path.getsize(audio_file)} 字节")
    
    # 导入 whisper
    print(f"\n📋 加载 Whisper 模型...")
    try:
        import whisper
        print(f"   ✅ whisper 模块导入成功")
        
        model = whisper.load_model("base", device="cpu")
        print(f"   ✅ 模型加载成功")
        
        # 测试文件路径输入（会触发内部 ffmpeg 调用）
        print(f"\n📋 测试文件路径输入（会触发内部 ffmpeg）:")
        print(f"   这是会卡住的调用方式...")
        print(f"   如果这里卡住，说明 Whisper 内部调用 ffmpeg 有问题")
        
        start_time = time.time()
        print(f"   开始时间: {start_time}")
        sys.stdout.flush()
        
        # 设置超时（使用线程）
        timeout_occurred = [False]
        
        def timeout_handler():
            time.sleep(10)  # 等待10秒
            if not timeout_occurred[0]:
                timeout_occurred[0] = True
                print(f"\n   ⚠️  已等待10秒，可能卡住了...")
                print(f"   按 Ctrl+C 中断")
                sys.stdout.flush()
        
        timer = threading.Timer(10.0, timeout_handler)
        timer.start()
        
        try:
            result = model.transcribe(
                audio_file,
                language="zh",
                verbose=False,
                fp16=False
            )
            timer.cancel()
            
            elapsed = time.time() - start_time
            print(f"\n   ✅ 成功完成（耗时: {elapsed:.2f}秒）")
            print(f"   转写文本: {result['text'][:50]}...")
        except KeyboardInterrupt:
            timer.cancel()
            elapsed = time.time() - start_time
            print(f"\n   ❌ 用户中断（耗时: {elapsed:.2f}秒）")
        except Exception as e:
            timer.cancel()
            elapsed = time.time() - start_time
            print(f"\n   ❌ 异常: {str(e)}（耗时: {elapsed:.2f}秒）")
            import traceback
            traceback.print_exc()
            
    except ImportError:
        print(f"   ❌ whisper 模块未安装")
    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

def test_environment_variables():
    """测试5: 检查环境变量"""
    print_section("测试5: 环境变量检查")
    
    print(f"📋 PATH 环境变量:")
    path = os.environ.get('PATH', '')
    print(f"   {path}")
    
    print(f"\n📋 关键环境变量:")
    key_vars = [
        'PATH', 'HOME', 'USER', 'SHELL',
        'DYLD_LIBRARY_PATH', 'LD_LIBRARY_PATH',
        'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
        'TORCH_NUM_THREADS'
    ]
    for var in key_vars:
        value = os.environ.get(var, '未设置')
        print(f"   {var}: {value}")

def main():
    """主函数"""
    print("="*60)
    print("🔍 Whisper ffmpeg 调用问题排查脚本")
    print("="*60)
    print("\n这个脚本将逐步排查为什么 Whisper 内部调用 ffmpeg 会卡住")
    print("请按照提示进行测试，并记录结果\n")
    
    input("按 Enter 开始测试...")
    
    # 测试1: 基础 ffmpeg 调用
    test_ffmpeg_basic()
    
    input("\n按 Enter 继续下一个测试...")
    
    # 测试2: 权限检查
    test_ffmpeg_permissions()
    
    input("\n按 Enter 继续下一个测试...")
    
    # 测试3: 依赖检查
    test_ffmpeg_dependencies()
    
    input("\n按 Enter 继续下一个测试...")
    
    # 测试4: Whisper 内部调用（这个可能会卡住）
    print("\n⚠️  警告: 下一个测试可能会卡住")
    print("   如果卡住，请按 Ctrl+C 中断")
    input("   按 Enter 继续（或 Ctrl+C 跳过）...")
    
    try:
        test_whisper_internal_call()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    
    input("\n按 Enter 继续最后一个测试...")
    
    # 测试5: 环境变量
    test_environment_variables()
    
    print("\n" + "="*60)
    print("✅ 排查完成")
    print("="*60)
    print("\n请将以上所有测试结果记录到文档中，便于进一步分析")

if __name__ == "__main__":
    main()

