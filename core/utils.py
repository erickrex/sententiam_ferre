"""
Utility functions for the core application.
"""
import re
import unicodedata


def derive_filename_from_description(description: str, version: int = 1, extension: str = 'png') -> str:
    """
    Derive a descriptive filename from a character description.
    
    This function converts a character description into a safe, descriptive filename
    by normalizing unicode, converting to lowercase, replacing spaces with underscores,
    removing special characters, and appending the version number.
    
    Args:
        description: The character description (e.g., "Friendly Robot Sidekick")
        version: The version number to append (default: 1)
        extension: The file extension without dot (default: 'png')
    
    Returns:
        A sanitized filename (e.g., "friendly_robot_sidekick_v1.png")
    
    Examples:
        >>> derive_filename_from_description("Friendly Robot Sidekick", 2)
        'friendly_robot_sidekick_v2.png'
        >>> derive_filename_from_description("Angry Vegetable Villain!", 1, 'json')
        'angry_vegetable_villain_v1.json'
    """
    if not description:
        return f"character_v{version}.{extension}"
    
    # Normalize unicode characters (e.g., convert accented chars to ASCII equivalents)
    normalized = unicodedata.normalize('NFKD', description)
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
    
    # Convert to lowercase
    lower_text = ascii_text.lower()
    
    # Replace spaces and multiple whitespace with single underscore
    spaced = re.sub(r'\s+', '_', lower_text.strip())
    
    # Remove any characters that aren't alphanumeric or underscore
    sanitized = re.sub(r'[^a-z0-9_]', '', spaced)
    
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Ensure we have something
    if not sanitized:
        sanitized = "character"
    
    # Truncate if too long (max 100 chars for the base name)
    if len(sanitized) > 100:
        sanitized = sanitized[:100].rstrip('_')
    
    # Append version and extension
    return f"{sanitized}_v{version}.{extension}"


def derive_json_filename_from_description(description: str, version: int = 1) -> str:
    """
    Derive a JSON filename from a character description.
    
    Convenience wrapper for derive_filename_from_description with JSON extension.
    
    Args:
        description: The character description
        version: The version number to append (default: 1)
    
    Returns:
        A sanitized JSON filename
    """
    return derive_filename_from_description(description, version, 'json')
