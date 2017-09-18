import datetime
import calendar
from django.db import connection


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = int(sourcedate.year + month / 12)
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


def execute_custom_sql_fetchall(sql):
    with connection.cursor() as cursor:
        cursor.execute(sql)
        result = cursor.fetchall()
    return result


def execute_custom_sql_fetchone(sql):
    with connection.cursor() as cursor:
        cursor.execute(sql)
        result = cursor.fetchone()
    return result[0]
