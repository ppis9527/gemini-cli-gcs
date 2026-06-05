import re

def sanitize_content(text):
    """
    Scans for high-entropy strings (secrets, API keys) and redacts them.
    """
    # Google API Key Pattern
    google_key_pattern = r'AIza[0-9A-Za-z-_]{35}'
    
    # Generic Secret/Token/Password Assignment
    assignment_pattern = r'(?i)(secret|token|password|auth|key|credential)["\']?\s*[:=]\s*["\']([^"\']{8,})["\']'
    
    sanitized = re.sub(google_key_pattern, "[REDACTED_GOOGLE_KEY]", text)
    
    def redact_assignment(match):
        key_name = match.group(1)
        val = match.group(2)
        if len(val) > 16 or any(c.isdigit() for c in val):
            return f'{key_name}: "[REDACTED_SECRET]"'
        return match.group(0)

    sanitized = re.sub(assignment_pattern, redact_assignment, sanitized)
    
    return sanitized
