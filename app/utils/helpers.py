"""
Utility helper functions for the Multi-Agent Startup Simulator.
"""

import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import asyncio

from .logger import get_logger

logger = get_logger(__name__)


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    return f"{prefix}{uuid.uuid4().hex}"


def hash_string(text: str) -> str:
    """Generate SHA256 hash of a string."""
    return hashlib.sha256(text.encode()).hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters."""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string."""
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse datetime from string."""
    return datetime.strptime(dt_str, format_str)


def calculate_time_diff(start: datetime, end: datetime) -> Dict[str, int]:
    """Calculate time difference in various units."""
    diff = end - start
    return {
        "days": diff.days,
        "hours": diff.seconds // 3600,
        "minutes": (diff.seconds % 3600) // 60,
        "seconds": diff.seconds % 60,
        "total_seconds": diff.total_seconds()
    }


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length with suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def split_text_into_chunks(text: str, chunk_size: int, overlap: int = 0) -> List[str]:
    """Split text into chunks with optional overlap."""
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap if overlap > 0 else end

    return chunks


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries."""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def deep_merge_dicts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()

    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON string."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"Failed to parse JSON: {json_str}")
        return default


def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """Safely serialize to JSON string."""
    try:
        return json.dumps(data, indent=2, default=str)
    except (TypeError, ValueError):
        logger.warning(f"Failed to serialize to JSON: {data}")
        return default


def read_file_content(file_path: Union[str, Path], encoding: str = "utf-8") -> Optional[str]:
    """Read file content safely."""
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            return path.read_text(encoding=encoding)
        return None
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None


def write_file_content(file_path: Union[str, Path], content: str, encoding: str = "utf-8") -> bool:
    """Write content to file safely."""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
        return True
    except Exception as e:
        logger.error(f"Error writing to file {file_path}: {e}")
        return False


def find_files_by_extension(directory: Union[str, Path], extensions: List[str]) -> List[Path]:
    """Find files by extensions in directory recursively."""
    path = Path(directory)
    if not path.exists():
        return []

    files = []
    for ext in extensions:
        files.extend(path.rglob(f"*{ext}"))

    return files


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity using Jaccard similarity."""
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    return intersection / union if union > 0 else 0.0


async def async_timeout(coro, timeout: float):
    """Run coroutine with timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {timeout} seconds")
        return None


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def format_currency(amount: Union[int, float], currency: str = "$") -> str:
    """Format amount as currency."""
    return f"{currency}{amount:,.2f}"


def calculate_percentage(part: Union[int, float], total: Union[int, float]) -> float:
    """Calculate percentage."""
    if total == 0:
        return 0.0
    return (part / total) * 100


def is_valid_url(url: str) -> bool:
    """Validate URL format."""
    pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))*)?$'
    return re.match(pattern, url) is not None


class LoggerMixin:
    """Mixin class that provides logging functionality."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger(self.__class__.__name__)