def call(version = None, extensions = []):
    '''
    {{use 'bootstraptable',  extensions = ["cookie"]}}
    '''
    a = []
    a.append('bootstraptable/bootstrap-table.js')
    a.append('bootstraptable/bootstrap-table.css')
    for ename in extensions:
        a.append('bootstraptable/extensions/%s/bootstrap-table-%s.js'%(ename, ename))
    return {'toplinks': a}
