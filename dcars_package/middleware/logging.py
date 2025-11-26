# dcars_package/middleware/logging.py
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("dcars")
logging.basicConfig(level=logging.INFO)

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        dur_ms = int((time.perf_counter() - start) * 1000)
        logger.info("method=%s path=%s status=%s duration_ms=%s",
                    request.method, request.url.path, response.status_code, dur_ms)
        return response