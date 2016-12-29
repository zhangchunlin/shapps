def call(version=None, plugins=[]):
    '''
    {{use 'jqplot',  plugins = ["xxxx"]}}
    '''
    a = []
    a.append('jqplot/jquery.jqplot.min.css')
    a.append('jqplot/jquery.jqplot.min.js')
    for ename in plugins:
        a.append('jqplot/plugins/jqplot.%s.min.js' % (ename))
    return {'toplinks': a}
