from __future__ import absolute_import, unicode_literals

import datetime

from celery import Celery, shared_task

from shop.user.models import Meal, Order, PayInfo


@shared_task
def auto_meal_leave(meal):
    meal = Meal.objects.filter(id=meal)
    if meal.exists():
        meal = meal.first()
        order = Order.objects.filter(meal=meal)
        for o in order:
            if o.status > 0:
                return True
        meal.status = 1
        meal.save()
        return True
    else:
        return True

@shared_task
def auto_meal_leave_payed(meal):
    meal = Meal.objects.filter(id=meal)
    if meal.exists():
        meal = meal.first()
        payinfo = PayInfo.objects.filter(user__order__meal__id=meal).order_by('-created')
        p = payinfo.first()
        if p.created + datetime.timedelta(hours=5) > datetime.datetime.now():
            meal.status = 1
            meal.save()
        return True
    else:
        return True
