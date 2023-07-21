from typing import Tuple, Dict, Any
from modular_api.helpers.constants import MODULAR_API_ITEMS, \
    MODULAR_API_JSON_MESSAGE, MODULAR_API_JSON_WARNINGS, \
    MODULAR_API_JSON_CODE, MODULAR_API_CODE, MODULAR_API_MESSAGE, \
    MODULAR_API_WARNINGS, MODULAR_API_TABLE_TITLE


class ResponseProcessor:
    def __init__(self, response: dict, keep_extras: bool = False):
        self._resp = response
        self._keep_extras = keep_extras

    @staticmethod
    def get_first(dct: dict, keys: Tuple[str, ...]) -> Any:
        values = (dct.get(key) for key in keys)  # gen
        return next((v for v in values if v), None)

    @staticmethod
    def pop_first(dct: dict, keys: Tuple[str, ...]) -> Any:
        """
        This function can change the incoming dict !!! Make sure you
        have a copy
        """
        values = (dct.pop(key, None) for key in keys)
        return next((v for v in values if v), None)

    def process(self) -> Tuple[Dict, int]:
        resp = self._resp
        getter = self.get_first
        if self._keep_extras:
            resp = resp.copy()  # shallow copy will do
            getter = self.pop_first

        code = getter(resp, (MODULAR_API_JSON_CODE, MODULAR_API_CODE)) or 500
        message = getter(resp, (MODULAR_API_JSON_MESSAGE, MODULAR_API_MESSAGE))
        items = getter(resp, (MODULAR_API_ITEMS,))
        table_title = getter(resp, (MODULAR_API_TABLE_TITLE,))
        warnings = getter(
            resp, (MODULAR_API_JSON_WARNINGS, MODULAR_API_WARNINGS)
        ) or []
        content = {MODULAR_API_JSON_WARNINGS: warnings}
        if message:
            content.update({
                MODULAR_API_JSON_MESSAGE: message
            })
        elif items:
            content.update({
                MODULAR_API_ITEMS: items,
                MODULAR_API_TABLE_TITLE: table_title
            })
        else:
            pass  # _LOG.warning('Something is wrong')
        if self._keep_extras:
            content.update(resp)  # updating with everything left
        return content, code


def process_response(response: dict) -> Tuple[Dict, int]:
    return ResponseProcessor(response, keep_extras=True).process()
