from django.forms import ModelForm
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from shop.user.models import *
from io import BytesIO
from django.utils import timezone
import xlsxwriter
from django.utils.translation import ugettext
import datetime
import random
from django.db.models import F
import re
import logging
from django import template
from django.db.models import Count
from django.db import connection
from shop.admin import utils


register = template.Library()

logger = logging.getLogger('docs.view')


def signin(request):
    return render(request, 'admin/login.html')


def index(request):
    if request.user.is_authenticated() is False:
        return HttpResponseRedirect('/admin/login/')
    context = {'module_name': 'dashboard'}
    return render(request, 'admin/index.html', context)


def login_view(request):
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    user = authenticate(username=username, password=password)
    x_forwarded_for = request.META.get('REMOTE_ADDR')
    if user is None:
        return HttpResponseRedirect('/admin/login/?error=pwderror')
    if user.is_active is False:
        return HttpResponseRedirect('/admin/login/?error=noactive')
    if user.status == 1:
        return HttpResponseRedirect('/admin/login/?error=lock')
    if user.is_superuser is False or user.is_staff is False:
        return HttpResponseRedirect('/admin/login/?error=noadmin')
    login(request, user)
    user = AbstractUser.objects.get(id=user.id)
    user.ip_address = x_forwarded_for
    user.save()
    return HttpResponseRedirect('/admin/index/')


def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/admin/')


def lock_view(request):
    if request.user.is_authenticated() is False:
        return HttpResponseRedirect('/admin/login/')
    return render(request, 'admin/user_lock.html')


def unlock_view(request):
    password = request.POST.get('password', '')
    user = authenticate(username=request.user.telephone, password=password)
    if user is None:
        return HttpResponseRedirect('/admin/lock/?error=pwderror')
    else:
        return HttpResponseRedirect('/admin/index/')


def get_user_list(usertype):
    if usertype == 'admin':
        return AbstractUser.objects.filter(
            is_superuser=True, is_staff=True)
    elif usertype == 'player':
        return IdentityCard.objects.filter(drive__isnull=False).annotate(dcount=Count('code'))
        # return AbstractUser.objects.filter(
        #                   is_superuser=False, is_staff=False)


def search_user_manage(usertype, type, q):
    if type == '':
        user_list = get_user_list(usertype)
    if type == 'usertype':
        if q == '':
            return get_user_list(usertype)
        user_list = get_user_list(usertype).filter(user_type_id=q)
    elif type == 'telephone':
        if q == '':
            return get_user_list(usertype)
        if usertype == 'admin':
            user_list = get_user_list(usertype).filter(telephone__contains=q)
        elif usertype == 'player':
            user_list = get_user_list(usertype).filter(user__telephone=q)
    elif type == 'name':
        if q == '':
            return get_user_list(usertype)
        if usertype == 'admin':
            user_list = get_user_list(usertype).filter(fullname__contains=q)
        elif usertype == 'player':
            user_list = get_user_list(usertype).filter(
                user__fullname__contains=q)
    elif type == 'cardno':
        if q == '':
            return get_user_list(usertype)
        if usertype == 'player':
            return get_user_list(usertype).filter(code__contains=q)
    elif type == 'sex':
        if q == '':
            return get_user_list(usertype)
        if usertype == 'player':
            return get_user_list(usertype).filter(user__sex=q)
    return user_list


def usermanage_view(request):
    user_type = request.GET.get('type', 'player')
    search_type = request.GET.get('search_type', '')
    q = request.GET.get('q', '')
    if user_type == 'player':
        user_list = search_user_manage(user_type, search_type, q)
        module_name = 'user_manage'
    if user_type == 'admin':
        user_list = search_user_manage(user_type, search_type, q)
        module_name = 'adminuser_manage'
    context = {'user_list': user_list,
               'user_type': user_type, 'module_name': module_name}
    return render(request, 'admin/user_manage.html', context)


def user_lock(request):
    telephone = request.GET.get('telephone', '')
    user_type = request.GET.get('type', '')
    if telephone != "":
        if telephone == request.user.telephone:
            return HttpResponseRedirect('/admin/user/?msg=yourself')
        user = AbstractUser.objects.get(telephone=telephone)
        user.status = 1
        user.save()
        return HttpResponseRedirect(
            '/admin/user/?msg=lock_success&type={0}'.format(user_type))


def user_unlock(request):
    telephone = request.GET.get('telephone', '')
    user_type = request.GET.get('type', '')
    if telephone != "":
        user = AbstractUser.objects.get(telephone=telephone)
        user.status = 0
        user.save()
        return HttpResponseRedirect(
            '/admin/user/?msg=unlock_success&type={0}'.format(user_type))


def user_add_view(request):
    return render(request, 'admin/user_add.html',
                  {'module_name': 'user_manage'})


def user_edit_view(request):
    telephone = request.GET.get('telephone', '')
    if telephone != "":
        user = AbstractUser.objects.get(telephone=telephone)
        context = {'user': user, 'module_name': 'user_manage'}
        return render(request, 'admin/user_edit.html', context)


def user_edit(request):
    telephone = request.POST.get('telephone', '')
    fullname = request.POST.get('fullname', '')
    birthday = request.POST.get('birthday', '')
    sex = request.POST.get('sex', '')
    user = AbstractUser.objects.get(telephone=telephone)
    user.fullname = fullname
    user.birthday = birthday
    user.sex = sex
    user.save()
    return HttpResponseRedirect(
        '/admin/user/edit/?telephone={0}&msg=success'.format(telephone))


def user_add(request):
    telephone = request.POST.get('telephone', '')
    print(telephone)
    result = AbstractUser.objects.filter(telephone=telephone).count()
    if result == 0:
        fullname = request.POST.get('fullname', '')
        birthday = request.POST.get('birthday', '')
        sex = request.POST.get('sex', '')
        password1 = request.POST.get('password1', '')
        user = AbstractUser(telephone=telephone,
                            fullname=fullname, birthday=birthday, sex=sex,
                            is_superuser=True, is_staff=True)
        user.set_password(password1)
        user.save()
        return HttpResponseRedirect('/admin/user/add/?msg=success')
    else:
        return HttpResponseRedirect('/admin/user/add/?msg=telephonerepeat')


