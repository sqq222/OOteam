from rest_framework import status

from shop.api.exception_handler import Error
from shop.user.models import Meal


def is_login(func):
    def wrapper(self, request):
        if request.user.is_authenticated():
            return func(self, request)
        else:
            raise Error(err_code="401", err_message="Token error", message=u'未登录',
                        status_code=status.HTTP_401_UNAUTHORIZED)

    return wrapper


def meal_check(func):
    def wrapper(self, request):
        meal = request.data.get('meal', None)
        if meal is None:
            raise Error(err_code="401", err_message="Meal error", message=u'Meal 参数错误',
                        status_code=status.HTTP_401_UNAUTHORIZED)
        try:
            meal = Meal.objects.get(id=meal)
            if meal.status == 1:
                raise Error(err_code="401", err_message="Meal error", message=u'Meal 已离座',
                            status_code=status.HTTP_401_UNAUTHORIZED)
            request.meal = meal
            return func(self, request)
        except Meal.DoesNotExist:
            raise Error(err_code="401", err_message="Meal error", message=u'Meal 参数错误',
                        status_code=status.HTTP_401_UNAUTHORIZED)

    return wrapper
