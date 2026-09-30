"""Pure ASGI middleware (no ``BaseHTTPMiddleware``, so streaming and context vars behave)."""

import contextlib
import logging
import re
import time
import uuid
from http import HTTPStatus

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.error_handlers import REQUEST_ID_HEADER, error_response, internal_error_response
from app.core.logging import request_id_var

logger = logging.getLogger(__name__)
access_logger = logging.getLogger("app.access")

# Accept a caller-supplied ID only if it is short and harmless to echo into logs/headers.
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class RequestContextMiddleware:
    """Per-request context: request ID, structured access log and last-resort error handling.

    Unexpected exceptions are caught here, rather than by Starlette's outermost error
    middleware, so the 500 response still carries the request ID and CORS headers.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = Headers(scope=scope).get(REQUEST_ID_HEADER, "")
        request_id = incoming if _VALID_REQUEST_ID.match(incoming) else uuid.uuid4().hex
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception:
            logger.exception("Unhandled error while processing request")
            if response_started:
                raise
            await internal_error_response()(scope, receive, send_with_request_id)
        finally:
            access_logger.info(
                "%s %s %s",
                scope["method"],
                scope["path"],
                status_code,
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status": status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
            request_id_var.reset(token)


class _BodyTooLargeError(Exception):
    pass


class BodySizeLimitMiddleware:
    """Rejects oversized request bodies before they are buffered or parsed.

    The declared ``Content-Length`` is checked up front, and the streamed byte count is
    enforced as well because clients may omit or misreport the header. This protects
    the multipart parser from resource exhaustion; the exact per-file limit is enforced
    by the upload reader.
    """

    def __init__(self, app: ASGIApp, max_body_bytes: int, max_file_bytes: int) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes
        self.max_file_mb = max_file_bytes // (1024 * 1024)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = Headers(scope=scope).get("content-length")
        if declared is not None and declared.isdigit() and int(declared) > self.max_body_bytes:
            await self._reject(scope, receive, send)
            return

        received = 0
        exceeded = False

        async def limited_receive() -> Message:
            nonlocal received, exceeded
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_body_bytes:
                    exceeded = True
                    raise _BodyTooLargeError
            return message

        async def guarded_send(message: Message) -> None:
            # Once the limit is hit, the framework may still try to answer (e.g. with a
            # generic body-parsing error); suppress that in favour of our 413.
            if not exceeded:
                await send(message)

        with contextlib.suppress(_BodyTooLargeError):
            await self.app(scope, limited_receive, guarded_send)
        if exceeded:
            await self._reject(scope, receive, send)

    async def _reject(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = error_response(
            HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            "file_too_large",
            f"The uploaded file exceeds the {self.max_file_mb} MB limit.",
        )
        await response(scope, receive, send)
