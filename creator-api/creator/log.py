import sys
import logging
from logging.handlers import SMTPHandler


class Formatter(logging.Formatter):

    def formatException(self, ei):
        s = super().formatException(ei)
        tb = ei[-1]
        if tb:
            while tb.tb_next:
                tb = tb.tb_next
            local_vars = tb.tb_frame.f_locals
            s = '{}\nLocal variables:\n{}'.format(
                s, '\n'.join(f'  {k}: {v}' for k, v in local_vars.items())
            )
        return s


def configure_logging(config):
    if config.DEBUG:
        logging.basicConfig(level=logging.DEBUG)
    else:
        # root logger: INFO to stdout; ERROR to mail
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        # log to stdout
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(Formatter(
            '%(name)s %(levelname)s in %(pathname)s:%(lineno)s: %(message)s'
        ))
        stream_handler.setLevel(logging.INFO)
        root_logger.addHandler(stream_handler)
        # mail
        if config.LOGGING_MAIL_SERVER:
            if 'gunicorn' in sys.argv[0]:
                proc = 'api'
            elif 'huey' in sys.argv[0]:
                proc = 'worker'
            elif 'run_sio' in sys.argv[0]:
                proc = 'socketio'
            else:
                proc = 'other'
            mail_handler = SMTPHandler(
                mailhost=config.LOGGING_MAIL_SERVER,
                fromaddr=config.LOGGING_MAIL_FROM,
                toaddrs=config.LOGGING_MAIL_TO_LIST,
                subject=f'[{config.ENV.upper()}][{proc}]creator Error',
            )
            mail_handler.setLevel(logging.ERROR)
            mail_handler.setFormatter(Formatter(
                '%(asctime)s [%(name)s]%(levelname)s in %(pathname)s:%(lineno)s %(message)s'
                # noqa
            ))
            root_logger.addHandler(mail_handler)
