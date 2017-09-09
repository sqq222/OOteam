from django import template
register = template.Library()



@register.filter(name='active_per')
def active_per(value, arg):
    return value / arg * 100


@register.filter(name='getDailyAddedPer')
def getDailyAddedPer(value, arg):
    if int(arg) > 0:
        if value[arg][1] == 0 and value[arg - 1][1] != 0:
            return '-100'
        if value[arg - 1][1] == 0 and value[arg][1] != 0:
            return '100'
        if value[arg - 1][1] == 0 and value[arg][1] == 0:
            return '0'
        # print((value[arg][1] - value[arg - 1][1]) / value[arg - 1][1])
        return (value[arg][1] - value[arg - 1][1]) / value[arg - 1][1]
        # return '1'
    else:
        return '0'
