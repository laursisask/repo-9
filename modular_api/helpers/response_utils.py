from bottle import HTTPResponse


def get_trace_id(tracer):
    return tracer.current_trace_context().trace_id


def build_response(_trace_id, http_code=200, content=None, message=None):
    if content is None:
        content = {}
    if message:
        content['message'] = message
    return HTTPResponse(status=http_code,
                        body=content,
                        headers={'Content-Type': 'application/json',
                                 'Trace-ID': _trace_id,
                                 'Code': http_code},
                        )
