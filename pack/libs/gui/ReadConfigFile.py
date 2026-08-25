try:
    import tomllib
except ImportError:
    import tomli as tomllib
import tomli_w
import pathlib
from typing import *
import inspect

path = pathlib.Path(__file__).resolve().parent 
_config = None
_config_file = pathlib.Path(__file__).resolve().parent / "config.toml"
file_path = pathlib.Path(__file__).resolve().parent

def resolve_tilde_path(path: str, current_file: Union[str, pathlib.Path] = None) -> pathlib.Path:
    """
    将路径开头的 ~ 解析为当前文件所在目录
    
    :param path: 原始路径字符串
    :param current_file: 当前文件路径，默认为调用者的文件路径
    :return: 解析后的 Path 对象
    """
    if not path:
        return pathlib.Path()
    
    if path.startswith('~'):
        if current_file is None:
            import inspect
            frame = inspect.currentframe().f_back
            current_file = pathlib.Path(frame.f_code.co_filename)
        
        current_dir = pathlib.Path(current_file).resolve().parent
        relative_path = path[1:].lstrip('/\\')
        return current_dir / relative_path
    
    return pathlib.Path(path)


def _get_config() -> dict:
    """内部方法：获取配置对象（自动加载文件）"""
    global _config
    if _config is None:
        _config = {}
        if _config_file.exists():
            with open(_config_file, "rb") as f:
                _config = tomllib.load(f)
    return _config


def _save_config():
    """内部方法：保存配置到文件（立即写入磁盘）"""
    global _config
    if _config is not None:
        with open(_config_file, "wb") as f:
            tomli_w.dump(_config, f)


def set_config_value(section: str, key: str, value: str):
    """
    设置配置值（自动创建 section，立即写入文件）
    支持多行字符串，无需转义
    """
    config = _get_config()
    
    if section not in config:
        config[section] = {}
    
    config[section][key] = value
    _save_config()


def get_config_value(section: str, key: str, fallback: Optional[str] = None) -> Optional[str]:
    """
    获取配置值（如果不存在返回 fallback）
    多行字符串会保持原样
    """
    config = _get_config()
    try:
        return config.get(section, {}).get(key, fallback)
    except (KeyError, AttributeError):
        return fallback


def read_config_value(section: str, key: str) -> Optional[str]:
    """
    只读方法：直接从文件读取最新值（绕过内存缓存）
    适用于担心全局缓存不一致的场景
    """
    if not _config_file.exists():
        return None
    
    with open(_config_file, "rb") as f:
        config = tomllib.load(f)
    
    try:
        return config.get(section, {}).get(key)
    except (KeyError, AttributeError):
        return None