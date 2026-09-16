from django.core.cache import cache

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutes


def _key(identifier):
    return f"login_attempts:{identifier}"


def is_locked_out(identifier):
    return cache.get(_key(identifier), 0) >= MAX_ATTEMPTS


def register_failed_attempt(identifier):
    key = _key(identifier)
    attempts = cache.get(key, 0) + 1
    cache.set(key, attempts, LOCKOUT_SECONDS)
    return attempts


def clear_attempts(identifier):
    cache.delete(_key(identifier))


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")
