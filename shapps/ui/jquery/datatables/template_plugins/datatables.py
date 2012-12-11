def call(app, var, env):
    a = []
    a.append('datatables/media/css/jquery.dataTables.css')
    a.append('datatables/media/css/jquery.dataTables_themeroller.css')
    a.append('datatables/media/js/jquery.dataTables.min.js')
    return {'toplinks': a}
