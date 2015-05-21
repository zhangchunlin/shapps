#! /usr/bin/env python
#coding=utf-8

"""
    LDAP / Active Directory authentication,copy and modify from MoinMoin

    python-ldap needs to be at least 2.0.0pre06 (available since mid 2002) for
    ldaps support - some older debian installations (woody and older?) require
    libldap2-tls and python2.x-ldap-tls, otherwise you get ldap.SERVER_DOWN:
    "Can't contact LDAP server" - more recent debian installations have tls
    support in libldap2 (see dependency on gnutls) and also in python-ldap.

    @copyright: 2006-2008 MoinMoin:ThomasWaldmann,
                2006 Nick Phillips
    @license: GNU GPL, see COPYING for details.
"""

import logging
log = logging.getLogger('shapps.auth.ldap')

try:
    import ldap
except ImportError, err:
    log.error("You need to have python-ldap installed (%s)." % str(err))
    raise


class LDAPAuth(object):
    """ get authentication data from form, authenticate against LDAP (or Active
        Directory), fetch some user infos from LDAP and create a user object
        for that user. The session is kept by moin automatically.
    """

    def __init__(self,
        server_uri='ldap://localhost',  # ldap / active directory server URI
                                        # use ldaps://server:636 url for ldaps,
                                        # use  ldap://server for ldap without tls (and set start_tls to 0),
                                        # use  ldap://server for ldap with tls (and set start_tls to 1 or 2).
        bind_dn='',  # We can either use some fixed user and password for binding to LDAP.
                     # Be careful if you need a % char in those strings - as they are used as
                     # a format string, you have to write %% to get a single % in the end.
                     #bind_dn = 'binduser@example.org' # (AD)
                     #bind_dn = 'cn=admin,dc=example,dc=org' # (OpenLDAP)
                     #bind_pw = 'secret'
                     # or we can use the username and password we got from the user:
                     #bind_dn = '%(username)s@example.org' # DN we use for first bind (AD)
                     #bind_pw = '%(password)s' # password we use for first bind
                     # or we can bind anonymously (if that is supported by your directory).
                     # In any case, bind_dn and bind_pw must be defined.
        bind_pw='',
        user_base_dn='', # base DN we use for searching user
        group_base_dn='', # base DN we use for searching group
        scope=ldap.SCOPE_SUBTREE, # scope of the search we do (2 == ldap.SCOPE_SUBTREE)
        referrals=0, # LDAP REFERRALS (0 needed for AD)
        user_match_filter='(uid=%(username)s)',
        group_match_filter='(o=%(groupname)s)',
        user_search_filter='(uid=%(username)s*)',
        group_search_filter='(o=%(groupname)s*)',
        # some attribute names we use to extract information from LDAP
        user_attributes = {
            'givenname':'givenName',
            'surname':'sn',
            'aliasname':'displayName',
            'email':'mail',
            'memberof':'memberOf',
        },
        group_attributes = {
            'email':'mail',
            'name':'sAMAccountName',
            'description':'description',
        },
        coding='utf-8', # coding used for ldap queries and result values
        timeout=10, # how long we wait for the ldap server [s]
        start_tls=0, # 0 = No, 1 = Try, 2 = Required
        tls_cacertdir=None,
        tls_cacertfile=None,
        tls_certfile=None,
        tls_keyfile=None,
        tls_require_cert=0, # 0 == ldap.OPT_X_TLS_NEVER (needed for self-signed certs)
        report_invalid_credentials=True, # whether to emit "invalid username or password" msg at login time or not
        ):
        self.server_uri = server_uri
        self.bind_dn = bind_dn
        self.bind_pw = bind_pw
        self.user_base_dn = user_base_dn
        self.group_base_dn = group_base_dn
        self.scope = scope
        self.referrals = referrals
        self.user_match_filter = user_match_filter
        self.group_match_filter = group_match_filter
        self.user_search_filter = user_search_filter
        self.group_search_filter = group_search_filter
        self.user_attributes = user_attributes
        self.group_attributes = group_attributes
        self.coding = coding
        self.timeout = timeout
        self.start_tls = start_tls
        self.tls_cacertdir = tls_cacertdir
        self.tls_cacertfile = tls_cacertfile
        self.tls_certfile = tls_certfile
        self.tls_keyfile = tls_keyfile
        self.tls_require_cert = tls_require_cert
        self.report_invalid_credentials = report_invalid_credentials

        def get_ldap_attributes(attrs):
            ldap_attributes = []
            for n in attrs:
                v = attrs[n]
                if isinstance(v,(str,unicode)):
                    ldap_attributes.append(v)
                elif isinstance(v,dict):
                    from_ldap = v.get("from_ldap")
                    if isinstance(from_ldap,str):
                        ldap_attributes.append(from_ldap)
                    elif isinstance(from_ldap,list):
                        for attr in from_ldap:
                            if attr.find('%')<0:
                                ldap_attributes.append(attr)
            return ldap_attributes
        self.user_ldap_attributes = get_ldap_attributes(user_attributes)
        log.debug("user_ldap_attributes:%s"%(self.user_ldap_attributes))
        self.group_ldap_attributes = get_ldap_attributes(group_attributes)
        log.debug("group_ldap_attributes:%s"%(self.group_ldap_attributes))

    def _get_ldap_connection(self):
        u = None
        dn = None
        log.debug("Setting misc. ldap options...")
        ldap.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3) # ldap v2 is outdated
        ldap.set_option(ldap.OPT_REFERRALS, self.referrals)
        ldap.set_option(ldap.OPT_NETWORK_TIMEOUT, self.timeout)

        if hasattr(ldap, 'TLS_AVAIL') and ldap.TLS_AVAIL:
            for option, value in (
                (ldap.OPT_X_TLS_CACERTDIR, self.tls_cacertdir),
                (ldap.OPT_X_TLS_CACERTFILE, self.tls_cacertfile),
                (ldap.OPT_X_TLS_CERTFILE, self.tls_certfile),
                (ldap.OPT_X_TLS_KEYFILE, self.tls_keyfile),
                (ldap.OPT_X_TLS_REQUIRE_CERT, self.tls_require_cert),
                (ldap.OPT_X_TLS, self.start_tls),
                #(ldap.OPT_X_TLS_ALLOW, 1),
            ):
                if value is not None:
                    ldap.set_option(option, value)

        log.debug("Trying to initialize %r." % self.server_uri)
        l = ldap.initialize(self.server_uri)
        log.debug("Connected to LDAP server %r." % self.server_uri)

        if self.start_tls and self.server_uri.startswith('ldap:'):
            log.debug("Trying to start TLS to %r." % self.server_uri)
            try:
                l.start_tls_s()
                log.debug("Using TLS to %r." % self.server_uri)
            except (ldap.SERVER_DOWN, ldap.CONNECT_ERROR), err:
                log.warning("Couldn't establish TLS to %r (err: %s)." % (self.server_uri, str(err)))
                raise

        l.simple_bind_s(self.bind_dn.encode(self.coding), self.bind_pw.encode(self.coding))
        log.debug("Bound with binddn %r" % self.bind_dn)

        return l

    def _search_user(self,l,username,search_filter=None):
        # you can use %(username)s here to get the stuff entered in the form
        search_filter = search_filter or self.user_match_filter
        filterstr = search_filter % locals()
        log.debug("Searching %r" % filterstr)

        lresults = l.search_st(self.user_base_dn, self.scope, filterstr.encode(self.coding),
                             attrlist=self.user_ldap_attributes, timeout=self.timeout)

        # we remove entries with dn == None to get the real result list:
        litems = [(dn, ldap_dict) for dn, ldap_dict in lresults if dn is not None]
        for dn, ldap_dict in litems:
            log.debug("dn:%r" % dn)
            for key, val in ldap_dict.items():
                log.debug("    %r: %r" % (key, val))

        return litems

    def _extract_ldap_dict(self,ldap_dict,attributes):
        attr_dict = {}

        def get_value_from_ldap_dict(k):
            if k.find('%')>=0:
                return k%(ldap_dict)
            else:
                return ldap_dict.get(k)

        for attr,attr_setting in attributes.items():
            if isinstance(attr_setting,(str,unicode,list)):
                from_ldap = attr_setting
            elif isinstance(attr_setting,dict):
                from_ldap = attr_setting.get('from_ldap')
            else:
                from_ldap = None

            if from_ldap:
                if isinstance(from_ldap,(str,unicode)):
                    value = get_value_from_ldap_dict(from_ldap)
                elif isinstance(from_ldap,list):
                    for lattr in from_ldap:
                        value = get_value_from_ldap_dict(lattr)
                        if value:
                            break
                else:
                    log.error("bad ldap attrs setting:%s"%(attr_setting))
                    value = None
            else:
                log.error("bad ldap attrs setting:%s"%(attr_setting))
                value = None
            if value:
                if isinstance(value,str):
                    try:
                        value = value.decode(self.coding)
                    except UnicodeDecodeError as e:
                        pass
                attr_dict[attr] = value
            else:
                log.error("can not obtain '%s' with '%s' from '%s'"%(attr,attr_setting,ldap_dict))
        return attr_dict

    def _get_user_attributes(self,ldap_dict):
        #extract ldap_dict
        #memberof will get whole list, others get one value from list
        memberof_key = self.user_attributes.get("memberof")
        for k,v in ldap_dict.items():
            if k!=memberof_key and isinstance(v,list):
                if v:
                    if len(v)>1:
                        ldap_dict[k]=v
                    else:
                        ldap_dict[k]=v[0]
                else:
                    ldap_dict[k]=None

        return self._extract_ldap_dict(ldap_dict,self.user_attributes)

    def _search_group(self,l,groupname,search_filter=None):
        # you can use %(username)s here to get the stuff entered in the form
        search_filter = search_filter or self.group_match_filter
        filterstr = search_filter % locals()
        log.debug("Searching %r" % filterstr)

        lresults = l.search_st(self.group_base_dn, self.scope, filterstr.encode(self.coding),
                            attrlist=self.group_ldap_attributes, timeout=self.timeout)

        # we remove entries with dn == None to get the real result list:
        lgroups = [(dn, ldap_dict) for dn, ldap_dict in lresults if dn is not None]
        for dn, ldap_dict in lgroups:
            log.debug("dn:%r" % dn)
            for key, val in ldap_dict.items():
                log.debug("    %r: %r" % (key, val))

        return lgroups

    def _get_group_attributes(self,ldap_dict):
        for k,v in ldap_dict.items():
            if isinstance(v,list):
                if v:
                    if len(v)>1:
                        ldap_dict[k]=v
                    else:
                        ldap_dict[k]=v[0]
                else:
                    ldap_dict[k]=None

        return self._extract_ldap_dict(ldap_dict,self.group_attributes)

    def login(self, username=None, password=None):
        # we require non-empty password as ldap bind does a anon (not password
        # protected) bind if the password is empty and SUCCEEDS!
        if (not username) or (not password):
            return False,None

        try:
            l = self._get_ldap_connection()

            litems = self._search_user(l,username)
            if len(litems) != 1:
                log.error("error, len(litems):%d"%(len(litems)))
                return False, None

            dn, ldap_dict = litems[0]
            log.debug("DN found is %r, trying to bind with pw" % dn)
            l.simple_bind_s(dn, password.encode(self.coding))
            log.debug("Bound with dn %r (username: %r)" % (dn, username))

            attr_dict = self._get_user_attributes(ldap_dict)
            log.debug("attr_dict: %s" % (attr_dict))
            return True, attr_dict

        except ldap.INVALID_CREDENTIALS as err:
            log.error("invalid credentials (wrong password?) for dn %r (username: %r)" % (dn, username))
            return False, None

        except ldap.SERVER_DOWN as err:
            # looks like this LDAP server isn't working, so we just try the next
            # authenticator object in cfg.auth list (there could be some second
            # ldap authenticator that queries a backup server or any other auth
            # method).
            log.error("LDAP server %s failed (%s). "
                          "Trying to authenticate with next auth list entry." % (self.server_uri, str(err)))
            return False, None

        except Exception as err:
            log.error("login() caught an exception(%s):%s",Exception,err)
            return False, None

    def get_user(self, username=None):
        if not username:
            return None

        attr_dict = None
        try:
            l = self._get_ldap_connection()

            litems = self._search_user(l,username)

            #only one user is valid
            if len(litems)==1:
                dn, ldap_dict = litems[0]
                if ldap_dict:
                    attr_dict = self._get_user_attributes(ldap_dict)

        except ldap.SERVER_DOWN, err:
            log.error("LDAP server %s failed (%s). "
                "Trying to authenticate with next auth list entry." % (self.server_uri, str(err)))

        except ldap.INVALID_CREDENTIALS as err:
            log.error("invalid credentials, bad bind user or password?")
            return None

        except Exception,err:
            log.error("get_user() caught an exception(%s):%s",Exception,err)

        return attr_dict

    def search_user(self, username=None):
        user_list = []

        if username:
            try:
                l = self._get_ldap_connection()
                litems = self._search_user(l,username,search_filter=self.user_search_filter)
                user_list = [(dn, self._get_user_attributes(ldap_dict)) for dn, ldap_dict in litems]

            except ldap.INVALID_CREDENTIALS as err:
                log.error("invalid credentials, bad bind user or password?")
                return None

            except Exception,err:
                log.error("search_user() caught an exception(%s):%s",Exception,err)

        return user_list

    def get_group(self, groupname=None):
        attr_dict = None
        if not groupname:
            return None

        try:
            l = self._get_ldap_connection()

            litems = self._search_group(l,groupname)

            #only one user is valid
            if len(litems)==1:
                dn, ldap_dict = litems[0]
                if ldap_dict:
                    attr_dict = self._get_group_attributes(ldap_dict)

        except ldap.SERVER_DOWN, err:
            log.error("LDAP server %s failed (%s). "
                "Trying to authenticate with next auth list entry." % (self.server_uri, str(err)))

        except ldap.INVALID_CREDENTIALS as err:
            log.error("invalid credentials, bad bind user or password?")

        except Exception as err:
            log.error("get_group() caught an exception:%s,groupname:%s",err,repr(groupname))

        return attr_dict

    def search_group(self, groupname=None):
        group_list = []

        if not groupname:
            return group_list

        try:
            l = self._get_ldap_connection()
            litems = self._search_group(l,groupname,search_filter=self.group_search_filter)
            group_list = [(dn, self._get_group_attributes(ldap_dict)) for dn, ldap_dict in litems]

        except ldap.INVALID_CREDENTIALS as err:
            log.error("invalid credentials, bad bind user or password?")
            return None

        except Exception,err:
            log.error("search_group() caught an exception(%s):%s",Exception,err)

        return group_list


#gen a ldapauth_handler for uliweb app
from uliweb import settings
if settings.LDAP and settings.LDAP.server_param:
    ldapauth_handler = LDAPAuth(**settings.LDAP.server_param)
else:
    ldapauth_handler = None
