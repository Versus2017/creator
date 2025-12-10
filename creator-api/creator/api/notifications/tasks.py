from ...huey_config import huey, app_context, logger
import json
from aliyunsdkcore.request import RpcRequest
from aliyunsdkcore.profile import region_provider
from ..utils import get_acs_client
from ...config import config


REGION = "cn-hangzhou"
PRODUCT_NAME = "Dysmsapi"
DOMAIN = "dysmsapi.aliyuncs.com"


region_provider.add_endpoint(PRODUCT_NAME, REGION, DOMAIN)

acs_client = get_acs_client()


class AliyunError(Exception):
    pass


@huey.task(retries=3, retry_delay=20)
@app_context
def send_sms_by_tpl(tpl_name, *mobiles, **tpl_kwargs):
    """
    Send sms use aliyun sms sdk
    :param tpl_name: aliyun sms template name, like SMS_143660082
    :param mobiles: phone numbers, '135xxxxx,136xxxxx', must less than 1000
    :param tpl_kwargs: sms template args
    :return:
    """

    logger.warning('start to send message to {}'.format(mobiles))
    if not config.get('MESSAGE_SEND_ENABLED'):
        logger.info('MESSAGE SEND ENABLED : FALSE')
        return

    req = RpcRequest(PRODUCT_NAME, '2017-05-25', 'SendSms')
    req.add_query_param('TemplateCode', tpl_name)
    req.add_query_param('PhoneNumbers', mobiles)
    req.add_query_param('SignName', config.ALY_SMS_SIGN_NAME)
    req.add_query_param('TemplateParam', json.dumps(tpl_kwargs))

    resp = acs_client.do_action_with_exception(req)
    resp = json.loads(resp)
    if resp.get('Code') != 'OK':
        raise AliyunError(resp)
    logger.warning(resp)


@huey.task(retries=3, retry_delay=20)
@app_context
def send_sms(type_, tpl, *mobiles):
    logger.warning('Not implemented')

