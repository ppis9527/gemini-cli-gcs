import sys

def estimate_tokens(text):
    """
    Simple token estimation based on character count (approx 4 chars per token).
    """
    return len(text) // 4

def truncate_to_quota(skeletons, global_quota=3000):
    """
    Enforces token quotas on a list of skeleton strings.
    Each skeleton is (file_path, content).
    """
    total_tokens = 0
    final_skeletons = []
    
    # Priority is given to the first files in the list
    for path, content in skeletons:
        tokens = estimate_tokens(content)
        if total_tokens + tokens > global_quota:
            # Over quota, try to truncate this skeleton or skip
            remaining = global_quota - total_tokens
            if remaining > 100:
                truncated = content[:remaining*4] + "\n# ... [Truncated due to Quota]"
                final_skeletons.append((path, truncated))
                total_tokens = global_quota
            break
        else:
            final_skeletons.append((path, content))
            total_tokens += tokens
            
    return final_skeletons
