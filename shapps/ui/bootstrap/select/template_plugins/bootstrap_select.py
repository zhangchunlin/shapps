def call(app, var, env, locales=None):
    a = ['bootstrap-select/bootstrap-select.css']
    a.append('bootstrap-select/bootstrap-select.js')
    if locales:
        if isinstance(locales, str):
            a.append('bootstrap-select/i18n/defaults-%s.js' % locales)
        elif isinstance(locales, list):
            for la in locales:
                a.append('bootstrap-select/i18n/defaults-%s.js' % la)
    return {'toplinks':a, 'depends':['bootstrap']}
