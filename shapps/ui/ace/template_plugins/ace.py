def call(app, var, env):
    from uliweb import settings
    a = []
    version = settings.UI_CONFIG.ace_version

    a.append('ace/%s/ace.min.css' % version)
    a.append('ace/%s/ace-elements.min.js' % version)
    a.append('ace/%s/ace.min.js' % version)
    a.append('ace/%s/bootbox.min.js' % version)
    a.append('ace/%s/jquery.dataTables.bootstrap.js' % version)
    return {'bottomlinks': a}
