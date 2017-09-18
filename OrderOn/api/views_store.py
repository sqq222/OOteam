import random

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from rest_framework import status
from rest_framework import views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from shop.user.models import *
from .exception_handler import Error, ErrorResponse
from .serializers import *
from shop import utils

_letter_cases = "abcdefghjkmnpqrstuvwxy"  # 去除可能干扰的i，l，o，z
_upper_cases = _letter_cases.upper()  # 大写字母
_numbers = ''.join(map(str, range(3, 10)))  # 数字
init_chars = ''.join((_letter_cases, _upper_cases, _numbers))


class SignUp(views.APIView):
    permission_classes = (AllowAny,)
    serializers_classes = LoginSerializer

    def post(self, request, *args, **kwargs):
        if 'username' not in request.data:
            raise Error(err_code="400", err_message="Params error", message=u'用户名不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)
        if 'fullname' not in request.data:
            raise Error(err_code="400", err_message="Params error", message=u'昵称不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)
        if 'sex' not in request.data:
            raise Error(err_code="400", err_message="Params error", message=u'性别不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)
        if 'birthday' not in request.data:
            raise Error(err_code="400", err_message="Params error", message=u'生日不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)
        if 'region' not in request.data:
            raise Error(err_code="400", err_message="Params error", message=u'地区不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)
        if 'email' not in request.data:
            raise Error(err_code="400", err_message="Params error", message=u'Email不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)
        if AbstractUser.objects.filter(username=request.data['username']).exists():
            raise Error(err_code=1001, err_message="Username is exist", message=u'用户名已存在')

        user = AbstractUser(username=request.data['username'], fullname=request.data['fullname'],
                            sex=request.data['sex'],
                            birthday=request.data['birthday'], region=request.data['region'],
                            email=request.data['email'], is_active=True)
        user.save()
        code = ''.join(random.sample(init_chars, 6)).upper()
        user.code = code
        user.save()

        subject = '来自商城系统'

        text_content = '这是一封重要的激活邮件. 您的激活码是：' + code

        html_content = '<p>您的激活码是：<strong>' + code + '</strong></p>'

        msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email, ])

        msg.attach_alternative(html_content, "text/html")

        msg.send()

        if user is not None:
            return Response({'success': True})
        else:
            raise Error(err_code="500", err_message="Server error", message=u'服务器错误',
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegCodeVer(views.APIView):
    permission_classes = (AllowAny,)
    serializers_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        if 'username' not in request.data:
            raise Error(err_code="400", err_message="Params error", message=u'用户名不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)
        if 'code' not in request.data:
            raise Error(err_code="400", err_message="Params error", message=u'验证码不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)
        if 'password' not in request.data:
            raise Error(err_code="400", err_message="Params error", message=u'密码不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)
        user = AbstractUser.objects.get(username=request.data['username'])
        if user is not None:

            if user.code.upper() == request.data['code'].upper():
                user.set_password(request.data['password'])

                user.save()
                return Response({'success': True})
            else:
                return Response({'success': False})

        return Response({'success': False})


class Forget_PwdView(views.APIView):
    """
    忘记密码
    提交emial，验证是否存在
    """
    permission_classes = (AllowAny,)
    serializers_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        if 'username' not in request.data:
            raise Error(err_code="400", err_message="Params error", message=u'username不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)
        user = AbstractUser.objects.filter(
            Q(email=request.data['username']) | Q(username=request.data['username'])).first()
        if user is None:
            raise Error(err_code=402, err_message='User is not exist.', message='用户不存在',
                        status_code=status.HTTP_402_PAYMENT_REQUIRED)
        # 生成验证码
        code = ''.join(random.sample(init_chars, 6)).upper()
        user.code = code
        user.save()

        # 发送邮件
        subject = '来自商城系统'

        text_content = '这是一封重要的激活邮件. 您的激活码是：' + code

        html_content = '<p>您的激活码是：<strong>' + code + '</strong></p>'

        msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email, ])

        msg.attach_alternative(html_content, "text/html")

        msg.send()
        return Response({'success': True, 'email': user.email})


class Forget_CodeVer(views.APIView):
    """
    忘记密码
    提交code，验证code是否一致
    """
    permission_classes = (AllowAny,)
    serializers_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        if 'email' not in request.data:
            raise Error(err_code="400", err_message="Params error", message=u'email不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)
        if 'code' not in request.data:
            raise Error(err_code="400", err_message="Params error", message=u'验证码不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)
        user = AbstractUser.objects.filter(email=request.data['email']).first()
        if user is not None:
            if user.code.upper() == request.data['code'].upper():
                return Response({'success': True})
            else:
                return Response({'success': False})

        return Response({'success': False})


class Change_PwdView(views.APIView):
    """
    忘记密码 - 修改密码
    """
    permission_classes = (AllowAny,)
    serializers_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        if 'email' not in request.data:
            raise Error(err_code="400", err_message="Params error", message=u'email不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)
        if 'code' not in request.data:
            raise Error(err_code="400", err_message="Params error", message=u'验证码不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)
        if 'password' not in request.data:
            raise Error(err_code="400", err_message="Params error", message=u'密码不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)
        user = AbstractUser.objects.filter(email=request.data['email']).first()
        if user is not None:
            if user.code.upper() == request.data['code'].upper():
                user.set_password(request.data['password'])
                user.basemob_uuid = utils.Easemob.change_password(user.username, user.password)
                user.save()
                return Response({'success': True})
            else:
                return Response({'success': False})

        return Response({'success': False})


class StoreView(views.APIView):
    """
    门店信息
    """
    permission_classes = (AllowAny,)
    serializers_class = StoreSerializer

    def get(self, request, *args, **kwargs):
        """
        参数：无 
        :return: 
        
        """
        print(request.user)
        if request.user.is_authenticated():
            serializers = StoreSerializer(request.user)
            return Response(serializers.data)
        else:
            return Response({"errors": "User is not authenticated"}, status=status.HTTP_400_BAD_REQUEST)


class Store_Add_Business_Time(views.APIView):
    """
    添加营业时间
    """
    permission_classes = (AllowAny,)

    # serializers_classes = Store_Business_TimeSerializer

    def post(self, request, *args, **kwargs):
        # if not request.user.is_authenticated():
        #     raise AuthenticationFailed('Invalid username or password')
        # else:

        start_normal = request.POST.get('start_normal', '')
        end_normal = request.POST.get('end_normal', '')
        start_holiday = request.POST.get('start_holiday', '')
        end_holiday = request.POST.get('end_holiday', '')
        last_normal = request.POST.get('last_normal', '')
        last_holiday = request.POST.get('last_holiday', '')
        start_rest_normal = request.POST.get('start_rest_normal', '')
        end_rest_normal = request.POST.get('end_rest_normal', '')
        start_rest_holiday = request.POST.get('start_rest_holiday', '')
        end_rest_holiday = request.POST.get('end_rest_holiday', '')
        week_free_day = request.POST.get('week_free_day', '')
        store = request.POST.get('store', '')
        if store is None:
            return ErrorResponse(400, '参数错误',
                                 status.HTTP_400_BAD_REQUEST)
        sbt = Store_Business_Time(start_normal=start_normal, end_normal=end_normal, start_holiday=start_holiday,
                                  end_holiday=end_holiday,
                                  last_normal=last_normal, last_holiday=last_holiday,
                                  start_rest_normal=start_rest_normal, end_rest_normal=end_rest_normal,
                                  start_rest_holiday=start_rest_holiday, end_rest_holiday=end_rest_holiday,
                                  week_free_day=week_free_day)
        sbt.save()
        if store is not '':
            Stores.objects.filter(id=store).update(business_time=sbt)
        return Response({'success': True})


class Store_Business_Time_FreeDay_View(views.APIView):
    """
    定休日
    """
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        """
        添加定休日
        :param store: 店铺ID
        :param freeday:  定休日
        :return: success
        """
        store = request.POST.get('store', '')
        freeday = request.POST.get('freeday', '')
        print('--------' + store)

        sbtf = Store_Business_Time_FreeDay(store_business_time=Stores.objects.get(id=store).business_time,
                                           free_day=freeday)
        sbtf.save()
        return Response({'success': True})


class Store_Business_Time_View(views.APIView):
    permission_classes = (AllowAny,)
    serializers = Store_Business_Time_Serializer

    def get(self, request, *args, **kwargs):
        sbt = Stores.objects.get(id=self.kwargs['pk']).business_time
        serializers = Store_Business_Time_Serializer(sbt)
        return Response(serializers.data)


class Store_Notice(views.APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        notice = request.POST.get('notice', '')
        business = Stores.objects.get(id=self.kwargs['pk']).business
        Store_Business.objects.filter(id=business.id).update(notice=notice)
        return Response({'success': True})


class Store_Desc(views.APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        desc = request.POST.get('desc', '')
        business = Stores.objects.get(id=self.kwargs['pk']).business
        Store_Business.objects.filter(id=business.id).update(desc=desc)
        return Response({'success': True})


class Store_Change_Pwd_View(views.APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        pwd = request.POST.get('pwd', '')
        business = Stores.objects.get(id=self.kwargs['pk']).business
        Store_Business.objects.filter(id=business.id).update(pwd=pwd)
        return Response({'success': True})