def WriteToExcel(model_name):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet_s = workbook.add_worksheet(model_name)
    data = AbstractUser.objects.all()
    print('------------------------')
    title = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'center',
        'valign': 'vcenter'
    })
    header = workbook.add_format({
        'bg_color': '#F7F7F7',
        'color': 'black',
        'align': 'center',
        'valign': 'top',
        'border': 1
    })
    cell_format = workbook.add_format({
        'color': 'black',
        'align': 'center',
        'valign': 'top',
        'border': 1
    })
    date_format = workbook.add_format({
        'num_format': 'yyyy-mm-dd',
        'color': 'black',
        'align': 'center',
        'valign': 'top',
        'border': 1
    })

    datetime_format = workbook.add_format({
        'num_format': 'yyyy-mm-dd hh:mm:ss',
        'color': 'black',
        'align': 'center',
        'valign': 'top',
        'border': 1
    })
    title_text = u"{0} - {1}".format(ugettext("导出数据"), model_name)
    worksheet_s.merge_range('B2:H2', title_text, title)
    worksheet_s.write(4, 0, ugettext("手机号码"), header)
    worksheet_s.write(4, 1, ugettext("昵称"), header)
    worksheet_s.write(4, 2, ugettext("性别"), header)
    worksheet_s.write(4, 3, ugettext("生日"), header)
    worksheet_s.write(4, 4, ugettext("注册日期"), header)
    worksheet_s.write(4, 5, ugettext("最后登录"), header)
    worksheet_s.write(4, 6, ugettext("IP地址"), header)
    worksheet_s.write(4, 7, ugettext("状态"), header)
    i = 0
    for d in data:
        row = 5 + i
        worksheet_s.write_string(row, 0, d.telephone, cell_format)
        worksheet_s.write_string(row, 1, d.fullname, cell_format)
        worksheet_s.write_string(row, 2, d.get_sex_display(), cell_format)
        if d.birthday is not None:
            birthday = d.birthday
            as_datetime = datetime.date(
                birthday.year, birthday.month, birthday.day)
            worksheet_s.write_datetime(row, 3, as_datetime, date_format)
        else:
            worksheet_s.write_string(row, 3, '', date_format)
        if d.date_joined is not None:
            date_joined = timezone.localtime(d.date_joined)

            as_datetime = datetime.datetime(
                date_joined.year, date_joined.month, date_joined.day,
                date_joined.hour, date_joined.minute, date_joined.second)
            worksheet_s.write_datetime(row, 4, as_datetime, datetime_format)
        else:
            worksheet_s.write_string(row, 4, '', datetime_format)
        if d.last_login is not None:
            last_login = timezone.localtime(d.last_login)
            as_datetime = datetime.datetime(
                last_login.year, last_login.month, last_login.day,
                last_login.hour, last_login.minute, last_login.second)
            worksheet_s.write_datetime(row, 5, as_datetime, datetime_format)
        else:
            worksheet_s.write_string(row, 5, '', datetime_format)
        if d.ip_address is None:
            worksheet_s.write_string(row, 6, '', cell_format)
        else:
            worksheet_s.write_string(row, 6, d.ip_address, cell_format)
        if d.get_status_display() is None:
            worksheet_s.write_string(row, 7, '', cell_format)
        else:
            worksheet_s.write_string(
                row, 7, d.get_status_display(), cell_format)
        i = i + 1
    worksheet_s.set_column('A:A', len(d.telephone))
    worksheet_s.set_column('B:B', len(d.fullname) * 2)
    worksheet_s.set_column('D:D', len(str(d.birthday)))
    worksheet_s.set_column('E:E', len(str(d.date_joined)))
    worksheet_s.set_column('F:F', len(str(d.last_login) * 6))
    worksheet_s.set_column('G:G', len(str(d.ip_address) * 5))
    workbook.close()
    xls_data = output.getvalue()
    return xls_data


def export_excel(request):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Report.xlsx'
    xls_data = WriteToExcel('user')
    response.write(xls_data)
    return response


class ModelFormWithFileField(ModelForm):
    class Meta:
        model = UploadFileForm
        fields = ['title', 'file']


def import_excel_handle(filename):
    pass


def upload_view(request):
    if request.method == 'POST':
        print(request.POST)
        print(request.FILES)
        form = ModelFormWithFileField(request.POST, request.FILES)
        if form.is_valid():
            result = form.save()
            import_excel_handle(result.file)
            return HttpResponseRedirect('/admin/upload/success/')


def identity_manage_view(request):
    identity_log = IdentityLog.objects.all().annotate(
        active_per=F('active_num') / F('total') * 100)
    context = {'identity_log': identity_log, 'module_name': 'identitymanage'}
    return render(request, 'admin/identity_manage.html', context)


def identity_add_view(request):
    return render(request, 'admin/identity_add.html',
                  {'module_name': 'identityadd'})


def identityadd(request):
    total = request.POST.get('total', '')
    desc = request.POST.get('desc', '')
    currenttime = timezone.localtime(timezone.now())
    code = "{0}{1}".format(currenttime.strftime('%Y%m%d%H%M%S'),
                           random.randint(100000, 999999))
    log = IdentityLog(code=code, total=int(total),
                      created_user=request.user, desc=desc)
    log.save()
    querysetlist = []
    for a in range(int(total)):
        querysetlist.append(IdentityCard(
            code=random.randint(100000000, 999999999), log=log))
    IdentityCard.objects.bulk_create(querysetlist)
    return HttpResponseRedirect('/admin/identity/add/?msg=success')


def identity_edit_view(request):
    log = request.GET.get('log', '')
    identity_card = IdentityCard.objects.filter(log__code=log)
    context = {'identity_card': identity_card, 'module_name': 'identitymanage'}
    return render(request, 'admin/identity_edit.html', context)


