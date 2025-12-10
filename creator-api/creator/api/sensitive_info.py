from collections import Iterable

from .utils import mask_value


class SensitiveInfoManager:
    def __init__(self, app):
        self.app = app
        app.extensions['sensitive_info_manager'] = self
        self.keywords = set(app.config.get('SENSITIVE_KEYWORDS', []))
        self.masks = {}
        self._can_view_sensitive_info_cb = lambda: False

    def register_mask(self, keyword, func):
        """
        register mask function for a keyword. The function should take 2
        args: (keyword, value) and return the masked value
        """
        self.keywords.add(keyword)
        self.masks[keyword] = func

    def can_view_sensitive_info_cb(self, func):
        """
        register a function which checks if I should mask. This function is
        probably related to request/current_user.
        """
        self._can_view_sensitive_info_cb = func

    def can_view_sensitive_info(self):
        return self._can_view_sensitive_info_cb()

    def maybe_mask(self, data: dict, *sensitive_fields) -> dict:
        """
        given the data to be returned to the client, check if the current user
        can view sensitive information.

        If he can, data is returned as is.

        If not, find possible sensitive fields
        in the data and mask them.

        :params data: data to be masked
        :params sensitive_fields:
            a list of fields which should be considered sensitive.
        """
        if self._can_view_sensitive_info_cb():
            return data
        return self._walk(data, self.keywords | set(sensitive_fields))

    def _walk(self, data, keywords, parent_key=''):
        updates = {}
        for k, v in data.items():
            if k in keywords and v is not None:
                try:
                    updates[k] = self._do_mask(k, v)
                except ValueError as e:
                    raise ValueError(
                        f'failed to mask {parent_key}.{k}: {e}')
            else:
                if isinstance(v, dict):
                    self._walk(v, keywords, f'{parent_key}.{k}')
                elif isinstance(v, Iterable) and not isinstance(v, str):
                    for i, item in enumerate(v):
                        self._walk(item, keywords, f'{parent_key}.{k}[{i}]')
        data.update(**updates)
        return data

    def _do_mask(self, key, value):
        f = self.masks.get(key) or self._default_mask
        return f(key, value)

    def _default_mask(self, key, value):
        return mask_value(value)
