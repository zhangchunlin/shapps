def call(app, var, env):
    from uliweb import settings
    a = []
    version = settings.UI_CONFIG.jeditable_version

    a.append('jeditable/%s/jquery.jeditable.min.js' % version)
    return {'bottomlinks': a}