def user_data_basic_view(request):
    card_count = IdentityCard.objects.count()
    binding_count = IdentityCard.objects.filter(
        drive__isnull=False).count()
    drive_count = Drive.objects.count()
    player_count = AbstractUser.objects.filter(is_superuser=False, is_staff=False).count()
    male_stat = AbstractUser.objects.filter(
        sex=1, is_superuser=False, is_staff=False).count()
    female_stat = AbstractUser.objects.filter(
        sex=2, is_superuser=False, is_staff=False).count()
    less_six_stat = AbstractUser.objects.filter(is_superuser=False,
                                                is_staff=False,
                                                birthday__year__gte=datetime.datetime.now().year - 6).count()
    bet_seven_eight_stat = AbstractUser.objects.filter(is_superuser=False,
                                                       is_staff=False,
                                                       birthday__year__range=(datetime.datetime.now().year - 8,
                                                                              datetime.datetime.now().year - 7)).count()
    bet_nine_ten_stat = AbstractUser.objects.filter(is_superuser=False,
                                                    is_staff=False,
                                                    birthday__year__range=(datetime.datetime.now().year - 10, datetime.datetime.now().year - 9)).count()
    bet_ten_twelve_stat = AbstractUser.objects.filter(is_superuser=False,
                                                      is_staff=False,
                                                      birthday__year__range=(datetime.datetime.now().year - 12, datetime.datetime.now().year - 10)).count()
    less_thridteen_stat = AbstractUser.objects.filter(is_superuser=False,
                                                      is_staff=False,
                                                      birthday__year__lte=datetime.datetime.now().year - 13).count()
    region_stat = AbstractUser.objects.filter(is_superuser=False,
                                              is_staff=False).values('region').annotate(total=Count('region')).order_by('-total')
    context = {'card_count': card_count,
               'player_count': player_count,
               'drive_count': drive_count,
               'binding_count':binding_count,
               'male_stat': male_stat,
               'female_stat': female_stat,
               'less_six_stat': less_six_stat,
               'bet_seven_eight_stat': bet_seven_eight_stat,
               'bet_nine_ten_stat': bet_nine_ten_stat,
               'bet_ten_twelve_stat': bet_ten_twelve_stat,
               'less_thridteen_stat': less_thridteen_stat,
               'region_stat': region_stat,
               'module_name': 'user_data_basic'}

    return render(request, 'admin/user_data/basic.html',
                  context)


