import hashlib
import uuid
import time
import xml.etree.ElementTree as ET
from fastapi import Request, Depends

from .. import router as app
from ..utils import config, get_settings
from .wechat import wechat
from ..settings.models import Settings


def check_signature(signature, timestamp, nonce,
                    settings: Settings = Depends(get_settings)):
    token = settings.wechat_event_token
    key = ''.join(sorted([timestamp, nonce, token]))
    sha1 = hashlib.sha1(key.encode('utf-8')).hexdigest()
    return signature == sha1


@app.get('/wx_configs')
def wx_configs(request: Request):
    jsapi_ticket = wechat.jsapi_ticket
    if not jsapi_ticket:
        return dict(success=False, error=dict(message='jsapi ticket 不存在'))
    jsapi_ticket = jsapi_ticket.decode('utf-8')
    app_id = config.get('WECHAT_APP_ID')
    url = request.args.get('url', '').split('#', 1)[0]
    ts = int(time.time())
    nonce = uuid.uuid4().hex
    payload = f'jsapi_ticket={jsapi_ticket}&noncestr={nonce}&timestamp={ts}&' \
              f'url={url}'.encode('utf-8')
    sig = hashlib.sha1(payload).hexdigest()
    resp = dict(
        success=True,
        appid=app_id,
        noncestr=nonce,
        timestamp=ts,
        signature=sig,
    )
    return dict(**resp)


@app.get('/wechat/events')
def wechat_server_validate(request: Request):
    if (check_signature(request.args.get('signature'),
                        request.args.get('timestamp'),
                        request.args.get('nonce'))):
        echostr = request.args.get('echostr', '')
        return echostr
    else:
        return ''


@app.post('/wechat/events')
def wechat_events(request: Request):
    root = ET.fromstring(request.data)
    wechat_xml = {}
    for child in root:
        wechat_xml[child.tag] = child.text

    from_username = wechat_xml.get('FromUserName')
    scene = None
    event = wechat_xml.get('Event').lower().strip()
    event_key = wechat_xml.get('EventKey')
    if event == 'subscribe' and event_key.startswith('qrscene_'):
        scene = event_key.replace('qrscene_', '')
    elif event == 'scan':
        scene = event_key

    # TODO: handle scene
    print(scene)

    if scene:
        # TODO: fix url
        url = config.get('EXTERNAL_URL')
        msg = f'感谢您的关注，点击<a href="{url}">查看</a>您的权益！'
        wechat.send_text_message(from_username, msg)

    return ''
