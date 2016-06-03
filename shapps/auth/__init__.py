#coding=utf-8
from uliweb import settings
from weto.session import Session
from uliweb.utils.common import import_attr, application_path

def get_session(key=None):
    options = dict(settings.get('SESSION_STORAGE', {}))
    options['data_dir'] = application_path(options['data_dir'])
    if 'url' not in options:
        _url = (settings.get_var('ORM/CONNECTION', '') or
        settings.get_var('ORM/CONNECTIONS', {}).get('default', {}).get('CONNECTION', ''))
        if _url:
            options['url'] = _url

    #process Session options
    session_storage_type = settings.SESSION.type
    Session.force = settings.SESSION.force

    serial_cls_path = settings.SESSION.serial_cls
    if serial_cls_path:
        serial_cls = import_attr(serial_cls_path)
    else:
        serial_cls = None

    session = Session(key, storage_type=session_storage_type,
        options=options, expiry_time=settings.SESSION.timeout, serial_cls=serial_cls)
    return session
