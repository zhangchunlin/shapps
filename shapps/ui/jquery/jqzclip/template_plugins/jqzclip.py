def call(app, var, env):
    a = []
    a.append('jqzclip/jquery.zclip.min.js')
    a.append("<script src='/static/jqzclip/ZeroClipboard.swf'></script>")
    return {'toplinks': a}
