from src.redis.ratelimiter import RateLimite

# ─── Auth — strict, per IP ────────────────────────────────
AUTH_LOGIN = RateLimite(limit=5, window_second=60)          # 5/min
AUTH_REGISTER = RateLimite(limit=3, window_second=3600)     # 3/hour
AUTH_REFRESH = RateLimite(limit=30, window_second=3600)     # 30/hour

# ─── Users — per user (IP fallback) ───────────────────────
USER_SEARCH = RateLimite(limit=60, window_second=60)
USER_GET = RateLimite(limit=120, window_second=60)

# ─── Conversations ────────────────────────────────────────
CONVERSATION_CREATE = RateLimite(limit=20, window_second=60)
CONVERSATION_LIST = RateLimite(limit=120, window_second=60)

# ─── Messages ─────────────────────────────────────────────
MESSAGE_SEND = RateLimite(limit=30, window_second=60)
MESSAGE_HISTORY = RateLimite(limit=120, window_second=60)
MESSAGE_READ = RateLimite(limit=120, window_second=60)

# ─── Global (coarse cap) ──────────────────────────────────
GLOBAL_HTTP = RateLimite(limit=300, window_second=60)
