def call(app, var, env):
    from uliweb import settings
    a = []
    version = settings.UI_CONFIG.jqueryui_version

    a.append('jqueryui/%s/jquery-ui-%s.custom.min.css' % (version, version))
    a.append('jqueryui/%s/jquery-ui-%s.full.min.js' % (version, version))
    return {'bottomlinks': a}
