from eventlet import monkey_patch
monkey_patch()
from creator.app_factory import get_full_app  # noqa

app = get_full_app()
app.extensions['socketio'].run(
    app, host='0.0.0.0',
    use_reloader=app.debug,
    debug=app.debug,
)
