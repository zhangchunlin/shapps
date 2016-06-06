
def fn_none_blank(obj):
    return obj or '&nbsp;'


# from uliweb.core.dispatch import bind
# @bind('prepare_default_env')
# def prepare_default_env(sender, env):
#     env['fnNoneToHtmlBlank'] = fn_none_blank
