from flask_babelex import get_locale


def test_locale_selector(app):
    lang_header = {
        'accept-language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4'
    }
    with app.test_request_context('/v1/ping/', headers=lang_header):
        assert get_locale().language == 'zh'
