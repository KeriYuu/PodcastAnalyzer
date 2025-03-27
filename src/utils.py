def format_duration(seconds: float) -> str:
    """
    Convert seconds to readable hours:minutes:seconds format
    
    Args:
        seconds: Number of seconds
        
    Returns:
        str: Formatted time string
    """
    seconds = round(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return "".join(parts) 