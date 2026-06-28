# import logging
#
# from flask import current_app
# from huey import crontab
#
# from ...huey_config import huey, app_context
# from .wechat import wechat, ACCESS_TOKEN_KEY, JSAPI_TICKET_KEY
#
# logger = logging.getLogger(__name__)
#
#
# @huey.periodic_task(crontab(minute='*/5'))
# @huey.lock_task('wechat-token-check-lock')
# @app_context
# def check_wx_tokens():
#     """
#     check access token and js api ticket every 5 minute, if the expires_in
#     is less then 6 minutes, refresh it
#     """
#     access_token_ttl = current_app.redis.ttl(ACCESS_TOKEN_KEY)
#     if not access_token_ttl or access_token_ttl < 360:
#         refresh_wx_token()
#     jsapi_ticket_ttl = current_app.redis.ttl(JSAPI_TICKET_KEY)
#     if not jsapi_ticket_ttl or jsapi_ticket_ttl < 360:
#         refresh_jsapi_ticket()
#
#
# @huey.task(retries=5, retry_delay=5)
# @huey.lock_task('wechat-token-lock')
# @app_context
# def refresh_wx_token():
#     app_id = wechat.app_id
#     app_secret = wechat.app_secret
#     resp = wechat.get('/cgi-bin/token', {
#         'grant_type': 'client_credential',
#         'appid': app_id,
#         'secret': app_secret
#     })
#     token = resp.get('access_token')
#     expires_in = resp.get('expires_in')
#     if token:
#         current_app.redis.set(ACCESS_TOKEN_KEY, token, ex=expires_in)
#
#
# @huey.task(retries=5, retry_delay=5)
# @huey.lock_task('wechat-jspai-ticket')
# @app_context
# def refresh_jsapi_ticket():
#     token = wechat.access_token
#     resp = wechat.get('/cgi-bin/ticket/getticket', {
#         'access_token': token,
#         'type': 'jsapi'
#     })
#     ticket = resp.get('ticket')
#     expires_in = resp.get('expires_in')
#     logger.warning(f'{ticket}, {expires_in}')
#     if ticket:
#         current_app.redis.set(JSAPI_TICKET_KEY, ticket, ex=expires_in)
