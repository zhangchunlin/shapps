
import requests
from urlparse import urljoin
from uliweb import settings
from uliweb.i18n import ugettext_lazy as _
import logging
import json as jn
from uliweb.orm import get_model

mylog = logging.getLogger('lenovoid')

def authenticate(lpsust):
    """
    lenovo id authenticate using lpsust.
    Will sync accountid, email or phone number to user.
    Field mapping:
        AccountID -> username
        Username or AliasName -> email
        verified or AliasVerified ->email_verified
        Username or AliasName -> Phone number
        verified or AliasVerified ->phone_verified
    error_code:
        200: success
        400: User login failed
        Other code see:settings.AUTH_LENOVOID.FIELD_REQUIRE_ERROR_MSG
    """
    from uliweb import request
    auth_url = urljoin(settings.AUTH_LENOVOID.BASE_URL, settings.AUTH_LENOVOID.ACCOUNTINFO_URL)
    data = {
        "lpsust": lpsust,
        "realm": settings.AUTH_LENOVOID.REALM
    }
    mylog.info("Lenovo ID auth url:%s, data: %s"%(auth_url, data))
    r = requests.post(auth_url, data = data)
    mylog.info(r.text)

    if r.ok:
        data = r.json()
        identity_info = data.get("IdentityInfo")
        if not identity_info:
            mylog.error("lpsust:%s auth failed. Error message: %s"%(lpsust, r.text))
            return False, {'error_message': _('Account login failed.'), "error_code": 400}
        l_account_id = identity_info.get("AccountID")
        l_user_name = identity_info.get("Username", "")
        l_verified = identity_info.get("verified")
        l_alias = identity_info.get("Alias", [{}])[0]
        l_alias_name = l_alias.get("AliasName", "")
        l_alias_verified = l_alias.get("AliasVerified")
        deviceid = identity_info.get("DeviceID")
        nickname = identity_info.get("CurtName")
        if l_user_name.isalnum():
            phone_num = l_user_name
            phone_verified = l_verified == 1
            email = l_alias_name
            email_verified = l_alias_verified == 1
        else:
            email = l_user_name
            email_verified = l_verified == 1
            phone_num = l_alias_name
            phone_verified = l_alias_verified == 1
        attr_dict = {
            "email": email,
            "phone_num": phone_num,
            "email_verified": email_verified,
            "phone_verified": phone_verified,
            "nickname": nickname,
            "auth_type": settings.AUTH.AUTH_TYPE_LENOVOID,
            "deviceid": deviceid,
            "nickname": nickname,
        }
        mylog.info("User account: %s"%(attr_dict))
        for f in settings.AUTH_LENOVOID.FIELD_REQUIRE_TRUE:
            if not attr_dict.get(f):
                error_msg = settings.AUTH_LENOVOID.FIELD_REQUIRE_ERROR_MSG.get(f).get("message")
                error_code = settings.AUTH_LENOVOID.FIELD_REQUIRE_ERROR_MSG.get(f).get("code")
                mylog.error("%s, user info: %s, remote ip: %s"%(error_msg, identity_info, request.environ['REMOTE_ADDR']))
                return False, {'error_message': _(error_msg), "error_code": error_code}

        #Save user

        user = _sync_lenovoid_user(str(l_account_id), attr_dict)
        return True, user
    else:
        mylog.error("lpsust:%s auth failed. Error message: %s, remote ip: %s"%(lpsust, r.text, request.environ['REMOTE_ADDR']))
        return False, {'error_message': _('Account login failed.'), "error_code": 400}

def _sync_lenovoid_user(username, attr_dict):
    User = get_model('user')
    user = User.get(User.c.username==username)
    changed = False
    if not user:
        user = User(username=username)
        changed = True
        mylog.info("Creating user: %s, attr_dict: %s"%(username, attr_dict))

    #update user attributes, k is culomn name , v is value
    for k,v in attr_dict.items():
        if hasattr(user, k) and getattr(user, k) != v:
            setattr(user, k, v)
            changed = True
    if changed:
        user.save()
    return user