def new_player_view(request):
    daily_start = datetime.date.today() + datetime.timedelta(-30)
    daily_data = []
    for a in range(30):
        daily_start = daily_start + datetime.timedelta(1)
        daily_data.append(str(daily_start.month) +
                          '-' + str(daily_start.day))
    daily_start = datetime.date.today() + datetime.timedelta(-30)
    month_start = utils.add_months(datetime.date.today(), -24)
    week_start = utils.add_months(datetime.date.today(), -12)
    with connection.cursor() as cursor:
        cursor.execute(("SELECT ac.dates, COALESCE(b.count,0) as total FROM "
                        "(SELECT to_char(date '" +
                        daily_start.strftime('%Y-%m-%d') +
                        "' + interval '1' DAY * s.a,'MM-DD') AS dates FROM "
                        "generate_series(0, 30) AS s (A) ) AS ac LEFT JOIN "
                        "( select to_char(date_joined,'MM-DD') as date,"
                        "count('id') as count from user_abstractuser "
                        "group by 1 ) as b ON ac.dates = b.date"))

        dailyrow = cursor.fetchall()
        cursor.execute(("SELECT ac.dates, COALESCE(b.count,0) as total"
                        " FROM (SELECT to_char(date '" +
                        month_start.strftime('%Y-%m-%d') +
                        "' + interval '1' MONTH * s.a,'YYYY-MM') "
                        "AS dates FROM generate_series(0, 24) AS s"
                        " (A) ) AS ac LEFT JOIN ( select to_char(date_joined,"
                        "'YYYY-MM') as date,count('id') as count from "
                        "user_abstractuser group by 1 ) as b"
                        " ON ac.dates = b.date"))
        monthrow = cursor.fetchall()
        cursor.execute(("SELECT ac.dates, COALESCE(b.count,0) as total"
                        " FROM (SELECT to_char(date '" +
                        week_start.strftime('%Y-%m-%d') +
                        "' + interval '1 week'  * s.a,'YYYY-第WW周')"
                        " AS dates FROM generate_series(0, 54) AS s (A)"
                        " ) AS ac LEFT JOIN ( select to_char(date_joined,"
                        "'YYYY-第WW周') as date,count('id') as count from "
                        "user_abstractuser group by 1 ) as b "
                        "ON ac.dates = b.date"))
        weekrow = cursor.fetchall()
        cursor.execute(("SELECT ac.dates, COALESCE(b.count,0) as total "
                        "FROM (SELECT to_char(date '" +
                        daily_start.strftime('%Y-%m-%d') +
                        "' + interval '1' DAY * s.a,'MM-DD') "
                        "AS dates FROM generate_series(0, 30) "
                        "AS s (A) ) AS ac LEFT JOIN ( select "
                        "to_char(date_joined,'MM-DD') as date,"
                        "count('id') as count from user_abstractuser "
                        "where sex = 1 group by 1 ) as b "
                        "ON ac.dates = b.date"))
        maledailyrow = cursor.fetchall()
        cursor.execute(("SELECT ac.dates, COALESCE(b.count,0) as total"
                        " FROM (SELECT to_char(date '" +
                        daily_start.strftime('%Y-%m-%d') +
                        "' + interval '1' DAY * s.a,'MM-DD') AS dates "
                        "FROM generate_series(0, 30) AS s (A) ) AS ac "
                        "LEFT JOIN ( select to_char(date_joined,'MM-DD') "
                        "as date,count('id') as count from user_abstractuser"
                        " where sex = 2 group by 1 ) as b "
                        "ON ac.dates = b.date"))
        femaledailyrow = cursor.fetchall()
        cursor.execute(("SELECT ac.dates, COALESCE(b.count,0) as total "
                        "FROM (SELECT to_char(date '" +
                        daily_start.strftime('%Y-%m-%d') +
                        "' + interval '1' DAY * s.a,'MM-DD') AS dates "
                        "FROM generate_series(0, 30) AS s (A) ) "
                        "AS ac LEFT JOIN ( select to_char(date_joined,'MM-DD')"
                        " as date,count('id') as count from user_abstractuser "
                        "where birthday >= '" +
                        str(datetime.date.today().year - 6) +
                        "-01-01' group by 1 ) as b ON ac.dates = b.date"))
        less_sixdailyrow = cursor.fetchall()
        cursor.execute(("SELECT ac.dates, COALESCE(b.count,0) as total "
                        "FROM (SELECT to_char(date '" +
                        daily_start.strftime('%Y-%m-%d') +
                        "' + interval '1' DAY * s.a,'MM-DD') "
                        "AS dates FROM generate_series(0, 30) "
                        "AS s (A) ) AS ac LEFT JOIN ( select "
                        "to_char(date_joined,'MM-DD') as date,"
                        "count('id') as count from user_abstractuser"
                        " where EXTRACT('year' FROM "
                        "user_abstractuser.birthday) BETWEEN " +
                        str(datetime.date.today().year - 8) +
                        " AND " +
                        str(datetime.date.today().year - 7) +
                        " group by 1 ) as b ON ac.dates = b.date"))
        bet_seven_eight_stat = cursor.fetchall()
        cursor.execute(("SELECT ac.dates, COALESCE(b.count,0) as total"
                        " FROM (SELECT to_char(date '" +
                        daily_start.strftime('%Y-%m-%d') +
                        "' + interval '1' DAY * s.a,'MM-DD') "
                        "AS dates FROM generate_series(0, 30) "
                        "AS s (A) ) AS ac LEFT JOIN ( select "
                        "to_char(date_joined,'MM-DD') as date,"
                        "count('id') as count from user_abstractuser"
                        " where EXTRACT('year' FROM "
                        "user_abstractuser.birthday) BETWEEN " +
                        str(datetime.date.today().year - 10) +
                        " AND " +
                        str(datetime.date.today().year - 9) +
                        " group by 1 ) as b ON ac.dates = b.date"))
        bet_nine_ten_stat = cursor.fetchall()
        cursor.execute(("SELECT ac.dates, COALESCE(b.count,0) as total "
                        "FROM (SELECT to_char(date '" +
                        daily_start.strftime('%Y-%m-%d') +
                        "' + interval '1' DAY * s.a,'MM-DD') AS"
                        " dates FROM generate_series(0, 30) AS "
                        "s (A) ) AS ac LEFT JOIN ( select "
                        "to_char(date_joined,'MM-DD') as date,"
                        "count('id') as count from user_abstractuser"
                        " where EXTRACT('year' FROM "
                        "user_abstractuser.birthday) BETWEEN " +
                        str(datetime.date.today().year - 12) +
                        " AND " +
                        str(datetime.date.today().year - 11) +
                        " group by 1 ) as b ON ac.dates = b.date"))
        bet_ten_twelve_stat = cursor.fetchall()
        cursor.execute(("SELECT ac.dates, COALESCE(b.count,0) as total"
                        " FROM (SELECT to_char(date '" +
                        daily_start.strftime('%Y-%m-%d') +
                        "' + interval '1' DAY * s.a,'MM-DD') "
                        "AS dates FROM generate_series(0, 30) "
                        "AS s (A) ) AS ac LEFT JOIN ( select "
                        "to_char(date_joined,'MM-DD') as date,"
                        "count('id') as count from user_abstractuser"
                        " where EXTRACT('year' "
                        "FROM user_abstractuser.birthday) < " +
                        str(datetime.date.today().year - 13) +
                        " group by 1 ) as b ON ac.dates = b.date"))
        less_thridteen_stat = cursor.fetchall()

    context = {
        'daily_user': dailyrow,
        'month_user': monthrow,
        'week_user': weekrow,
        'maledailyrow': maledailyrow,
        'femaledailyrow': femaledailyrow,
        'less_sixdailyrow': less_sixdailyrow,
        'bet_seven_eight_stat': bet_seven_eight_stat,
        'bet_nine_ten_stat': bet_nine_ten_stat,
        'bet_ten_twelve_stat': bet_ten_twelve_stat,
        'less_thridteen_stat': less_thridteen_stat,
        'module_name': 'user_data_added'}
    return render(request, 'admin/user_data/new_player.html',
                  context)


def get_sex_active_stat(start_date, end_date, sex):
    with connection.cursor() as cursor:
        cursor.execute(("SELECT Count(*) AS count "
                        "FROM   (SELECT user_abstractuser.id "
                        "FROM   user_gamelog, "
                        "user_gamelog_player, "
                        "user_abstractuser "
                        "WHERE  user_gamelog_player.gamelog_id ="
                        " user_gamelog.id "
                        "AND user_gamelog_player.abstractuser_id"
                        " = user_abstractuser.id "
                        "AND user_gamelog.start_time BETWEEN '" +
                        start_date.strftime('%Y-%m-%d') +
                        "' AND '" +
                        end_date.strftime('%Y-%m-%d') +
                        "' "
                        "AND user_abstractuser.sex = " +
                        str(sex) +
                        " GROUP  BY 1) AS a"))
        result = cursor.fetchone()
    return result[0]


def get_area_list(start_time, end_time):
    with connection.cursor() as cursor:
        cursor.execute(("SELECT a.region, "
                        "Count(*) AS count "
                        "FROM   (SELECT user_gamelog.region, "
                        "user_abstractuser.id "
                        " FROM   user_gamelog, "
                        "user_gamelog_player, "
                        "user_abstractuser "
                        " WHERE  user_gamelog_player.gamelog_id "
                        "= user_gamelog.id "
                        "AND user_gamelog_player.abstractuser_id "
                        "= user_abstractuser.id "
                        "AND user_gamelog.start_time BETWEEN '" +
                        start_time.strftime('%Y-%m-%d') +
                        "' AND '" +
                        end_time.strftime('%Y-%m-%d') +
                        "' "
                        " GROUP  BY 1, "
                        "2) AS a "
                        "GROUP  BY 1"))
        result = cursor.fetchall()
        print(end_time.strftime('%Y-%m-%d'))
    return result


