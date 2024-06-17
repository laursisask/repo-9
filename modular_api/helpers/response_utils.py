from bottle import HTTPResponse
from http import HTTPStatus


def get_trace_id(tracer):
    return tracer.current_trace_context().trace_id


def build_response(_trace_id, http_code: HTTPStatus | int = HTTPStatus.OK,
                   content=None, message=None):
    if isinstance(http_code, HTTPStatus):
        http_code = http_code.value
    if content is None:
        content = {}
    if message:
        content['message'] = message
    return HTTPResponse(
        status=http_code,
        body=content,
        headers={
            'Content-Type': 'application/json',
            'Trace-ID': _trace_id,
            'Code': http_code
        },
    )
