import os
from datetime import datetime
from pathlib import Path
from typing import Any


# Environment variable loading
# Go up from tools/ -> jira_ai_assistant/ -> src/ -> jira_ai_assistant/ -> project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
ENV_LOCATIONS = [BASE_DIR / "jira_ai_assistant" / ".env", BASE_DIR / ".env"]


def _load_env_file(env_path: Path) -> None:
    """
    Load environment variables from a .env file if present.
    Existing environment values are left untouched so external config can override.
    """
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Strip optional surrounding quotes
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        if key and key not in os.environ:
            os.environ[key] = value


def load_jira_env() -> None:
    """
    Load environment variables from .env files.
    This function should be called at module import time.
    """
    for env_file in ENV_LOCATIONS:
        _load_env_file(env_file)


def _extract_text_from_adf(adf_content: Any) -> str:
    """
    Helper function to extract plain text from Atlassian Document Format (ADF).
    
    Args:
        adf_content: ADF content structure (dict or list)
    
    Returns:
        str: Plain text extracted from ADF
    """
    if not adf_content:
        return ""
    
    if isinstance(adf_content, str):
        return adf_content
    
    if isinstance(adf_content, dict):
        if adf_content.get("type") == "text":
            return adf_content.get("text", "")
        if "content" in adf_content:
            return _extract_text_from_adf(adf_content["content"])
    
    if isinstance(adf_content, list):
        return " ".join(_extract_text_from_adf(item) for item in adf_content)
    
    return ""


def _format_date(date_str: str) -> str:
    """
    Helper function to format ISO date string to DD/MM/YYYY format.
    
    Args:
        date_str: ISO date string (e.g., '2025-08-17T10:00:00.000+0000')
    
    Returns:
        str: Formatted date string (e.g., '17/08/2025')
    """
    if not date_str:
        return ""
    
    try:
        # Parse ISO format date
        dt = datetime.fromisoformat(date_str.replace('+0000', '+00:00').replace('Z', '+00:00'))
        return dt.strftime("%d/%m/%Y")
    except (ValueError, AttributeError):
        return date_str

