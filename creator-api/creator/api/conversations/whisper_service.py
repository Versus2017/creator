"""
Whisper 语音识别服务

提供语音转文字功能，支持：
1. 基础转写（短音频）
2. 智能分段转写（长音频）
3. 时间戳和分段信息

技术方案：
- 支持本地 Whisper 模型部署（推荐，数据私密）
- 支持 OpenAI Whisper API（备选）

本地部署（使用 faster-whisper）：
- 引擎：faster-whisper（基于 CTranslate2，速度快 4 倍）
- 模型：medium（准确率 96%+，1.5GB）
- 设备：M1/M2 Mac CPU 模式即可（速度很快）
- 首次运行会自动下载模型到 ~/.cache/huggingface/

依赖安装：
1. pip install faster-whisper
2. brew install ffmpeg（Mac）或 apt-get install ffmpeg（Linux）
"""

import logging
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import soundfile as sf

from ...config import config

logger = logging.getLogger(__name__)


def _resolve_binary(name: str) -> Optional[str]:
    """在常见路径中解析可执行文件的绝对路径"""
    try:
        path = shutil.which(name)
        if path:
            return path
    except Exception:
        pass
    for base in ["/usr/local/bin", "/opt/homebrew/bin", "/usr/bin", "/bin"]:
        candidate = os.path.join(base, name)
        if os.path.exists(candidate):
            return candidate
    return None