def get_age_active_stat(start_date, end_date, start_age, end_age, expression):
    with connection.cursor() as cursor:
        if end_age == -1:
            cursor.execute(("SELECT Count(*) AS count "
                            "FROM   (SELECT user_abstractuser.id "
                            "FROM   user_gamelog, "
                            "user_gamelog_player, "
                            "user_abstractuser "
                            "WHERE  user_gamelog_player.gamelog_id ="
                            " user_gamelog.id "
                            "AND user_gamelog_player.abstractuser_id"
                            " = user_abstractuser.id "
                            "AND user_gamelog.start_time BETWEEN '" +
                            start_date.strftime('%Y-%m-%d') +
                            "' AND '" +
                            end_date.strftime('%Y-%m-%d') +
                            "' "
                            "AND EXTRACT('year' FROM "
                            "user_abstractuser.birthday) " +
                            expression +
                            " " +
                            str(start_age) +
                            " GROUP  BY 1) AS a"))
            result = cursor.fetchone()
        else:
            cursor.execute(("SELECT Count(*) AS count "
                            "FROM   (SELECT user_abstractuser.id "
                            "FROM   user_gamelog, "
                            "user_gamelog_player, "
                            "user_abstractuser "
                            "WHERE  user_gamelog_player.gamelog_id ="
                            " user_gamelog.id "
                            "AND user_gamelog_player.abstractuser_id"
                            " = user_abstractuser.id "
                            "AND user_gamelog.start_time BETWEEN '" +
                            start_date.strftime('%Y-%m-%d') +
                            "' AND '" +
                            end_date.strftime('%Y-%m-%d') +
                            "' "
                            "AND EXTRACT('year' FROM "
                            "user_abstractuser.birthday)  between " +
                            str(start_age) +
                            " and " +
                            str(end_age) +
                            " GROUP  BY 1) AS a"))
            result = cursor.fetchone()
    return result[0]


def get_played_day_over(start_time,end_time,over):
    return utils.execute_custom_sql_fetchone(("SELECT Count(*) AS count "
                                        "FROM   (SELECT fullname, "
                                        "Count(fullname) AS count "
                                        "FROM   (SELECT user_abstractuser.fullname, "
                                        "To_char(user_gamelog.start_time, 'YYYY-MM-DD') AS c "
                                        "FROM   user_gamelog, "
                                        "user_gamelog_player, "
                                        "user_abstractuser "
                                        "WHERE  user_gamelog_player.gamelog_id = user_gamelog.id "
                                        "AND user_gamelog_player.abstractuser_id = "
                                        "    user_abstractuser.id "
                                        "AND user_gamelog.start_time BETWEEN "
                                        "'" +
                                        start_time.strftime('%Y-%m-%d') +
                                        "' AND '" +
                                        end_time.strftime('%Y-%m-%d') +
                                        "' "
                                        "GROUP  BY 1, "
                                        "2)AS a "
                                        "GROUP  BY 1) AS b "
                                        "WHERE  count >= " + str(over)))


def get_played_day(start_time,end_time, begin, end):
    return utils.execute_custom_sql_fetchone(("SELECT Count(*) AS count "
                                        "FROM   (SELECT fullname, "
                                        "Count(fullname) AS count "
                                        "FROM   (SELECT user_abstractuser.fullname, "
                                        "To_char(user_gamelog.start_time, 'YYYY-MM-DD') AS c "
                                        "FROM   user_gamelog, "
                                        "user_gamelog_player, "
                                        "user_abstractuser "
                                        "WHERE  user_gamelog_player.gamelog_id = user_gamelog.id "
                                        "AND user_gamelog_player.abstractuser_id = "
                                        "    user_abstractuser.id "
                                        "AND user_gamelog.start_time BETWEEN "
                                        "'" +
                                        start_time.strftime('%Y-%m-%d') +
                                        "' AND '" +
                                        end_time.strftime('%Y-%m-%d') +
                                        "' "
                                        "GROUP  BY 1, "
                                        "2)AS a "
                                        "GROUP  BY 1) AS b "
                                        "WHERE  count >= "+
                                        str(begin) +" "
                                        "AND count <= " + str(end)))


