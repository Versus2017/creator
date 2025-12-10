"""
开源版占位提示词。真实提示词请放在同目录的 `local_prompts.py`（已被 .gitignore 忽略）。
如果存在本地文件，会自动加载；否则返回占位内容，提示开发者补充。
"""

from importlib import util
from pathlib import Path
from typing import Any, Dict, List

_LOCAL_MESSAGE = "本地提示词未提供，请在 local_prompts.py 中配置。"
LOCAL_PROMPTS_LOADED = False


def get_conversation_system_prompt(topic: str, user_profile: dict = None) -> str:
    return _LOCAL_MESSAGE


def get_script_generation_prompt(
    topic: str,
    format_type: str,
    requirements: str = None,
    style_context: str = None,
    conversation_context: List[Dict[str, Any]] = None,
) -> str:
    return _LOCAL_MESSAGE


SCENE_PROMPTS: Dict[str, str] = {}


def get_conversation_title_prompt(first_message: str) -> str:
    return _LOCAL_MESSAGE


def get_optimization_prompt(script_content: str, optimization_type: str) -> str:
    return _LOCAL_MESSAGE


def get_script_extraction_prompt(conversation_messages: list) -> str:
    return _LOCAL_MESSAGE


def get_refinement_prompt(raw_text: str, conversation_context: str = "", audio_duration: int = 0) -> str:
    return _LOCAL_MESSAGE


def get_user_profile_analysis_prompt(introduction: str) -> str:
    return _LOCAL_MESSAGE


def get_research_system_prompt(script_content: str, script_title: str, performance_data: dict = None) -> str:
    return _LOCAL_MESSAGE


def get_research_initial_message(script_title: str, performance_data: dict = None) -> str:
    return _LOCAL_MESSAGE


def get_research_analysis_prompt(
    script_content: str,
    script_title: str,
    conversation_history: list,
    user_feedback_summary: str = None,
) -> str:
    return _LOCAL_MESSAGE


def get_research_summary_prompt(
    script_title: str,
    key_findings: list,
    ai_analysis: dict,
    user_feedback: dict = None,
) -> str:
    return _LOCAL_MESSAGE


def get_style_profile_update_prompt(user_existing_profile: dict, new_research: dict) -> str:
    return _LOCAL_MESSAGE


def get_research_analyze_prompt(script_title: str, script_content: str, dialogue_text: str) -> str:
    return _LOCAL_MESSAGE


def _load_local_prompts():
    local_path = Path(__file__).with_name("local_prompts.py")
    if not local_path.exists():
        return None
    spec = util.spec_from_file_location("creator.api.conversations.local_prompts", local_path)
    if not spec or not spec.loader:
        return None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_local_module = _load_local_prompts()
if _local_module:
    LOCAL_PROMPTS_LOADED = True
    globals().update({k: getattr(_local_module, k) for k in dir(_local_module) if not k.startswith("_")})
