def call(app, var, env):
    a = []
    a.append('moment/moment.min.js')
    a.append('moment/moment-timezone-with-data.min.js')
    return {'toplinks': a}