def player_active_view(request):
    daily_start = datetime.date.today() + datetime.timedelta(-30)
    month_start = utils.add_months(datetime.date.today(), -24)
    week_start = utils.add_months(datetime.date.today(), -12)
    with connection.cursor() as cursor:
        cursor.execute((""
                        "SELECT ac.dates, "
                        "    COALESCE(b.count,0) as total "
                        "FROM "
                        "    ( "
                        "        SELECT "
                        " to_char(date '" +
                        daily_start.strftime('%Y-%m-%d') +
                        "' + interval '1 day' "
                        " * s.a,'YYYY-MM-DD') "
                        "             AS dates "
                        "        FROM "
                        "            generate_series(0, 30) AS s (A) "
                        "    ) AS ac "
                        "LEFT JOIN ( "
                        "select a.date, count(*) as count from ( "
                        " SELECT "
                        "  to_char(start_time,'YYYY-MM-DD') as date "
                        ",user_abstractuser.id "
                        "FROM "
                        "  user_gamelog, "
                        "  user_gamelog_player, "
                        "  user_abstractuser "
                        "WHERE "
                        "user_gamelog_player.gamelog_id = user_gamelog.id AND "
                        "user_gamelog_player.abstractuser_id = "
                        "user_abstractuser.id ""AND "
                        "to_char(user_abstractuser.date_joined,'YYYY-MM-DD')"
                        " =  to_char(user_gamelog.start_time,'YYYY-MM-DD') "
                        "group by 1,2) as a group by 1 "
                        ") as b ON ac.dates = b.date"))
        # 每日新用户活跃
        daily_newplayer = cursor.fetchall()
        cursor.execute((""
                        "SELECT ac.dates, "
                        "    COALESCE(b.count,0) as total "
                        "FROM "
                        "    ( "
                        "        SELECT "
                        " to_char(date '" +
                        week_start.strftime('%Y-%m-%d') +
                        "' + interval '1 week' "
                        " * s.a,'YYYY-第WW周') "
                        "             AS dates "
                        "        FROM "
                        "            generate_series(0, 54) AS s (A) "
                        "    ) AS ac "
                        "LEFT JOIN ( "
                        "select a.date, count(*) as count from ( "
                        " SELECT "
                        "  to_char(start_time,'YYYY-第WW周') as date "
                        ",user_abstractuser.id "
                        "FROM "
                        "  user_gamelog, "
                        "  user_gamelog_player, "
                        "  user_abstractuser "
                        "WHERE "
                        "user_gamelog_player.gamelog_id = user_gamelog.id AND "
                        "user_gamelog_player.abstractuser_id = "
                        "user_abstractuser.id ""AND "
                        "to_char(user_abstractuser.date_joined,'YYYY-第WW周')"
                        " =  to_char(user_gamelog.start_time,'YYYY-第WW周') "
                        "group by 1,2) as a group by 1 "
                        ") as b ON ac.dates = b.date"))
        # 每周新用户活跃
        week_newplayer = cursor.fetchall()
        cursor.execute((""
                        "SELECT ac.dates, "
                        "    COALESCE(b.count,0) as total "
                        "FROM "
                        "    ( "
                        "        SELECT "
                        " to_char(date '" +
                        month_start.strftime('%Y-%m-%d') +
                        "' + interval '1 month' "
                        " * s.a,'YYYY-MM') "
                        "             AS dates "
                        "        FROM "
                        "            generate_series(0, 24) AS s (A) "
                        "    ) AS ac "
                        "LEFT JOIN ( "
                        "select a.date, count(*) as count from ( "
                        " SELECT "
                        "  to_char(start_time,'YYYY-MM') as date "
                        ",user_abstractuser.id "
                        "FROM "
                        "  user_gamelog, "
                        "  user_gamelog_player, "
                        "  user_abstractuser "
                        "WHERE "
                        "user_gamelog_player.gamelog_id = user_gamelog.id AND "
                        "user_gamelog_player.abstractuser_id = "
                        "user_abstractuser.id ""AND "
                        "to_char(user_abstractuser.date_joined,'YYYY-MM')"
                        " =  to_char(user_gamelog.start_time,'YYYY-MM') "
                        "group by 1,2) as a group by 1 "
                        ") as b ON ac.dates = b.date"))
        # 每月新用户活跃
        month_newplayer = cursor.fetchall()
        # 老用户
        cursor.execute((""
                        "SELECT ac.dates, "
                        "    COALESCE(b.count,0) as total "
                        "FROM "
                        "    ( "
                        "        SELECT "
                        " to_char(date '" +
                        daily_start.strftime('%Y-%m-%d') +
                        "' + interval '1 day' "
                        " * s.a,'YYYY-MM-DD') "
                        "             AS dates "
                        "        FROM "
                        "            generate_series(0, 30) AS s (A) "
                        "    ) AS ac "
                        "LEFT JOIN ( "
                        "select a.date, count(*) as count from ( "
                        " SELECT "
                        "  to_char(start_time,'YYYY-MM-DD') as date "
                        ",user_abstractuser.id "
                        "FROM "
                        "  user_gamelog, "
                        "  user_gamelog_player, "
                        "  user_abstractuser "
                        "WHERE "
                        "user_gamelog_player.gamelog_id = user_gamelog.id AND "
                        "user_gamelog_player.abstractuser_id = "
                        "user_abstractuser.id ""AND "
                        "to_char(user_abstractuser.date_joined,'YYYY-MM-DD')"
                        " <>  to_char(user_gamelog.start_time,'YYYY-MM-DD') "
                        "group by 1,2) as a group by 1 "
                        ") as b ON ac.dates = b.date"))
        # 每日老用户活跃
        daily_oldplayer = cursor.fetchall()
        cursor.execute((""
                        "SELECT ac.dates, "
                        "    COALESCE(b.count,0) as total "
                        "FROM "
                        "    ( "
                        "        SELECT "
                        " to_char(date '" +
                        week_start.strftime('%Y-%m-%d') +
                        "' + interval '1 week' "
                        " * s.a,'YYYY-第WW周') "
                        "             AS dates "
                        "        FROM "
                        "            generate_series(0, 54) AS s (A) "
                        "    ) AS ac "
                        "LEFT JOIN ( "
                        "select a.date, count(*) as count from ( "
                        " SELECT "
                        "  to_char(start_time,'YYYY-第WW周') as date "
                        ",user_abstractuser.id "
                        "FROM "
                        "  user_gamelog, "
                        "  user_gamelog_player, "
                        "  user_abstractuser "
                        "WHERE "
                        "user_gamelog_player.gamelog_id = user_gamelog.id AND "
                        "user_gamelog_player.abstractuser_id = "
                        "user_abstractuser.id ""AND "
                        "to_char(user_abstractuser.date_joined,'YYYY-第WW周')"
                        " <>  to_char(user_gamelog.start_time,'YYYY-第WW周') "
                        "group by 1,2) as a group by 1 "
                        ") as b ON ac.dates = b.date"))
        # 每周老用户活跃
        week_oldplayer = cursor.fetchall()
        cursor.execute((""
                        "SELECT ac.dates, "
                        "    COALESCE(b.count,0) as total "
                        "FROM "
                        "    ( "
                        "        SELECT "
                        " to_char(date '" +
                        month_start.strftime('%Y-%m-%d') +
                        "' + interval '1 month' "
                        " * s.a,'YYYY-MM') "
                        "             AS dates "
                        "        FROM "
                        "            generate_series(0, 24) AS s (A) "
                        "    ) AS ac "
                        "LEFT JOIN ( "
                        "select a.date, count(*) as count from ( "
                        " SELECT "
                        "  to_char(start_time,'YYYY-MM') as date "
                        ",user_abstractuser.id "
                        "FROM "
                        "  user_gamelog, "
                        "  user_gamelog_player, "
                        "  user_abstractuser "
                        "WHERE "
                        "user_gamelog_player.gamelog_id = user_gamelog.id AND "
                        "user_gamelog_player.abstractuser_id = "
                        "user_abstractuser.id ""AND "
                        "to_char(user_abstractuser.date_joined,'YYYY-MM')"
                        " <>  to_char(user_gamelog.start_time,'YYYY-MM') "
                        "group by 1,2) as a group by 1 "
                        ") as b ON ac.dates = b.date"))
        # 每月老用户活跃
        month_oldplayer = cursor.fetchall()

        # 临时用户
        cursor.execute(("SELECT    ac.dates, "
                        "COALESCE(b.count,0) AS total "
                        "FROM ( "
                        "SELECT to_char(date '" +
                        daily_start.strftime('%Y-%m-%d') +
                        "' + interval '1 day' * s.a,'YYYY-MM-DD') AS dates "
                        "FROM   generate_series(0, 30) AS s (a) ) AS ac "
                        "LEFT JOIN "
                        "( "
                        "SELECT   to_char(start_time,'YYYY-MM-DD') AS date , "
                        "         sum(tempplayer)               AS count "
                        "FROM     user_gamelog "
                        "GROUP BY 1 ) AS b "
                        "ON        ac.dates = b.date"))
        # 每日临时用户活跃
        daily_tempplayer = cursor.fetchall()
        cursor.execute(("SELECT    ac.dates, "
                        "COALESCE(b.count,0) AS total "
                        "FROM ( "
                        "SELECT to_char(date '" +
                        week_start.strftime('%Y-%m-%d') +
                        "' + interval '1 day' * s.a,'YYYY-第WW周') AS dates "
                        "FROM   generate_series(0, 54) AS s (a) ) AS ac "
                        "LEFT JOIN "
                        "( "
                        "SELECT   to_char(start_time,'YYYY-第WW周') AS date , "
                        "         sum(tempplayer)               AS count "
                        "FROM     user_gamelog "
                        "GROUP BY 1 ) AS b "
                        "ON        ac.dates = b.date"))
        # 每周临时用户活跃
        week_tempplayer = cursor.fetchall()
        cursor.execute(("SELECT    ac.dates, "
                        "COALESCE(b.count,0) AS total "
                        "FROM ( "
                        "SELECT to_char(date '" +
                        month_start.strftime('%Y-%m-%d') +
                        "' + interval '1 week' * s.a,'YYYY-MM') AS dates "
                        "FROM   generate_series(0, 54) AS s (a) ) AS ac "
                        "LEFT JOIN "
                        "( "
                        "SELECT   to_char(start_time,'YYYY-MM') AS date , "
                        "         sum(tempplayer)               AS count "
                        "FROM     user_gamelog "
                        "GROUP BY 1 ) AS b "
                        "ON        ac.dates = b.date"))
        # 每月临时用户活跃
        month_tempplayer = cursor.fetchall()

        daily_male = get_sex_active_stat(daily_start, datetime.date.today(), 1)
        daily_female = get_sex_active_stat(
            daily_start, datetime.date.today(), 2)
        daily_less_six = get_age_active_stat(daily_start,
                                             datetime.date.today(),
                                             datetime.date.today().year - 6,
                                             -1, '>')
        daily_seven_eight = get_age_active_stat(daily_start,
                                                datetime.date.today(),
                                                datetime.date.today().year - 8,
                                                datetime.date.today().year - 7,
                                                '>')
        daily_nine_ten = get_age_active_stat(daily_start,
                                             datetime.date.today(),
                                             datetime.date.today().year - 10,
                                             datetime.date.today().year - 9,
                                             '>')
        daily_ten_twelve = get_age_active_stat(daily_start,
                                               datetime.date.today(),
                                               datetime.date.today().year - 12,
                                               datetime.date.today().year - 10,
                                               '>')
        daily_more_twelve = get_age_active_stat(daily_start,
                                                datetime.date.today(),
                                                datetime.date.today().year - 13,
                                                -1, '<')

        area_list = get_area_list(daily_start, datetime.date.today())
        for a in area_list:
            print(a[0])
        new_player_list = utils.execute_custom_sql_fetchone(("SELECT Count(*)"
                                                             "FROM (SELECT "
                                                             "To_char"
                                                             "(user_gamelog."
                                                             "start_time,"
                                                             " 'YYYY-MM-DD') "
                                                             "AS c "
                                                             "FROM "
                                                             "user_gamelog,"
                                                             "user_gamelog_"
                                                             "player,"
                                                             "user_"
                                                             "abstractuser "
                                                             "WHERE  "
                                                             "user_gamelog_"
                                                             "player."
                                                             "gamelog_id ="
                                                             "user_gamelog.id "
                                                             "AND user_gamelog"
                                                             "_player."
                                                             "abstractuser_id"
                                                             " = user_abstract"
                                                             "user.id "
                                                             "AND user_gamelog"
                                                             ".start_time "
                                                             "BETWEEN '" +
                                                             daily_start.strftime('%Y-%m-%d') +
                                                             "' AND '" +
                                                             datetime.date.today().strftime('%Y-%m-%d') +
                                                             "' "
                                                             "AND To_char(user_gamelog.start_time, 'YYYY-MM-DD') = To_char( "
                                                             "user_abstractuser.date_joined, 'YYYY-MM-DD') "
                                                             "GROUP  BY c)AS a"))
        from_2_3_list = get_played_day(
            daily_start,
            datetime.date.today(),
            2,
            3)
        from_4_7_list = get_played_day(
            daily_start,
            datetime.date.today(),
            4,
            7)
        from_8_14_list = get_played_day(
            daily_start,
            datetime.date.today(),
            8,
            14)
        from_15_30_list = get_played_day(
            daily_start,
            datetime.date.today(),
            15,
            30)
        from_31_90_list = get_played_day(
            daily_start,
            datetime.date.today(),
            31,
            90)
        from_91_180_list = get_played_day(
            daily_start,
            datetime.date.today(),
            91,
            180)
        from_181_365_list = get_played_day(
            daily_start,
            datetime.date.today(),
            181,
            365)
        over_365_list = get_played_day_over(
            daily_start,
            datetime.date.today(),
            365)

    context = {
        'daily_newplayer': daily_newplayer,
        'daily_oldplayer': daily_oldplayer,
        'daily_tempplayer': daily_tempplayer,
        'week_newplayer': week_newplayer,
        'week_oldplayer': week_oldplayer,
        'week_tempplayer': week_tempplayer,
        'month_newplayer': month_newplayer,
        'month_oldplayer': month_oldplayer,
        'month_tempplayer': month_tempplayer,
        'daily_male': daily_male,
        'daily_female': daily_female,
        'daily_less_six': daily_less_six,
        'daily_seven_eight': daily_seven_eight,
        'daily_nine_ten': daily_nine_ten,
        'daily_ten_twelve': daily_ten_twelve,
        'daily_more_twelve': daily_more_twelve,
        'area_list': area_list,
        'new_player_list': new_player_list,
        'from_2_3_list': from_2_3_list,
        'from_4_7_list': from_4_7_list,
        'from_8_14_list': from_8_14_list,
        'from_15_30_list': from_15_30_list,
        'from_31_90_list': from_31_90_list,
        'from_91_180_list': from_91_180_list,
        'from_181_365_list': from_181_365_list,
        'over_365_list': over_365_list,
        'module_name': 'user_data_active'}
    return render(request, 'admin/user_data/player_active.html', context)