class WhisperService:
    """
    Whisper 语音识别服务（支持本地模型和 API）
    
    使用方法：
        service = WhisperService()
        result = service.transcribe(audio_path)
    """
    
    def __init__(self):
        """
        初始化 Whisper 服务
        
        根据配置选择本地模型或 API
        """
        self.use_local = config.WHISPER_USE_LOCAL
        self.model = None
        self.api_client = None
        
        if self.use_local:
            # 使用本地 Whisper 模型
            self.model_name = config.WHISPER_MODEL_NAME
            self.device = config.WHISPER_DEVICE
            self._load_local_model()
        else:
            # 使用 OpenAI API
            self.model_name = 'whisper-1'
            self._init_api_client()
    
    def _load_local_model(self):
        """
        加载本地 Whisper 模型（使用 faster-whisper）
        
        服务启动时会自动下载模型到 ~/.cache/huggingface/
        如果模型未下载，会立即触发下载（约 1.5GB，需要 5-10 分钟）
        """
        import sys
        import os
        
        # 配置 HuggingFace 镜像源（国内用户推荐）
        # 如果设置了 HF_ENDPOINT 环境变量，优先使用
        if not os.environ.get('HF_ENDPOINT'):
            # 使用国内镜像源（hf-mirror.com）
            os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
            logger.info(f"🌐 使用 HuggingFace 镜像源: https://hf-mirror.com")
        
        logger.info(f"🔍 [诊断] 开始加载 faster-whisper 模型")
        logger.info(f"🔍 [诊断] 模型名称: {self.model_name}")
        logger.info(f"🔍 [诊断] 设备: {self.device}")
        logger.info(f"🔍 [诊断] 计算类型: {config.WHISPER_COMPUTE_TYPE}")
        logger.info(f"🔍 [诊断] 当前进程ID: {os.getpid()}")
        
        try:
            from faster_whisper import WhisperModel
            logger.info(f"🔍 [诊断] faster_whisper 模块导入成功")
            
            logger.info(f"🚀 开始加载 faster-whisper 模型...")
            logger.info(f"   - 如果是首次运行，将自动从 HuggingFace 下载模型")
            logger.info(f"   - 下载位置: ~/.cache/huggingface/")
            logger.info("=" * 60)
            
            # 强制刷新输出
            sys.stdout.flush()
            sys.stderr.flush()
            
            logger.info(f"🔍 [诊断] 调用 WhisperModel()...")
            import time
            load_start = time.time()
            
            # 加载模型（首次会自动下载）
            # faster-whisper 会自动从 HuggingFace 下载 CTranslate2 格式的模型
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=config.WHISPER_COMPUTE_TYPE,
                download_root=None,  # 使用默认缓存目录
                local_files_only=False  # 允许下载
            )
            
            load_time = time.time() - load_start
            logger.info(f"🔍 [诊断] 模型加载完成，耗时: {load_time:.2f}秒")
            logger.info(f"🔍 [诊断] 模型对象类型: {type(self.model)}")
            logger.info(f"🔍 [诊断] 模型是否为 None: {self.model is None}")
            
            logger.info("=" * 60)
            logger.info(f"✅ faster-whisper 模型加载成功: {self.model_name}")
            logger.info(f"   - 引擎: faster-whisper (CTranslate2)")
            logger.info(f"   - 设备: {self.device}")
            logger.info(f"   - 计算类型: {config.WHISPER_COMPUTE_TYPE}")
            
            # 根据模型名称显示大小
            model_sizes = {
                'tiny': '~75MB',
                'base': '~145MB',
                'small': '~488MB',
                'medium': '~1.5GB',
                'large': '~3GB',
                'large-v2': '~3GB',
                'large-v3': '~3GB'
            }
            model_size = model_sizes.get(self.model_name, '未知')
            logger.info(f"   - 模型大小: {model_size}")
            logger.info(f"   - 准确率: 96%+")
            logger.info(f"   - 性能提升: 比 openai-whisper 快 4 倍 🚀")
            logger.info(f"   - 语音转文字服务已就绪！")
            
            # 强制刷新输出
            sys.stdout.flush()
            sys.stderr.flush()
            
        except ImportError:
            logger.error("❌ faster-whisper 未安装，请运行: pip install faster-whisper")
            logger.warning("将使用模拟模式")
            self.model = None
        except Exception as e:
            logger.error(f"❌ faster-whisper 模型加载失败: {str(e)}")
            logger.warning("将使用模拟模式")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            self.model = None
    
    def _init_api_client(self):
        """
        初始化 OpenAI API 客户端
        """
        try:
            from openai import OpenAI
            
            api_key = config.OPENAI_API_KEY
            if api_key:
                self.api_client = OpenAI(
                    api_key=api_key,
                    base_url=config.OPENAI_API_BASE,
                    timeout=config.WHISPER_API_TIMEOUT
                )
                logger.info(f"✅ OpenAI API 客户端初始化成功")
            else:
                logger.warning("⚠️ OpenAI API Key 未配置，将使用模拟模式")
        except Exception as e:
            logger.error(f"❌ OpenAI API 客户端初始化失败: {str(e)}")
    
    def transcribe(
        self, 
        audio_path: str,
        language: str = "zh",
        word_timestamps: bool = True
    ) -> Dict:
        """
        转写音频文件
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码（zh=中文, en=英文）
            word_timestamps: 是否返回词级时间戳（本地模型支持）
        
        Returns:
            {
                "text": "完整转写文本",
                "duration": 30.5,
                "language": "zh",
                "segments": [...]  # 本地模型返回详细分段，API 返回简化分段
            }
        """
        logger.info(f"开始转写: {audio_path}, 模式={'本地' if self.use_local else 'API'}")
        
        # 1. 检查文件是否存在
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        # 2. 获取音频时长（优先使用 ffprobe，支持所有格式包括 webm）
        duration = self._get_audio_duration(audio_path)
        
        # 3. 调用 faster-whisper 转写
        # faster-whisper 直接支持多种音频格式（通过 ffmpeg），无需预转换
        
        # 诊断：检查服务状态
        logger.info(f"🔍 [诊断] use_local={self.use_local}, model={self.model is not None}, api_client={self.api_client is not None}")
        
        if self.use_local and self.model:
            # 本地 faster-whisper 模型
            logger.info(f"🔍 [诊断] 使用 faster-whisper 模型进行转写")
            
            # faster-whisper 性能更好，直接使用文件路径即可
            # 不需要像 openai-whisper 那样的数组输入 workaround
            result = self._transcribe_with_local_model(audio_path, language, word_timestamps)
        elif self.api_client:
            # OpenAI API（支持 webm）
            logger.info(f"🔍 [诊断] 使用 OpenAI API 进行转写")
            result = self._transcribe_with_openai_api(audio_path, language)
            result['duration'] = duration
        else:
            # 如果没有可用的转写服务，抛出异常
            raise RuntimeError("Whisper 服务未正确初始化：模型未加载且 API 客户端未配置")
        
        logger.info(f"✅ 转写完成: 文本长度={len(result['text'])}, 时长={result.get('duration', 0):.2f}秒")
        
        return result
    
    def _transcribe_with_local_model(
        self, 
        audio_path: str,
        language: str,
        word_timestamps: bool = True
    ) -> Dict:
        """
        使用本地 Whisper 模型进行转写（faster-whisper）
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码（zh, en, ja, ko等）
            word_timestamps: 是否返回词级时间戳
        
        Returns:
            {
                "text": "转写文本",
                "duration": 30.5,
                "language": "zh",
                "segments": [...]  # 详细的分段信息
            }
        """
        try:
            # 导入必要的模块
            import time
            import os
            
            # 诊断：验证模型状态
            logger.info(f"🔍 [诊断] 开始转写检查")
            logger.info(f"🔍 [诊断] 模型对象类型: {type(self.model)}")
            logger.info(f"🔍 [诊断] 模型是否为 None: {self.model is None}")
            logger.info(f"🔍 [诊断] 音频文件路径: {audio_path}")
            logger.info(f"🔍 [诊断] 音频文件是否存在: {os.path.exists(audio_path)}")
            if os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                logger.info(f"🔍 [诊断] 音频文件大小: {file_size} 字节 ({file_size/1024:.2f} KB)")
            
            logger.info(f"调用 faster-whisper 模型: {audio_path}, language={language}")
            logger.info("⏳ faster-whisper 转写中（比原版快 4 倍）...")
            logger.info("   提示：medium 模型在 CPU 上，3秒音频约需 2.5-7.5 秒")
            
            # 调用 faster-whisper 模型
            # 参数说明：
            # - language: 指定语言可以提高准确率和速度
            # - word_timestamps: 返回词级时间戳（用于精确分段）
            # - beam_size: 束搜索大小，默认5（越大越准确但越慢）
            # - vad_filter: VAD过滤，自动去除静音部分
            # - condition_on_previous_text: False 可以提高速度
            
            start_time = time.time()
            logger.info(f"🔍 [诊断] 准备调用 model.transcribe()，时间: {start_time}")
            logger.info(f"🔍 [诊断] 参数: language={language}, word_timestamps={word_timestamps}, beam_size=5")
            
            logger.info(f"🔍 [诊断] 开始调用 transcribe()...")
            
            # faster-whisper 返回 (segments, info) 元组
            # segments 是一个生成器，需要遍历才能获取所有结果
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                beam_size=5,  # 束搜索大小，默认5
                word_timestamps=word_timestamps,
                vad_filter=False,  # 禁用 VAD 过滤（保持与原版一致）
                condition_on_previous_text=False  # 禁用上下文依赖，提高速度
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"🔍 [诊断] transcribe() 调用完成（返回生成器），耗时: {elapsed_time:.2f}秒")
            
            # 诊断：检查返回结果
            logger.info(f"🔍 [诊断] info 类型: {type(info)}")
            logger.info(f"🔍 [诊断] segments 类型: {type(segments)}")
            logger.info(f"🔍 [诊断] 检测到的语言: {info.language}")
            logger.info(f"🔍 [诊断] 语言概率: {info.language_probability:.2f}")
            logger.info(f"🔍 [诊断] 音频时长: {info.duration:.2f}秒")
            
            # 遍历生成器，收集所有分段
            logger.info("🔍 [诊断] 开始遍历 segments 生成器...")
            segment_start = time.time()
            
            all_text = []
            all_segments = []
            
            for seg in segments:
                all_text.append(seg.text)
                all_segments.append({
                    "id": seg.id,
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip()
                })
            
            segment_time = time.time() - segment_start
            logger.info(f"🔍 [诊断] segments 遍历完成，耗时: {segment_time:.2f}秒")
            logger.info(f"🔍 [诊断] 获取到 {len(all_segments)} 个分段")
            
            total_time = time.time() - start_time
            logger.info(f"⏱️ faster-whisper 总耗时: {total_time:.2f}秒")
            
            # 构建返回结果
            output = {
                "text": "".join(all_text).strip(),
                "duration": info.duration,
                "language": info.language,
                "segments": all_segments
            }
            
            logger.info(f"✅ faster-whisper 转写成功: 文本长度={len(output['text'])}")
            return output
            
        except Exception as e:
            logger.error(f"❌ faster-whisper 转写失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            raise
    
    def _transcribe_with_openai_api(
        self, 
        audio_path: str,
        language: str
    ) -> Dict:
        """
        使用 OpenAI Whisper API 进行转写
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码（zh, en, ja, ko等）
        
        Returns:
            {
                "text": "转写文本",
                "language": "zh",
                "segments": []
            }
        """
        try:
            logger.info(f"调用 OpenAI Whisper API: {audio_path}, language={language}")
            
            # 1. 检查文件大小（OpenAI API 限制 25MB）
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            if file_size_mb > 25:
                raise ValueError(f"音频文件过大: {file_size_mb:.2f}MB，OpenAI API 限制为 25MB")
            
            # 2. 打开音频文件
            with open(audio_path, "rb") as audio_file:
                # 3. 调用 Whisper API
                # API 文档: https://platform.openai.com/docs/api-reference/audio/createTranscription
                transcript = self.api_client.audio.transcriptions.create(
                    model=self.model_name,
                    file=audio_file,
                    language=language if language != "zh" else "zh",  # 中文使用 "zh"
                    response_format="verbose_json",  # 获取详细信息（包含时间戳）
                    timestamp_granularities=["segment"]  # 获取分段级别的时间戳
                )
            
            # 4. 解析结果
            result = {
                "text": transcript.text,
                "language": transcript.language or language,
                "segments": []
            }
            
            # 5. 提取分段信息（如果有）
            if hasattr(transcript, 'segments') and transcript.segments:
                result['segments'] = [
                    {
                        'id': seg.id,
                        'start': seg.start,
                        'end': seg.end,
                        'text': seg.text
                    }
                    for seg in transcript.segments
                ]
                logger.info(f"获取到 {len(result['segments'])} 个分段")
            
            logger.info(f"OpenAI Whisper API 转写成功: 文本长度={len(result['text'])}")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI Whisper API 转写失败: {str(e)}")
            raise
    
    def _convert_audio_if_needed(self, audio_path: str) -> str:
        """
        如果需要，将音频转换为 wav 格式
        
        Args:
            audio_path: 原始音频文件路径
        
        Returns:
            str: 转换后的音频文件路径（如果不需要转换，返回原路径）
        """
        file_ext = Path(audio_path).suffix.lower()
        
        # 如果已经是 wav 格式，不需要转换
        if file_ext == '.wav':
            return audio_path
        
        # 对于 webm、ogg 等格式，转换为 wav 以提高兼容性
        # 注意：Whisper 本身支持多种格式，但 soundfile 可能不支持某些格式
        if file_ext in ['.webm', '.ogg', '.m4a']:
            logger.info(f"检测到 {file_ext} 格式，转换为 wav 格式以提高兼容性")
            
            try:
                # 使用 ffmpeg 转换音频格式
                # 检查 ffmpeg 是否可用
                try:
                    ffmpeg_bin = _resolve_binary('ffmpeg') or 'ffmpeg'
                    subprocess.run([ffmpeg_bin, '-version'], 
                                 capture_output=True, 
                                 check=True, 
                                 timeout=5)
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    logger.warning("ffmpeg 未安装或不可用，跳过格式转换")
                    logger.warning("Whisper 应该能直接处理此格式，但如果出现问题请安装 ffmpeg")
                    return audio_path
                
                # 创建临时 wav 文件
                temp_dir = os.path.dirname(audio_path)
                temp_wav_path = os.path.join(
                    temp_dir, 
                    f"{Path(audio_path).stem}_converted.wav"
                )
                
                # 使用 ffmpeg 转换：转换为 16kHz 单声道 wav（Whisper 推荐格式）
                cmd = [
                    _resolve_binary('ffmpeg') or 'ffmpeg',
                    '-i', audio_path,      # 输入文件
                    '-ar', '16000',        # 采样率 16kHz（Whisper 标准）
                    '-ac', '1',            # 单声道
                    '-y',                   # 覆盖已存在的文件
                    temp_wav_path          # 输出文件
                ]
                
                logger.info(f"执行转换命令: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
                
                if result.returncode != 0:
                    logger.error(f"ffmpeg 转换失败: {result.stderr}")
                    logger.warning("转换失败，尝试使用原始文件")
                    return audio_path
                
                if not os.path.exists(temp_wav_path):
                    logger.error("转换后的文件不存在")
                    return audio_path
                
                logger.info(f"✅ 音频格式转换成功: {temp_wav_path}")
                return temp_wav_path
                
            except subprocess.TimeoutExpired:
                logger.error("ffmpeg 转换超时")
                return audio_path
            except Exception as e:
                logger.error(f"音频格式转换失败: {str(e)}")
                logger.warning("转换失败，尝试使用原始文件")
                return audio_path
        
        # 其他格式直接返回原路径
        return audio_path
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """
        获取音频时长
        
        优先使用 ffprobe（支持所有格式包括 webm），
        如果不支持则使用 soundfile（仅支持 wav/flac/ogg 等）
        
        Args:
            audio_path: 音频文件路径
        
        Returns:
            float: 音频时长（秒）
        """
        file_ext = Path(audio_path).suffix.lower()
        
        # 对于 webm、m4a 等格式，直接使用 ffprobe（soundfile 不支持）
        if file_ext in ['.webm', '.m4a', '.mp3', '.aac']:
            return self._get_duration_with_ffprobe(audio_path)
        
        # 对于 wav、flac、ogg 等格式，优先使用 soundfile（更快）
        try:
            info = sf.info(audio_path)
            duration = info.duration
            logger.info(f"使用 soundfile 获取音频时长: {duration:.2f}秒")
            return duration
        except Exception as e:
            logger.warning(f"soundfile 获取时长失败: {str(e)}，尝试使用 ffprobe")
            return self._get_duration_with_ffprobe(audio_path)
    
    def _get_duration_with_ffprobe(self, audio_path: str) -> float:
        """
        使用 ffprobe 获取音频时长（支持所有格式）
        
        Args:
            audio_path: 音频文件路径
        
        Returns:
            float: 音频时长（秒）
        """
        try:
            cmd = [
                _resolve_binary('ffprobe') or 'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                audio_path
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                duration = float(result.stdout.strip())
                logger.info(f"使用 ffprobe 获取音频时长: {duration:.2f}秒")
                return duration
            else:
                raise ValueError(f"ffprobe 返回空结果: {result.stderr}")
        except FileNotFoundError:
            logger.warning("ffprobe 未安装，无法获取准确时长")
            # 降级到文件大小估算
            return self._estimate_duration_by_size(audio_path)
        except Exception as e:
            logger.warning(f"ffprobe 获取时长失败: {str(e)}")
            # 降级到文件大小估算
            return self._estimate_duration_by_size(audio_path)
    
    def _estimate_duration_by_size(self, audio_path: str) -> float:
        """
        根据文件大小估算音频时长（降级方案）
        
        Args:
            audio_path: 音频文件路径
        
        Returns:
            float: 估算的音频时长（秒）
        """
        try:
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            # webm 压缩率较高，1MB ≈ 120秒（取决于码率）
            # 这是一个粗略估算，实际时长可能差异较大
            estimated_duration = file_size_mb * 120
            logger.warning(f"使用估算的音频时长: {estimated_duration:.2f}秒（不准确，建议安装 ffmpeg）")
            return estimated_duration
        except Exception as e:
            logger.error(f"获取音频时长失败: {str(e)}")
            return 0.0
    
    def transcribe_with_segments(
        self,
        audio_path: str,
        max_segment_duration: int = 180,
        language: str = "zh"
    ) -> Dict:
        """
        转写长音频并智能分段
        
        Args:
            audio_path: 音频文件路径
            max_segment_duration: 单段最大时长（秒），默认3分钟
            language: 语言代码
        
        Returns:
            {
                "text": "完整转写文本",
                "duration": 600,
                "segments": {
                    "segment_count": 3,
                    "total_duration": 600,
                    "segments": [
                        {
                            "index": 0,
                            "start_time": 0.0,
                            "end_time": 180.5,
                            "text": "第一段文本...",
                            "duration": 180.5,
                            "word_count": 256
                        },
                        ...
                    ]
                }
            }
        """
        logger.info(f"开始分段转写: {audio_path}")
        
        # 1. 先进行完整转写
        result = self.transcribe(audio_path, language=language, word_timestamps=True)
        
        # 2. 如果音频较短（<5分钟），不需要分段
        if result['duration'] < 300:
            logger.info("音频较短，不需要分段")
            return result
        
        # 3. 智能分段
        if result.get('segments'):
            # 使用 Whisper 的原始分段进行智能合并
            segmented = self._smart_segment(
                result['segments'],
                result['duration'],
                max_segment_duration
            )
        else:
            # 如果没有分段信息，简单按时间切分
            segmented = self._simple_segment(
                result['text'],
                result['duration'],
                max_segment_duration
            )
        
        result['segments'] = segmented
        
        logger.info(f"分段完成: 共{segmented['segment_count']}段")
        
        return result
    
    def _smart_segment(
        self,
        whisper_segments: List[Dict],
        total_duration: float,
        max_segment_duration: int
    ) -> Dict:
        """
        智能分段：基于 Whisper 的时间戳和停顿
        
        策略：
        1. 检测长停顿（>2秒）作为分段点
        2. 单段不超过 max_segment_duration
        3. 最终控制在 3-5 段
        """
        segments = []
        current_start = 0
        accumulated_text = ""
        accumulated_duration = 0
        
        for i, seg in enumerate(whisper_segments):
            seg_duration = seg['end'] - seg['start']
            
            # 检测条件1：长停顿
            pause_duration = 0
            if i < len(whisper_segments) - 1:
                pause_duration = whisper_segments[i + 1]['start'] - seg['end']
            
            # 检测条件2：时长超限
            if accumulated_duration + seg_duration > max_segment_duration or pause_duration > 2.0:
                if accumulated_text:
                    segments.append({
                        'index': len(segments),
                        'start_time': current_start,
                        'end_time': seg['end'],
                        'text': accumulated_text.strip(),
                        'duration': accumulated_duration,
                        'word_count': len(accumulated_text)
                    })
                
                # 开始新段
                current_start = seg['end'] if pause_duration > 2.0 else seg['start']
                accumulated_text = "" if pause_duration > 2.0 else seg['text']
                accumulated_duration = 0 if pause_duration > 2.0 else seg_duration
            else:
                accumulated_text += " " + seg['text']
                accumulated_duration += seg_duration
        
        # 最后一段
        if accumulated_text:
            segments.append({
                'index': len(segments),
                'start_time': current_start,
                'end_time': whisper_segments[-1]['end'],
                'text': accumulated_text.strip(),
                'duration': accumulated_duration,
                'word_count': len(accumulated_text)
            })
        
        return {
            'segment_count': len(segments),
            'total_duration': total_duration,
            'segments': segments
        }
    
    def _simple_segment(
        self,
        text: str,
        duration: float,
        max_segment_duration: int
    ) -> Dict:
        """
        简单分段：按时间均分
        
        当没有 Whisper 时间戳时使用
        """
        segment_count = max(1, int(duration / max_segment_duration) + 1)
        text_length = len(text)
        segment_text_length = text_length // segment_count
        
        segments = []
        for i in range(segment_count):
            start_idx = i * segment_text_length
            end_idx = (i + 1) * segment_text_length if i < segment_count - 1 else text_length
            segment_text = text[start_idx:end_idx]
            
            segments.append({
                'index': i,
                'start_time': i * max_segment_duration,
                'end_time': min((i + 1) * max_segment_duration, duration),
                'text': segment_text,
                'duration': min(max_segment_duration, duration - i * max_segment_duration),
                'word_count': len(segment_text)
            })
        
        return {
            'segment_count': len(segments),
            'total_duration': duration,
            'segments': segments
        }


# 单例实例
_whisper_service = None


def get_whisper_service() -> WhisperService:
    """
    获取 WhisperService 单例
    
    使用单例模式避免重复创建 OpenAI 客户端
    """
    global _whisper_service
    if _whisper_service is None:
        _whisper_service = WhisperService()
    return _whisper_service

