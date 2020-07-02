import base64
import io
import time
import traceback
from urllib.parse import urlparse

import requests
from chalice import BadRequestError, Chalice

from decouple import config

# Importable errors
# * BadRequestError - return a status code of 400
# * UnauthorizedError - return a status code of 401
# * ForbiddenError - return a status code of 403
# * NotFoundError - return a status code of 404
# * ConflictError - return a status code of 409
# * UnprocessableEntityError - return a status code of 422
# * TooManyRequestsError - return a status code of 429
# * ChaliceViewError - return a status code of 500


DEBUG = config("DEBUG", cast=bool, default=False)

app = Chalice(app_name="relay")

app.debug = DEBUG

"""
The app.current_request object also has the following properties.

    current_request.query_params - A dict of the query params for the request.
    current_request.headers - A dict of the request headers.
    current_request.uri_params - A dict of the captured URI params.
    current_request.method - The HTTP method (as a string).
    current_request.json_body - The parsed JSON body (json.loads(raw_body))
    current_request.raw_body - The raw HTTP body as bytes.
    current_request.context - A dict of additional context information
    current_request.stage_vars - Configuration for the API Gateway stage

You can also debug the current request with: app.current_request.to_dict()
"""


@app.route("/", methods=["GET", "POST", "HEAD"])
def index():
    request = app.current_request
    request_headers = {}
    if request.method == "POST":
        try:
            request_data = request.json_body
        except Exception as exc:
            raise BadRequestError(
                f"Unable to extract JSON body from POST request " f"({exc})"
            )
        request_headers.update(request_data.get("headers", {}))
    else:
        # If the request is GET and there are no parameters, query_params becomes None.
        request_data = request.query_params or {}

    request_url = request_data.get("url")
    if not request_url:
        raise BadRequestError("Missing 'url'")

    request_method = request_data.get("method", "get").lower()
    if request_method not in ("head", "get", "post", "put", "delete"):
        raise BadRequestError(f"Invalid method {request_method!r}")

    parsed = urlparse(request_url)
    if not parsed.netloc:
        raise BadRequestError(f"Invalid URL ({parsed})")
    if parsed.scheme not in ("https", "http"):
        raise BadRequestError("Invalid URL (must be 'http' or 'https')")

    request_timeout = int(request_data.get("timeout", 30))
    if request_timeout < 1:
        raise BadRequestError("'timeout' value must be greater than 0")
    if request_timeout >= 60:
        raise BadRequestError("'timeout' value must be less than 60")

    method = getattr(requests, request_method)

    body = None
    error = None
    try:
        t0 = time.perf_counter()
        response = method(request_url, headers=request_headers, timeout=request_timeout)
        attempts = 1
        t1 = time.perf_counter()

        if not request_data.get("nobody") and request_method != "head":
            if response.headers["content-type"].startswith("text/"):
                body = response.content.decode(response.encoding)
            elif response.headers["content-type"].startswith("application/json"):
                body = response.json()
            else:
                body = base64.b64encode(response.content).decode("utf-8")
    except Exception as exc:
        f = io.StringIO()
        traceback.print_exc(file=f)
        error = {
            "traceback": f.getvalue(),
            "value": str(exc),
            "type": exc.__class__.__name__,
        }

    return {
        "meta": {
            "took": t1 - t0,
            "attempts": attempts,
            "nobody": bool(request_data.get("nobody")),
            "elapsed": response.elapsed.total_seconds(),
        },
        "error": error,
        "request": {
            "url": request_url,
            "headers": request_headers,
            "timeout": request_timeout,
            "method": request_method,
        },
        "response": {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": body,
        },
    }