def player_stay_view(request):
    daily_start = datetime.date.today() + datetime.timedelta(-30)
    next_day = utils.execute_custom_sql_fetchall(("SELECT ac.dates, "
                                                    "COALESCE(b.count,0) AS total "
                                                    "FROM ( "
                                                    "SELECT to_char(date '" +
                                                    daily_start.strftime('%Y-%m-%d') +
                                                    "' + interval '1 day' * s.a,'YYYY-MM-DD') AS dates "
                                                    "FROM   generate_series(0, 30) AS s (a) ) AS ac "
                                                    "LEFT JOIN "
                                                    "(select date,count(*) from (SELECT "
                                                    "to_char(start_time,'YYYY-MM-DD') AS date,user_abstractuser.id "
                                                    "FROM "
                                                    "  public.user_gamelog, "
                                                    "  public.user_gamelog_player, "
                                                    "  public.user_abstractuser "
                                                    "WHERE "
                                                    "  user_gamelog_player.gamelog_id = user_gamelog.id AND "
                                                    "  user_gamelog_player.abstractuser_id = user_abstractuser.id AND "
                                                    "  to_char(user_gamelog.start_time,'YYYY-MM-DD') = to_char(user_abstractuser.date_joined::timestamp + '1 day','YYYY-MM-DD') group by 1,2 ) as c  group by 1 "
                                                    ") AS b "
                                                    "ON ac.dates = b.date"))
    seven_day = utils.execute_custom_sql_fetchall(("SELECT ac.dates, "
                                                    "COALESCE(b.count,0) AS total "
                                                    "FROM ( "
                                                    "SELECT to_char(date '" +
                                                    daily_start.strftime('%Y-%m-%d') +
                                                    "' + interval '1 day' * s.a,'YYYY-MM-DD') AS dates "
                                                    "FROM   generate_series(0, 30) AS s (a) ) AS ac "
                                                    "LEFT JOIN "
                                                    "(select date,count(*) from (SELECT "
                                                    "to_char(start_time,'YYYY-MM-DD') AS date,user_abstractuser.id "
                                                    "FROM "
                                                    "  public.user_gamelog, "
                                                    "  public.user_gamelog_player, "
                                                    "  public.user_abstractuser "
                                                    "WHERE "
                                                    "  user_gamelog_player.gamelog_id = user_gamelog.id AND "
                                                    "  user_gamelog_player.abstractuser_id = user_abstractuser.id AND "
                                                    "  to_char(user_gamelog.start_time,'YYYY-MM-DD') between to_char(user_abstractuser.date_joined::timestamp + '1 day','YYYY-MM-DD') and to_char(user_abstractuser.date_joined::timestamp + '7 day','YYYY-MM-DD')  group by 1,2 ) as c  group by 1 "
                                                    ") AS b "
                                                    "ON ac.dates = b.date"))

    thirdty_day = utils.execute_custom_sql_fetchall(("SELECT ac.dates, "
                                                    "COALESCE(b.count,0) AS total "
                                                    "FROM ( "
                                                    "SELECT to_char(date '" +
                                                    daily_start.strftime('%Y-%m-%d') +
                                                    "' + interval '1 day' * s.a,'YYYY-MM-DD') AS dates "
                                                    "FROM   generate_series(0, 30) AS s (a) ) AS ac "
                                                    "LEFT JOIN "
                                                    "(select date,count(*) from (SELECT "
                                                    "to_char(start_time,'YYYY-MM-DD') AS date,user_abstractuser.id "
                                                    "FROM "
                                                    "  public.user_gamelog, "
                                                    "  public.user_gamelog_player, "
                                                    "  public.user_abstractuser "
                                                    "WHERE "
                                                    "  user_gamelog_player.gamelog_id = user_gamelog.id AND "
                                                    "  user_gamelog_player.abstractuser_id = user_abstractuser.id AND "
                                                    "  to_char(user_gamelog.start_time,'YYYY-MM-DD') between to_char(user_abstractuser.date_joined::timestamp + '1 day','YYYY-MM-DD') and to_char(user_abstractuser.date_joined::timestamp + '30 day','YYYY-MM-DD')  group by 1,2 ) as c  group by 1 "
                                                    ") AS b "
                                                    "ON ac.dates = b.date"))
    context = {
            'next_day':next_day,
            'seven_day':seven_day,
            'thirdty_day':thirdty_day,
            'module_name': 'user_data_stay'
            }
    return render(request, 'admin/user_data/player_stay.html', context)

