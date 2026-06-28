# !!! NEVER IMPORT THIS !!!
# Only used for WSGI entrance
#
# * To create an `app`, use `app_factory`
# * To refer to an `app`, use `flask.current_app`

from .app_factory import get_full_app

app = application = get_full_app()
