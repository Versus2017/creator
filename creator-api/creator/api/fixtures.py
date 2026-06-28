from . import router as app

_fixtures = {}


def register_enum(enum, func=None):
    _fixtures[enum.__name__] = [
        e.dump() for e in enum if (True if func is None else func(e))
    ]


@app.get('/admin/fixtures')
def get_fixtures():
    return dict(
        success=True,
        fixtures=_fixtures,
    )
