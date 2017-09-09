# from django.utils.timezone import utc
import calendar
from functools import reduce

import pytz
from django.db.models import Q, FieldDoesNotExist, Count, F
from django.db.models.fields.reverse_related import ForeignObjectRel
from oauth2_provider.models import AccessToken
from rest_framework import status
from rest_framework import views, generics, permissions
from rest_framework.decorators import list_route, detail_route
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from shop import utils
from shop.api import errors
from shop.api.decorators import is_login, meal_check
from shop.api.tasks import auto_meal_leave
from shop.user.serializers import *
from shop.utils import AESCustom
from .exception_handler import Error, ForeignObjectRelDeleteError, ModelDontHaveIsActiveFiled
from .serializers import *

# from pytz import timezone

# AbstractUser = get_user_model()

logger = logging.getLogger('docs.view')


class UnActiveModelMixin(object):
    """ 
    删除一个对象，并不真删除，级联将对应外键对象的is_active设置为false，需要外键对象都有is_active字段.
    """

    def perform_destroy(self, instance):
        rel_fileds = [f for f in instance._meta.get_fields() if isinstance(f, ForeignObjectRel)]

        links = [f.get_accessor_name() for f in rel_fileds]

        for link in links:
            manager = getattr(instance, link, None)
            if not manager:
                continue
            if isinstance(manager, models.Model):
                if hasattr(manager, 'is_active') and manager.is_active:
                    manager.is_active = False
                    manager.save()
                    raise ForeignObjectRelDeleteError(u'{} 上有关联数据'.format(link))
            else:
                if not manager.count():
                    continue
                try:
                    manager.model._meta.get_field('is_active')
                    manager.filter(is_active=True).update(is_active=False)
                except FieldDoesNotExist as ex:
                    # 理论上，级联删除的model上面应该也有is_active字段，否则代码逻辑应该有问题
                    logger.warn(ex)
                    raise ModelDontHaveIsActiveFiled(
                        '{}.{} 没有is_active字段, 请检查程序逻辑'.format(
                            manager.model.__module__,
                            manager.model.__class__.__name__
                        ))
        instance.is_active = False
        instance.save()

    def get_queryset(self):
        return self.queryset.filter(is_active=True)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    # max_page_size = 1000


class IsAuthenticatedOrCreate(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        if request.method == 'POST':
            return True
        return super(IsAuthenticatedOrCreate, self).has_permission(request, view)


class SignUp(generics.CreateAPIView):
    queryset = AbstractUser.objects.all()
    serializer_class = SignUpSerializer
    # permission_classes = IsAuthenticatedOrCreate


class Login(generics.ListAPIView):
    queryset = AbstractUser.objects.all()
    serializer_class = LoginSerializer
    authentication_classes = (AllowAny,)


class SignIn(views.APIView):
    permission_classes = (AllowAny,)

    # serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        if 'username' not in request.data:
            msg = 'Username required'
            raise AuthenticationFailed(msg)
        elif 'password' not in request.data:
            msg = 'Password required'
            raise AuthenticationFailed(msg)

        user = authenticate(username=request.data[
            'username'], password=request.data['password'])
        # print(user)

        if user is None or not user.is_active:
            raise AuthenticationFailed('Invalid username or password')
        serializer = LoginSerializer(instance=user)
        return Response(serializer.data, status=200)


class Store_IndustryViewSet(ModelViewSet):
    queryset = Store_Industry.objects.all()
    serializer_class = Store_IndustrySerializer


class Store_CateringViewSet(ModelViewSet):
    queryset = Store_Catering.objects.all()
    serializer_class = Store_CateringSerializer


class Store_BusinessViewSet(ModelViewSet):
    queryset = Store_Business.objects.all()
    serializer_class = Store_BusinessSerializer


class Store_Business_TimeViewSet(ModelViewSet):
    queryset = Store_Business_Time.objects.all()
    serializer_class = Store_Business_TimeSerializer


class Store_Business_Time_FreeDayViewSet(ModelViewSet):
    queryset = Store_Business_Time_FreeDay.objects.all()
    serializer_class = Store_Business_Time_FreeDaySerializer


class Store_LicenseViewSet(ModelViewSet):
    queryset = Store_License.objects.all()
    serializer_class = Store_LicenseSerializer


class Store_AuthViewSet(ModelViewSet):
    queryset = Store_Auth.objects.all()
    serializer_class = Store_AuthSerializer


class Store_Food_SafetyViewSet(ModelViewSet):
    queryset = Store_Food_Safety.objects.all()
    serializer_class = Store_Food_SafetySerializer


class StoresViewSet(ModelViewSet):
    queryset = Stores.objects.all()
    serializer_class = StoresSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return StoresSerializer
        if self.action == 'retrieve':
            return StoreDetailSerializer
        return StoresSerializer

    @list_route(methods=['get'])
    def get_kitchen(self, request):
        store = request.GET.get('store', 0)
        kitchen = Kitchen.objects.filter(store_id=store)
        return Response(KitchenSerializer(kitchen, many=True).data)

    @list_route(methods=['get'])
    def get_meal_order(self, request):
        desk_no = request.GET.get('desk')
        meal = Meal.objects.filter(desk__number=desk_no, status=0).order_by('-created')

        return Response({'meal': MealOrderByDeskSerializer(meal, many=True).data})

    @list_route(methods=['get'])
    def index(self, request):
        try:
            ret = Stores.objects.get(id=request.GET.get('store'))
        except Stores.DoesNotExist:
            return Response(status=404)
        return Response(StoreIndexSerializer(instance=ret, context={'request': request}).data)


class Store_RotationViewSet(ModelViewSet):
    queryset = Store_Rotation.objects.all()
    serializer_class = Store_RotationSerializer
    filter_fields = ('store',)


class Store_ImageViewSet(ModelViewSet):
    queryset = Store_Image.objects.all()
    serializer_class = Store_ImageSerializer
    filter_fields = ('store',)


class Store_LobbyViewSet(ModelViewSet):
    queryset = Store_Lobby.objects.all()
    serializer_class = Store_LobbySerializer
    filter_fields = ('store',)


class Store_KitchenViewSet(ModelViewSet):
    queryset = Store_Kitchen.objects.all()
    serializer_class = Store_KitchenSerializer
    filter_fields = ('store',)


class Store_OtherViewSet(ModelViewSet):
    queryset = Store_Other.objects.all()
    serializer_class = Store_OtherSerializer
    filter_fields = ('store',)


class Store_AdViewSet(ModelViewSet):
    queryset = Store_Ad.objects.all()
    serializer_class = Store_AdSerializer
    filter_fields = ('store',)


class AbstractUserViewSet(ModelViewSet):
    queryset = AbstractUser.objects.all()
    serializer_class = UserSerializer

    @list_route(methods=['post'])
    def robot(self, request):
        params = request.data.get('text', None)
        username = params.replace('token ', '')
        try:
            user = AbstractUser.objects.get(username=username)
            token = AccessToken.objects.filter(user_id=user.id).order_by('-expires')
            if token.exists():
                token = token.first().token
            else:
                response = {"text": "**该用户没有token**"}
                return Response(response)
        except AbstractUser.DoesNotExist:
            response = {"text": "**未找到用户**"}
            return Response(response)
        response = {
            "text": 'Token: `{0}`'.format(token),
            "attachments": [
                {
                    # "title": "Meal：[点击查看](http://114.115.157.120:8002/api/v1.0/meal/{0}/)".format(order.meal_id),
                    "color": "#666666",
                    "text": "",
                }
            ]
        }
        return Response(response)

    @list_route(methods=['post'])
    def set_easemob_user(self, request):
        """
        设置环信接收用户
        :param request:
        :return:
        """
        user_id = request.data.get('user_id')
        user = AbstractUser.objects.get(id=user_id)
        AbstractUser.objects.filter(store_id=user.store_id).update(is_basemob=False)
        user.is_basemob = True
        user.save()
        return Response({'success': True})

    @list_route(methods=['get'])
    def me(self, request):

        if request.user.is_authenticated():
            serializer = self.get_serializer(instance=request.user)
            return Response(serializer.data)
        else:
            raise Error(err_code="400", err_message="Params error", message=u'未登录',
                        status_code=status.HTTP_306_RESERVED)


class FoodCategoryViewSet(ModelViewSet):
    queryset = FoodCategory.objects.filter(is_display=True)
    serializer_class = FoodCategorySerializer
    filter_fields = ('store',)


class KitchenViewSet(ModelViewSet):
    queryset = Kitchen.objects.all()
    serializer_class = KitchenSerializer


class TaxViewSet(ModelViewSet):
    queryset = Tax.objects.all()
    serializer_class = TaxSerializer


class SellPeriodViewSet(ModelViewSet):
    queryset = SellPeriod.objects.all()
    serializer_class = SellPeriodSerializer


class FoodImageViewSet(ModelViewSet):
    queryset = FoodImage.objects.all()
    serializer_class = FoodImageSerializer


class TagCategoryViewSet(ModelViewSet):
    queryset = TagCategory.objects.all()
    serializer_class = TagCategorySerializer


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class FoodUnitViewSet(ModelViewSet):
    queryset = FoodUnit.objects.all()
    serializer_class = FoodUnitSerializer


class FoodViewSet(ModelViewSet):
    # now = pytz.timezone("Asia/Shanghai").localize(datetime.now())
    pytz = pytz.timezone("Asia/Shanghai")
    now = pytz.localize(datetime.now())
    queryset = Food.objects.filter(Q(Q(Q(sellperiod_food__begin__lt=now) &
                                       Q(sellperiod_food__end__gt=now))
                                     & Q(sell_time=1)) | Q(sell_time=0))
    serializer_class = FoodSerializer
    pagination_class = StandardResultsSetPagination
    paginate_by = 15
    filter_fields = ('store', 'category')
    search_fields = ('name',)

    def get_queryset(self):
        self.queryset = self.queryset.filter(is_enable=True).exclude(
            category__in=FoodCategory.objects.filter(is_gift=True))
        now = pytz.timezone("Asia/Shanghai").localize(datetime.now())
        if now.weekday() == 1:
            return self.queryset.filter(Q(Q(monday=True) & Q(sell_time=1)) | Q(sell_time=0))
        elif now.weekday() == 2:
            return self.queryset.filter(Q(Q(tuesday=True) & Q(sell_time=1)) | Q(sell_time=0))
        elif now.weekday() == 3:
            return self.queryset.filter(Q(Q(wednesday=True) & Q(sell_time=1)) | Q(sell_time=0))
        elif now.weekday() == 4:
            return self.queryset.filter(Q(Q(thursday=True) & Q(sell_time=1)) | Q(sell_time=0))
        elif now.weekday() == 5:
            return self.queryset.filter(Q(Q(friday=True) & Q(sell_time=1)) | Q(sell_time=0))
        elif now.weekday() == 6:
            return self.queryset.filter(Q(Q(saturday=True) & Q(sell_time=1)) | Q(sell_time=0))
        elif now.weekday() == 7:
            return self.queryset.filter(Q(Q(sunday=True) & Q(sell_time=1)) | Q(sell_time=0))

        return self.queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return FoodSerializer
        if self.action == 'retrieve':
            return FoodDetailSerializer
        return FoodSerializer

    def get_serializer_context(self):
        return {'request': self.request}


class FoodSpecViewSet(ModelViewSet):
    """
    商品售卖时间
    """
    queryset = FoodSpec.objects.all()
    serializer_class = FoodSpecSerializer

    @list_route(methods=['post'])
    def food_stock_over(self, request):
        try:
            food_spec_id = request.POST.get('food_spec')
            FoodSpec.objects.filter(id=food_spec_id).update(stock=0)
            return Response({'success': True})
        except:
            raise Error(err_code="400", err_message="Food not found", message=u'商品未找到',
                        status_code=status.HTTP_400_BAD_REQUEST)


class DeskCategoryViewSet(ModelViewSet):
    """
    桌位类型音频
    """
    queryset = DeskCategory.objects.all()
    serializer_class = DeskCategorySerializer

    filter_fields = ('store',)


class DeskViewSet(ModelViewSet):
    """
    桌位音频
    """
    queryset = Desk.objects.all()
    serializer_class = DeskSerializer
    filter_fields = ('id', 'number', 'display_number', 'category', 'store')
    search_fields = ('number', 'display_number')

    @list_route(methods=['get'])
    def is_use(self, request):
        meal = Meal.objects.filter(desk_id=request.GET.get('desk'), status=0)
        return Response({'is_use': True}) if meal.count() > 0 else Response({'is_use': False})


class FoodCountViewSet(ModelViewSet):
    """
    商品数量音频
    """
    queryset = FoodCount.objects.all()
    serializer_class = FoodCountSerializer


class FoodAudioViewSet(ModelViewSet):
    """
    商品音频
    """
    queryset = FoodAudio.objects.all()
    serializer_class = FoodAudioSerializer


class TagAudioViewSet(ModelViewSet):
    """
    标签音频
    """
    queryset = TagAudio.objects.all()
    serializer_class = TagAudioSerializer


class CountAudioViewSet(ModelViewSet):
    """
    数量音频
    """
    queryset = CountAudio.objects.all()
    serializer_class = CountAudioSerializer


class UnitAudioViewSet(ModelViewSet):
    """
    单位音频
    """
    queryset = UnitAudio.objects.all()
    serializer_class = UnitAudioSerializer


class DeskAudioViewSet(ModelViewSet):
    """
    餐桌音频
    """
    queryset = DeskAudio.objects.all()
    serializer_class = DeskAudioSerializer


class StoreCategoryViewSet(ModelViewSet):
    """
    店铺类型
    """
    queryset = StoreCategory.objects.all()
    serializer_class = StoreCategorySerializer


class Store_FavoriteViewSet(ModelViewSet):
    """
    收藏
    """
    queryset = Store_Favorite.objects.all()
    serializer_class = Store_FavoriteSerializer
    pagination_class = StandardResultsSetPagination
    paginate_by = 15
    filter_fields = ('user',)
    ordering_fields = ('id',)
    search_fields = ('store__name',)

    def create(self, request):
        if request.user is not None:
            if Store_Favorite.objects.filter(user=self.request.user, store_id=request.data['store_id']).exists():
                return Response({'success': True})
            favorite = Store_Favorite(user=self.request.user, store_id=request.data['store_id'])
            favorite.save()
            return Response({'success': True})


class ReserveViewSet(ModelViewSet):
    """
    预约
    """
    queryset = Reserve.objects.all()
    serializer_class = ReserveReturnSerializer
    pagination_class = StandardResultsSetPagination
    paginate_by = 15
    filter_fields = ('user',)

    def get_serializer_class(self):
        if self.action == 'create':
            return ReserveSerializer
        return ReserveReturnSerializer

    @list_route(methods=['post'])
    def cancel(self, request):
        """
        取消预约
        

        """
        Reserve.objects.filter(id=request.data['id']).update(status=3)
        return Response({'success': True})

    def destroy(self, request, *args, **kwargs):
        """
        DELETE
        """
        super(ReserveViewSet, self).destroy(self, request, *args, **kwargs)
        return Response({'success': True})

    def create(self, request, *args, **kwargs):
        """
        CREATE
        """
        from django.utils.dateparse import parse_datetime

        # tz_utc_8 = timezone(timedelta(hours=8))
        datetime = pytz.timezone("Asia/Shanghai").localize(parse_datetime(request.data['datetime']))
        # print(parse_datetime(request.data['datetime']).astimezone(tz="Asia/Shanghai"))
        # print(parse_datetime(request.data['datetime']).replace(tzinfo=tz_utc_8))
        # datetime = timezone(settings.TIME_ZONE).localize(datetime.strptime(request.data['datetime'],'%Y-%m-%d %H:%M'))
        # print(parse_datetime('2017-05-25 12:00').replace(tzinfo=timezone("Asia/Shanghai")))

        result = StoreUnReserve.objects.filter(store=request.data['store'], begin__lt=datetime,
                                               end__gt=datetime)
        if result.exists():
            return Response({'success': False, 'message': '该时间门店不可预约',
                             'stoppingreserve': StoreUnReserveSerializer(result, many=True).data})
        else:
            result = Reserve.objects.create(num=request.data['num'], desk_category_id=request.data['desk_category'],
                                            datetime=datetime, tel=request.data['tel'], store_id=request.data['store'],
                                            user_id=request.data['user'], name=request.data['name'])
            return Response(ReserveSerializer(result).data, status=status.HTTP_201_CREATED)


class CouponCodeViewSet(ModelViewSet):
    """
    优惠券代码
    """
    queryset = CouponCode.objects.all()
    serializer_class = CouponCodeSerializer
    filter_fields = ('receive_user',)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE
        """
        super(CouponCodeViewSet, self).destroy(self, request, *args, **kwargs)
        return Response({'success': True})


class CouponViewSet(ModelViewSet):
    """
    优惠券接口
    """
    # datetime = pytz.timezone("Asia/Shanghai").localize(datetime.now())
    pytz = pytz.timezone("Asia/Shanghai")
    now = pytz.localize(datetime.now())
    queryset = Coupon.objects.filter(start_show__lt=now, end__gt=now, status=0).order_by('-created')

    serializer_class = CouponSerializer
    filter_fields = ('store',)

    def get_serializer_context(self):
        return {'request': self.request}

    @list_route(methods=['get'])
    def my_coupon(self, request):
        """
        CESHI
        :param request: 
        :return: 
        """
        if request.user.is_authenticated():
            datetime.now().utcnow()

            if 'store' in request.GET:
                coupon_code = CouponCode.objects.filter(Q(Q(coupon__store_id=request.GET.get('store')) &
                                                          Q(receive_user=request.user)))
                coupon_code = coupon_code.filter(pay_coupon__isnull=True,
                                                 coupon__end__gt=timezone.now()).distinct()
                coupon = Coupon.objects.filter(store_id=request.GET.get('store'), is_receive=False,
                                               end__gt=timezone.now()).distinct()
            else:
                coupon_code = CouponCode.objects.filter(receive_user=request.user,
                                                        pay_coupon__isnull=True,
                                                        coupon__end__gt=timezone.now())
                coupon = None  # Coupon.objects.filter(is_receive=False, end__gt=timezone.now()).distinct()

            # 去除限制
            result = []
            if coupon is not None:
                for c in coupon:
                    p = PayInfo.objects.filter(user=request.user, coupon=c, created__year=timezone.now().year,
                                               created__month=timezone.now().month, created__day=timezone.now().day)
                    if p.count() >= c.daily_limit:
                        continue
                    p = PayInfo.objects.filter(user=request.user, coupon=c)
                    if p.count() >= c.single_limit:
                        continue
                    result.append(c)

            result_code = []
            for c in coupon_code:
                p = PayInfo.objects.filter(user=request.user, coupon_code__coupon=c.coupon,
                                           created__year=timezone.now().year,
                                           created__month=timezone.now().month, created__day=timezone.now().day)
                if p.count() >= c.coupon.daily_limit:
                    continue
                p = PayInfo.objects.filter(user=request.user, coupon_code__coupon=c.coupon)
                if p.count() >= c.coupon.single_limit:
                    continue
                result_code.append(c)
            return Response({'coupon_code': CouponCodeSerializer(result_code, many=True,
                                                                 context={'request': request}).data,
                             'coupon': CouponSerializer(result, many=True, context={'request': request}).data})
        else:
            raise Error(err_code="401", err_message="Token error", message=u'未登录',
                        status_code=status.HTTP_401_UNAUTHORIZED)

    @list_route(methods=['post'])
    def receive(self, request):
        """
        领取优惠券
        必要：用户token
        POST参数：
        coupon - coupon主键 
        """
        if request.user.is_authenticated():
            coupon = Coupon.objects.get(id=request.data['coupon'])
            receive_count = CouponCode.objects.filter(coupon=coupon, receive_time__year=datetime.now().year,
                                                      receive_time__month=datetime.now().month,
                                                      receive_time__day=datetime.now().day,
                                                      receive_user=request.user).count()

            if coupon.daily_limit is not None and receive_count >= coupon.daily_limit:
                return Response({'success': False, 'message': '超过每人每日限额'})
            receive_count = CouponCode.objects.filter(coupon=coupon, receive_user=request.user).count()
            if coupon.single_limit is not None and receive_count >= coupon.single_limit:
                return Response({'success': False, 'message': '超过单人限额'})
            if CouponCode.objects.filter(coupon=coupon).count() >= coupon.count:
                return Response({'success': False, 'message': '优惠券已全部发放'})
            code = get_random_string(length=9, allowed_chars='0123456789')
            coupon_code = CouponCode(code=code, coupon_id=request.data['coupon'], receive_user=request.user,
                                     is_receive=True)
            coupon_code.save()
            return Response({'success': True, 'code': coupon_code.code})
        else:
            raise Error(err_code="401", err_message="Token error", message=u'未登录',
                        status_code=status.HTTP_401_UNAUTHORIZED)


class MealViewSet(UnActiveModelMixin, ModelViewSet):
    queryset = Meal.objects.all().order_by('-created')
    serializer_class = MealSerializer
    filter_fields = ('user', 'status', 'desk')
    search_fields = ('store__name', 'order_meal__order_food__food__name')
    pagination_class = StandardResultsSetPagination
    paginate_by = 15

    def get_serializer_context(self):
        return {'request': self.request}

    @list_route(methods=['post'])
    @is_login
    def get_all_meal_by_user(self, request):
        return Response(MealByUserSerializer(Meal.objects.filter(user=request.user,status=0), many=True).data)

    @detail_route(methods=['get'])
    def get_user_name(self, request, pk):
        meal = Meal.objects.get(id=pk)
        return Response({'user':list(meal.user.all().values('username'))})

    @list_route(methods=['post'])
    @is_login
    def modify_rash_status(self, request):
        """
        将支付状态由现金未支付改为现金已支付并离座
        :param request:
        :return:
        """
        if request.user.user_type == 0:
            raise Error(err_code="401", err_message="Permission error", message=u'无权限',
                        status_code=status.HTTP_401_UNAUTHORIZED)

        meal_id = request.data.get('meal_id', None)
        if meal_id is None:
            raise Error(err_code="401", err_message="Meal not found", message=u'Meal 未找到',
                        status_code=status.HTTP_400_BAD_REQUEST)
        meal = Meal.objects.get(id=meal_id)
        order_list = Order.objects.filter(meal=meal)
        for order in order_list:
            if order.status == 1:
                order.status = 2
                order.save()

                # total_price = sum([f.price + f.tax_value for f in Order_Food.objects.filter(order=order)])
                # payinfo = PayInfo(
                #     order=order,
                #     user=request.user,
                #     pay_type=1,
                #     money=total_price,
                #     money_pay=total_price,
                #     tax=order.tax_value
                # )
                # payinfo.save()
        unpay = order_list.filter(status=0, order_food__isnull=False).count()
        if unpay == 0:
            meal.status = 1
            meal.save()
        return Response({'success': True, 'meal_status': meal.status})

    @list_route(methods=['get'])
    def get_user_info(self, request):
        meal_id = request.GET.get('meal_id')
        payinfo = PayInfo.objects.filter(order__meal__id=meal_id).order_by('-created')
        if payinfo.exists():
            payinfo = payinfo.first()
            return Response(
                {'easemob_id': payinfo.user.username, 'fullname': payinfo.user.fullname,
                 'img': request.build_absolute_uri(payinfo.user.img.url) if payinfo.user.img.name != '' else None})
        meal = Meal.objects.filter(id=meal_id)
        user = meal.first().user.first()
        return Response({'easemob_id': user.username, 'fullname': user.fullname,
                         'img': request.build_absolute_uri(user.img.url) if user.img.name != '' else None})

    @list_route(methods=['post'])
    @meal_check
    def add_user(self, request):
        user = request.POST.get('user')
        meal = request.POST.get('meal')
        obj = Meal.objects.get(id=meal)
        obj.total_user = user
        obj.save()
        return Response({'success': True})

    @list_route(methods=['get'])
    def get_last_meal(self, request):
        if not request.user.is_authenticated():
            raise Error(err_code="401", err_message="Token error", message=u'未登录',
                        status_code=status.HTTP_401_UNAUTHORIZED)
        ret = Meal.objects.filter(user__in=[request.user.id, ], status=0) \
            .annotate(count=Count('order_meal')).order_by('-created') \
            .filter(count=Order.objects.filter(status__lt=0, meal_id=F('id')).count()).first()
        if ret is None:
            return Response({'store_name': None, 'meal_id': None})
        return Response({'store_name': ret.store.name, 'meal_id': ret.id})

    @list_route(methods=['get'])
    def get_meal_user_count(self, request):
        try:
            if 'meal' in request.GET:
                return Meal.objects.get(id=request.GET.get('meal')).user.count()
            else:
                raise Error(err_code="400", err_message="Meal error", message=u'用餐信息错误',
                            status_code=status.HTTP_400_BAD_REQUEST)
        except:
            raise Error(err_code="400", err_message="Meal error", message=u'用餐信息错误',
                        status_code=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['get'])
    def my_meal(self, request):
        if request.user.is_authenticated():
            queryset = self.filter_queryset(
                self.get_queryset().filter(user=request.user, status=1).order_by('-created'))
            for q in queryset:
                p = PayInfo.objects.filter(order__meal__id=q.id).count()
                if p == 0:
                    queryset._result_cache.remove(q)
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = MyMealSerializer(page, context={"request": request}, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = MyMealSerializer(queryset, context={"request": request}, many=True)

            return Response(serializer.data)
        else:
            raise Error(err_code="401", err_message="Token error", message=u'未登录',
                        status_code=status.HTTP_401_UNAUTHORIZED)

    @list_route(methods=['post'])
    def start_meal(self, request):
        """
        流程:
        +-----------+      +------------+       +------------------+        +----------------+
        |           | Yes  |            |  Yes  |                  |        |                |
        |   Login?  +----->+ Have meal? +------>+ Add user to meal +------->+ Return message |
        |           |      |            |       |                  |        |                |
        +-----+-----+      +-----+------+       +------------------+        +-------+--------+
              |                  |                                                 ^
              |No                |No                                               |
              |                  |                                                 |
              v                  v                                                 |
        +-----+-----+      +-----+------+       +------------------+        +-------+--------+
        |           |      |            |       |                  |        |                |
        | Return 401|      |Create meal +------>+ Add user to meal +------->+  Create order  |
        |           |      |            |       |                  |        |                |
        +-----------+      +------------+       +------------------+        +----------------+
        
        1.是否登录,登录，跳到2，未登录跳到4
        2.是否有用餐信息，有跳到3，无用餐信息跳到5
        3.添加用户到用餐信息中，返回信息
        4.返回401
        5.创建用餐信息 ==> 添加当前用户到用餐信息 ==> 创建订单 ==> 返回信息
        """
        if request.user.is_authenticated():
            spell = request.POST.get('spell')
            try:
                if spell.lower() == 'true':
                    raise Meal.DoesNotExist()
                result = Meal.objects.filter(desk_id=request.POST.get('desk'), store_id=request.POST.get('store'),
                                             status=0, is_active=True).order_by('created').first()
                if result is not None:
                    user_add = AbstractUser.objects.get(id=request.POST.get('user'))
                    result.user.add(user_add)
                    order = Order.objects.filter(meal=result).order_by('created').last()

                    return Response(
                        {'success': True, 'meal_id': result.id, 'meal_code': result.code, 'order_id': order.id})
                else:
                    raise Meal.DoesNotExist()
            except Meal.DoesNotExist:
                meal = Meal(desk_id=request.POST.get('desk'), store_id=request.POST.get('store'), is_active=True)
                meal.save()
                user = AbstractUser.objects.get(id=request.POST.get('user'))
                meal.user.add(user)

                order = Order(meal=meal)
                order.save()
                r = auto_meal_leave.apply_async((meal.id,), eta=datetime.utcnow() + timedelta(minutes=5))
                return Response({'success': True, 'meal_id': meal.id, 'meal_code': meal.code, 'order_id': order.id})
        else:
            raise Error(err_code="401", err_message="Token error", message=u'未登录',
                        status_code=status.HTTP_401_UNAUTHORIZED)

    @list_route(methods=['post'])
    def force_end_meal(self, request):
        if not request.user.is_authenticated():
            raise Error(err_code=errors.NOT_LOGIN, err_message='Not login', message='未登录',
                        status_code=status.HTTP_401_UNAUTHORIZED)

        if request.user.user_type < 1:
            raise Error(err_code=errors.NOT_LOGIN, err_message='没有权限', message='没有权限',
                        status_code=status.HTTP_401_UNAUTHORIZED)

        meal_id = request.POST.get('id')
        if meal_id is None:
            raise Error(err_code=errors.BAD_PARAMS, err_message='meal_id', message='meal id不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)
        Meal.objects.filter(id=meal_id).update(status=1)
        Order.objects.filter(meal_id=meal_id, status__lte=1).update(status=9)
        return Response({'success': True})

    @list_route(methods=['post'])
    def end_meal(self, request):
        """
        流程:
         +-----------+        +----------------+     +---------------------------+
         |           |  Yes   |                | Yes |                           |
         |  Login?   +--------> Meal is exist? +-----> Order in meal is all pay? |
         |           |        |                |     |                           |
         +-----+-----+        +-------+--------+     +-------------+-------------+
               |                      |                            |
               | No                   | No                         | No
               v                      v                            v
         +-----------+        +----------------+     +---------------------------+
         |           |        |                |     |                           |
         | Throw 401 |        |   Throw 404    |     | Modify meal status to over|
         |           |        |                |     |                           |
         +-----------+        +----------------+     +-------------+-------------+
                                                                   |
                                                                   | 
                                                                   v
                                                     +---------------------------+
                                                     |                           |
                                                     |      Return true          |
                                                     |                           |
                                                     +---------------------------+
        
        
        1. 是否登录，登录跳到2，未登录跳到5
        2. 用餐信息是否存在，存在跳到3，没有用餐信息跳到6
        3. 所有订单是否支付，已支付跳到4，跳到7
        4. 更改用餐信息状态为用餐结束，返回成功
        5. 返回401
        6. 返回404
        7. 返回2001
        """
        if request.user.is_authenticated():
            try:
                meal = Meal.objects.get(id=request.POST.get('meal'))
            except Meal.DoesNotExist:
                raise Error(err_code='404', err_message='Not found', message=u'用餐信息不存在',
                            status_code=status.HTTP_404_NOT_FOUND)
            Order.objects.filter(meal=meal, order_food__isnull=True).update(status=9)
            if meal.order_meal.count() == Order.objects.filter(meal=meal, status__gt=0).count():
                meal.status = 1
                meal.save()
                return Response({'success': True})
            else:
                raise Error(err_code=errors.NOT_PAY, err_message='Meal is not pay', message='用餐中的订单没有全部支付',
                            status_code=status.HTTP_403_FORBIDDEN)
        else:
            raise Error(err_code=errors.NOT_LOGIN, err_message='Not login', message='未登录',
                        status_code=status.HTTP_401_UNAUTHORIZED)


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_fields = ('meal',)
    search_fields = ('meal__desk__number', 'code')
    pagination_class = StandardResultsSetPagination
    paginate_by = 15

    @list_route(methods=['post'])
    def robot(self, request):
        params = request.data.get('text', None)
        order = params.replace('order ', '')

        try:
            if order == 'last':
                order = Order.objects.all().order_by('-created').first()
            else:
                order = Order.objects.get(id=order)
        except Order.DoesNotExist:
            response = {"text": "**未找到订单**"}
            return Response(response)
        response = {
            "text": "订单ID: `{0}` \n 订单编号:`{1}` \n 总价格:`{2}` \n VIP总价:`{3}` \n "
                    "创建时间:`{4}` \n 当前状态:`{5}` \n 总税:`{6}` \n VIP总税:`{7}` \n "
                    "Meal：[点击查看](http://114.115.157.120:8002/api/v1.0/meal/{8}/)".format(order.id, order.code,
                                                                                         order.total_price,
                                                                                         order.total_vip_price,
                                                                                         order.created,
                                                                                         order.get_status_display(),
                                                                                         order.tax_value,
                                                                                         order.vip_tax_value,
                                                                                         order.meal_id),
            "attachments": [
                {
                    # "title": "Meal：[点击查看](http://114.115.157.120:8002/api/v1.0/meal/{0}/)".format(order.meal_id),
                    "color": "#666666",
                    "text": "",
                }
            ]
        }
        return Response(response)

    @list_route(methods=['post'])
    def clear_order_food(self, request):
        if request.user.is_authenticated():
            order = request.POST.get('order')
            Order_Food.objects.filter(order_id=order).delete()
            return Response({'success': True})
        else:
            raise Error(err_code="401", err_message="Token error", message=u'未登录',
                        status_code=status.HTTP_401_UNAUTHORIZED)

    @list_route(methods=['get'])
    def get_order_in_meal_kitchen(self, request):
        if request.user.is_authenticated() and request.user.user_type > 0:
            queryset = Meal.objects.filter(order_meal__status__range=(1, 8),
                                           status=0,
                                           created__range=(timezone.now() + timedelta(hours=-8), timezone.now()),
                                           store_id=request.user.store_id).distinct().order_by('-created')
            # queryset = Order.objects.filter(status__gte=1,
            #                                 created__range=(timezone.now() + timedelta(hours=-8), timezone.now()),
            #                                 meal__store_id=request.user.store_id)
            if 'search' in request.GET:
                queryset = queryset.filter(Q(code__endswith=request.GET.get('search')) |
                                           Q(desk__display_number__contains=request.GET.get('search')))

            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = OrderInMealSerializer(page, context={"request": request}, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = OrderInMealSerializer(queryset, context={"request": request}, many=True)

            return Response(serializer.data)
        else:
            raise Error(err_code="401", err_message="Token error", message=u'未登录',
                        status_code=status.HTTP_401_UNAUTHORIZED)

    @list_route(methods=['get'])
    def get_order_kitchen(self, request):
        # return Response({'user':request.user.is_authenticated(),'type':request.user.user_type})
        if (request.user.is_authenticated() and request.user.user_type == 0) or not request.user.is_authenticated():
            raise Error(err_code="401", err_message="Token error", message=u'账户错误',
                        status_code=status.HTTP_401_UNAUTHORIZED)
        return Response({'obj': KitChenOrderSerializer(Food.objects.first(), context={'request': request}).data})

    @list_route(methods=['get'])
    def get_food_num(self, request):
        ret = Order_Food.objects.values('order').filter(order_id=request.GET.get('id')).annotate(count=Sum('num'))
        result = 0
        for r in ret:
            result += r['count']
        return Response({'success': True, 'num': result})

    @meal_check
    def create(self, request, *args, **kwargs):

        order = Order(meal_id=request.meal.id)
        order.save()
        return Response({'success': True, 'order': OrderSerializer(order).data})

    @list_route(methods=['post'])
    def clean(self, request):
        order = request.POST.get('order')
        Order_Food.objects.filter(order_id=order).delete()
        return Response({'success': True})

    @list_route(methods=['get'])
    def get_order_by_store(self, request):
        store = request.GET.get('store')
        if store is not None:
            # TODO:添加条件，当天营业时间数据
            queryset = Meal.objects.filter(store_id=store, status=1,
                                           order_meal__order_food__isnull=False,
                                           order_meal__order_pay__isnull=False).order_by(
                '-created').distinct()

            if 'search' in request.GET:
                queryset = queryset.filter(Q(desk__display_number__endswith=request.GET.get('search')) |
                                           Q(code__endswith=request.GET.get('search')))

            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = MealOrderByStoreSerializer(page, context={"request": request}, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = MealOrderByStoreSerializer(queryset, context={"request": request}, many=True)

            return Response(serializer.data)
        else:
            raise Error(err_code=1010, err_message='Store is not exist.',
                        message='Store参数错误', status_code=status.HTTP_400_BAD_REQUEST)


class OrderFoodViewSet(ModelViewSet):
    queryset = Order_Food.objects.all()
    serializer_class = OrderFoodSerializer
    filter_fields = ('order',)

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderFoodCreateSerializer
        else:
            return OrderFoodSerializer

    def create(self, request, *args, **kwargs):
        # if request.user is not None:
        orderfood = Order_Food(order_id=request.POST.get('order'), food_id=request.POST.get('food'),
                               food_spec_id=request.POST.get('food_spec'), num=request.POST.get('num'),
                               price=request.POST.get('price'))
        orderfood.save()
        if 'tag' in request.POST:
            tags = request.POST.get('tag')
            tags = tags.split(',')
            for tag in tags:
                orderfood.tag.add(Tag.objects.get(id=tag))
        return Response({'success': True}, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE
        """
        instance = self.get_object()
        if instance.order.status > 0:
            raise Error(err_code=errors.NOT_PAY, err_message='Order is payed', message='订单已支付，不能删除及更改',
                        status_code=status.HTTP_400_BAD_REQUEST)
        super(OrderFoodViewSet, self).destroy(self, request, *args, **kwargs)
        return Response({'success': True})

    @list_route(methods=['post'])
    def add_cart_by_id(self, request):
        order_food_id = request.POST.get('id')
        num = request.POST.get('num')
        if order_food_id is None:
            raise Error(err_code=1012, err_message='ID is not exist.', message='ID不存在',
                        status_code=status.HTTP_400_BAD_REQUEST)

        ret = Order_Food.objects.filter(id=order_food_id)  # .update(num=F('num') + num)
        if ret.first().order.meal.status == 1:
            raise Error(err_code="401", err_message="Meal error", message=u'Meal 已离座',
                        status_code=status.HTTP_401_UNAUTHORIZED)
        for r in ret:
            r.num += int(num)
            if r.num == 0:
                r.delete()
            else:
                r.save()
        return Response({'success': True})

    @list_route(methods=['post'])
    def add_cart(self, request):
        """
        添加购物车
        """

        serializer = AddCartSerializer(data=request.data)

        if serializer.is_valid():
            if int(serializer.initial_data['num']) < 0:
                order_food = Order_Food.objects.filter(order_id=serializer.initial_data['order'],
                                                       food_id=serializer.initial_data['food'],
                                                       food_spec_id=serializer.initial_data['food_spec']) \
                    .order_by('-created')
                if order_food.count() > 0:
                    order_food = order_food.first()
                    if order_food.num + int(serializer.initial_data['num']) <= 0:
                        ret = Order_Food.objects.filter(id=order_food.id)
                        ret.delete()
                        return Response({'success': True})
                    order_food.num += int(serializer.initial_data['num'])
                    order_food.save()
                    return Response({'success': True})
                return Response({'success': True})

            order_food = Order_Food.objects.filter(order_id=serializer.initial_data['order'],
                                                   food_id=serializer.initial_data['food'],
                                                   food_spec_id=serializer.initial_data['food_spec'])

            if 'tag' in serializer.initial_data:
                tags = serializer.initial_data['tag']
                tags = tags.split(',')
                order_food = order_food.annotate(tagcount=Count('tag')).filter(tagcount=len(tags))

                for tag in tags:
                    order_food = order_food.filter(tag=tag)
            if 'desc' in serializer.initial_data:
                order_food = order_food.filter(desc=serializer.initial_data['desc'])

            if order_food.count() > 0:

                if order_food.first().num + int(serializer.initial_data['num']) <= 0:
                    Order_Food.objects.filter(id=order_food.id).delete()
                    return Response({'success': True})
                order_food = order_food.first()
                order_food.num += int(serializer.initial_data['num'])
                order_food.save()
            else:
                order_food = Order_Food(order_id=serializer.initial_data['order'],
                                        food_id=serializer.initial_data['food'],
                                        food_spec_id=serializer.initial_data['food_spec'],
                                        num=serializer.initial_data['num'],
                                        price=serializer.initial_data['price'],
                                        )
                if 'desc' in serializer.initial_data:
                    order_food.desc = serializer.initial_data['desc']

                order_food.save()

                if 'tag' in serializer.initial_data:
                    tags = serializer.initial_data['tag']
                    tags = tags.split(',')

                    for tag in tags:
                        order_food.tag.add(Tag.objects.get(id=tag))

            return Response({'success': True})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'])
    def change_num(self, request):
        """
        修改食物数量
        """
        instance = Order.objects.get(id=request.POST.get('order'))
        if instance.status > 0:
            raise Error(err_code=errors.NOT_PAY, err_message='Order is payed', message='订单已支付，不能删除及更改',
                        status_code=status.HTTP_400_BAD_REQUEST)
        Order_Food.objects.filter(id=request.POST.get('food')).update(num=request.POST.get('num'))
        return Response({'success': True})


class RefundOrderViewSet(ModelViewSet):
    """
    退款信息
    """
    queryset = RefundOrder.objects.all()
    serializer_class = RefundOrderSerializer
    filter_fields = ('id', 'user', 'store')
    pagination_class = StandardResultsSetPagination
    paginate_by = 15

    def get_serializer_class(self):
        if self.action == 'list':
            return RefundOrderViewSerializer
        if self.action == 'retrieve':
            return RefundOrderDetailSerializer
        return RefundOrderSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    def add_months(self, sourcedate, months):
        add_month = timedelta(months * 365 / 12)
        return sourcedate + add_month

    @list_route(methods=['post'])
    def reject_refund(self, request):
        refund_id = request.POST.get('refund_id')
        refund_desc = request.POST.get('refund_desc')
        refund_order = RefundOrder.objects.get(id=refund_id)
        refund_order.status = 2
        refund_order.process_date = timezone.now()
        refund_order.refuse_desc = refund_desc
        refund_order.save()
        order = Order.objects.get(id=refund_order.order_id)
        order.status = 7
        order.save()
        return Response({'success': True})

    @list_route(methods=['post'])
    def agree_refund(self, request):
        refund_id = request.POST.get('refund_id')
        refund_order = RefundOrder.objects.get(id=refund_id)
        # 1.修改状态
        if refund_order.refund_type == 0:
            refund_order.status = 1
            refund_order.process_date = timezone.now()
            refund_order.save()
            order = Order.objects.get(id=refund_order.order_id)
            order.status = 6
            order.save()
        else:
            # 商品退款
            price = refund_order.refund_gold + refund_order.refund_point + refund_order.refund_cash
            Order_Food.objects.filter(id=refund_order.food_id).update(num=F('num') - refund_order.num,
                                                                      price=F('price') - price)

        # 2.优惠券返回
        if refund_order.refund_type == 0:
            pay_info = PayInfo.objects.filter(order_id=refund_order.order_id).first()
            coupon_code = CouponCode.objects.get(id=pay_info.coupon_code.id)
            coupon_code.is_use = False
            coupon_code.save()
        # 3.返回金币和会员点
        # 3.1 会员点退款
        point_id = StorePoint.objects.filter(store=refund_order.store_id)
        if point_id.exists():
            point_id = point_id.first().id
        else:
            raise Error(err_code="1007", err_message="Point error", message=u'门店会员点信息错误',
                        status_code=status.HTTP_400_BAD_REQUEST)

        current_point = StorePointLog.objects.filter(user_id=refund_order.user_id,
                                                     point_id=point_id).order_by('-created')
        if current_point.exists():
            current_point = current_point.first().current_point
        else:
            current_point = 0
        ret = StorePointLog(point_id=point_id, user_id=refund_order.user_id, recharge_point=-refund_order.refund_point,
                            pay_type=2)
        ret.current_point = int(current_point) + int(-refund_order.refund_point)
        store_point = StorePoint.objects.get(id=point_id)
        ret.end_date = self.add_months(timezone.now(), store_point.end_date)
        ret.save()
        # 3.2 金币退款
        current_gold = GoldLog.objects.filter(user_id=refund_order.user_id).order_by('-created')
        if current_gold.exists():
            current_gold = current_gold.first().current_gold
        else:
            current_gold = 0
        ret = GoldLog(user_id=refund_order.user_id, store_id=refund_order.store_id,
                      recharge_gold=-refund_order.refund_gold, pay_type=3)
        ret.current_gold = int(current_gold) + int(-refund_order.refund_gold)
        ret.save()
        return Response({'success': True})


class QueueLogViewSet(ModelViewSet):
    """
    排队信息
    """
    queryset = QueueLog.objects.all()
    serializer_class = QueueLogSerializer

    @list_route(methods=['get'])
    def get_current_num(self, request):
        store = request.GET.get('store')
        ret = QueueLog.objects.filter(store_id=store, queue__created__year=datetime.now().year,
                                      queue__created__month=datetime.now().month,
                                      queue__created__day=datetime.now().day).aggregate(Count('code'))
        return Response({'current': ret['code__count'] if ret['code__count'] else 0})

    def is_over(self, request):
        logid = request.GET.get('logid')
        ret = QueueLog.objects.filter(store_id=request.GET.get('store'), queue__created__year=datetime.now().year,
                                      queue__created__month=datetime.now().month,
                                      queue__created__day=datetime.now().day).aggregate(Max('code'))
        max = ret['code__max'] if ret['code__max'] is not None else 0

        log = QueueLog.objects.get(id=logid)
        if log.code <= max:
            return Response({'is_over': False})
        else:
            return Response({'is_over': True})

    def create(self, request, *args, **kwargs):
        # if request.user is not None:
        # desk_category_id=request.POST.get('desk_category')

        queue = Queue(store_id=request.POST.get('store'),
                      num=request.POST.get('num'), chindren_num=request.POST.get('chindren_num'),
                      no_smoking=request.POST.get('no_smoking'))
        if 'desk_category' in request.POST:
            queue.desk_category_id = request.POST.get('desk_category')
        queue.save()
        log = QueueLog(store_id=request.POST.get('store'), queue=queue)
        log.save()

        return Response({'success': True, 'id': log.id, 'code': log.code}, status=status.HTTP_201_CREATED)


class PayViewSet(ModelViewSet):
    queryset = PayInfo.objects.all()
    serializer_class = PayInfoSerializer
    order = None
    money = None
    point_pay = None
    gold_pay = None
    couponcode = None
    coupon_code = None
    store_id = None
    usergift = None
    tax = 0

    def add_months(self, sourcedate, months):
        month = sourcedate.month - 1 + months
        year = int(sourcedate.year + month / 12)
        month = month % 12 + 1
        day = min(sourcedate.day, calendar.monthrange(year, month)[1])
        return datetime.date(year, month, day)

    @list_route(methods=['post'])
    def robot(self, request):
        params = request.data.get('text', None)
        payinfo = params.replace('pay ', '')

        try:
            if payinfo == 'last':
                payinfo = PayInfo.objects.all().order_by('-created').first()
            else:
                payinfo = PayInfo.objects.get(order=payinfo)
        except PayInfo.DoesNotExist:
            response = {"text": "**未找到支付信息**"}
            return Response(response)
        response = {
            "text": "订单ID: `{0}` \n 支付用户:`{1}` \n 支付方式:`{2}` \n 优惠券代码:`{3}` \n "
                    "优惠券:`{4}` \n 支付金额:`{5}` \n 银行卡支付:`{6}` \n 支付宝支付:`{7}` \n "
                    "会员点支付:`{8}` \n 金币支付:`{9}` \n 现金支付:`{10}` \n 支付时间:`{11}` \n "
                    "支付编号:`{12}` \n 优惠金额:`{13}` \n 税:`{14}` \n "
                    "Order：[点击查看](http://114.115.157.120:8002/api/v1.0/order/{15}/)".format(payinfo.order.id,
                                                                                            payinfo.user.username,
                                                                                            payinfo.get_pay_type_display(),
                                                                                            payinfo.coupon_code.code if payinfo.coupon_code is not None else None,
                                                                                            payinfo.coupon.name if payinfo.coupon is not None else None,
                                                                                            payinfo.money,
                                                                                            payinfo.card_pay,
                                                                                            payinfo.alipay_pay,
                                                                                            payinfo.point_pay,
                                                                                            payinfo.gold_pay,
                                                                                            payinfo.money_pay,
                                                                                            payinfo.created,
                                                                                            payinfo.code,
                                                                                            payinfo.limit_price,
                                                                                            payinfo.tax,
                                                                                            payinfo.order.id),
            "attachments": [
                {
                    # "title": "Meal：[点击查看](http://114.115.157.120:8002/api/v1.0/meal/{0}/)".format(order.meal_id),
                    "color": "#666666",
                    "text": "",
                }
            ]
        }
        return Response(response)

    @list_route(methods=['get'])
    @is_login
    def get_current(self, request):
        """
        获取当前余额
        :param request:
        :return:
        """
        store = request.GET.get('store')
        point = StorePoint.objects.filter(store=store)
        ret = 0
        if point.exists():
            point = point.first()
            ret = StorePointLog.objects.filter(user_id=request.user.id, point=point).order_by('created')
            ret = ret.last().current_point if ret.exists() else 0
        # else:
        #     raise Error(err_code=1009, err_message='This store is not have point setting.',
        #                 message='该店铺没有设置会员点', status_code=status.HTTP_400_BAD_REQUEST)

        # if ret.exists():
        #     ret = ret.last().current_point
        # else:
        #     ret = 0x

        gold = GoldLog.objects.filter(user_id=request.user.id).order_by('created')
        # if gold.exists():
        #     gold = gold.last().current_gold
        # else:
        #     gold = 0
        gold = gold.last().current_gold if gold.exists() else 0

        pay_type = StorePayType.objects.get(store_id=store)

        return Response({'current_point': ret,
                         'current_gold': gold,
                         'cash': pay_type.cash,
                         'point': pay_type.point,
                         'gold': pay_type.gold,
                         'third_party': pay_type.third_party,
                         'alipay': pay_type.alipay})

    @list_route(methods=['post'])
    def recharge_store(self, request):
        """
        充值会员点
        :param request:
        :return:
        """
        if not request.user.is_authenticated():
            raise Error(err_code="401", err_message="Token error", message=u'未登录',
                        status_code=status.HTTP_401_UNAUTHORIZED)
        # 解密
        aes = AESCustom()
        point = aes.decrypt(request.POST.get('point'))
        user = aes.decrypt(request.POST.get('user'))
        recharge_point = aes.decrypt(request.POST.get('recharge_point'))
        pay_type = aes.decrypt(request.POST.get('pay_type'))
        current_point = StorePointLog.objects.filter(user_id=user, point_id=point).order_by('-created')
        if current_point.exists():
            current_point = current_point.first().current_point
        else:
            current_point = 0
        ret = StorePointLog(point_id=point, user_id=user, recharge_point=recharge_point, pay_type=pay_type)
        ret.current_point = int(current_point) + int(recharge_point)
        store_point = StorePoint.objects.get(id=point)
        ret.end_date = self.add_months(timezone.now(), store_point.end_date)
        ret.save()
        return Response(
            {'success': True, 'current_point': ret.current_point, 'end_date': timezone.now().strptime('%Y-%m-%d')})

    @list_route(methods=['post'])
    def recharge_gold(self, request):
        """
        充值金币
        :param request:
        :return:
        """
        if not request.user.is_authenticated():
            raise Error(err_code="401", err_message="Token error", message=u'未登录',
                        status_code=status.HTTP_401_UNAUTHORIZED)
        # 解密
        aes = AESCustom()
        user = aes.decrypt(request.POST.get('user'))
        recharge_gold = aes.decrypt(request.POST.get('recharge_gold'))
        pay_type = aes.decrypt(request.POST.get('pay_type'))
        store = aes.decrypt(request.POST.get('store'))
        current_gold = GoldLog.objects.filter(user_id=user).order_by('-created')
        if current_gold.exists():
            current_gold = current_gold.first().current_gold
        else:
            current_gold = 0
        ret = GoldLog(user_id=user, store_id=store, recharge_gold=recharge_gold, pay_type=pay_type)
        ret.current_gold = int(current_gold) + int(recharge_gold)
        ret.save()
        return Response({'success': True, 'current_point': ret.current_gold})

    def check_conpon(self, coupon):
        if coupon is None:
            self.couponcode = CouponCode.objects.get(code=self.couponcode)
            if self.couponcode.is_use or PayInfo.objects.filter(coupon_code=self.couponcode).exists():
                raise Error(err_code=errors.IS_USE, err_message='The coupon was used.', message='优惠券已使用',
                            status_code=status.HTTP_400_BAD_REQUEST)
            return self.couponcode.coupon
        return None

    def sum_total_price(self, order_food_list):
        totalprice = 0
        for order_food in order_food_list:
            if order_food.food_spec.stock >= order_food.num:
                if self.point_pay == self.money and order_food.vip_price > 0:
                    totalprice += order_food.vip_price if order_food.num > 0 else 0
                    totalprice += order_food.vip_tax_value
                    self.tax += order_food.vip_tax_value
                else:
                    totalprice += order_food.price if order_food.num > 0 else 0
                    totalprice += order_food.tax_value
                    self.tax += order_food.tax_value
            else:
                raise Error(err_code=errors.STOCK_IS_EMPTY, err_message='Some food stock is empty.',
                            message='{0}无库存'.format(order_food.food_spec), status_code=status.HTTP_400_BAD_REQUEST)
        return totalprice

    def get_point(self, order):
        """
        查询会员点信息
        :param order:
        :return:
        """
        store_id = Stores.objects.filter(meal_store__order_meal__id=order)
        if store_id.exists():
            store_id = store_id.first().id
        else:
            raise Error(err_code=1005, err_message='Order not found',
                        message='订单未找到:' + str(order), status_code=status.HTTP_400_BAD_REQUEST)
        point = StorePoint.objects.filter(store=store_id)
        if point.exists():
            return point.first()
        else:
            raise Error(err_code=1006, err_message='StorePoint not found',
                        message='会员点信息未找到', status_code=status.HTTP_400_BAD_REQUEST)

    def less_food_price(self, totalprice, order_food):
        """
        减去当前order_food金额
        :param point_pay:
        :param money:
        :param totalprice:
        :param order_food:
        :return:
        """
        if self.point_pay == self.money and order_food.vip_price > 0:
            totalprice -= order_food.vip_price
            totalprice -= order_food.vip_tax_value
            self.tax -= order_food.vip_tax_value
        else:
            totalprice -= order_food.price
            totalprice -= order_food.tax_value
            self.tax -= order_food.tax_value
        return totalprice

    def less_food_price_by_once(self, totalprice, order_food):
        """
        减去当前order_food金额
        :param point_pay:
        :param money:
        :param totalprice:
        :param order_food:
        :return:
        """
        if self.point_pay == self.money and order_food.food_spec.vip_price > 0:
            totalprice -= order_food.food_spec.vip_price
            totalprice -= order_food.food_spec.vip_tax_value
            self.tax -= order_food.food_spec.vip_tax_value
        else:
            totalprice -= order_food.food_spec.price
            totalprice -= order_food.food_spec.tax_value
            self.tax -= order_food.food_spec.tax_value
        return totalprice

    def add_food_price(self, totalprice, price, order_food, is_unite=False, discount=False):
        """
        添加订单中商品到总价中(含税)
        :param totalprice: 总价
        :param price: 单价
        :param order_food: order_food对象
        :return: 总价
        """

        tmp_price = price * order_food.num if not is_unite and not discount else price
        if not is_unite and not discount:
            tax = utils.TaxTool.tax(price, order_food.num, False,
                                    order_food.food.tax.tax)
            tmp_price += tax
            self.tax += tax
        elif discount:
            tax = utils.TaxTool.tax(price, 1, False,
                                    order_food.food.tax.tax)
            tmp_price += tax
            self.tax += tax
        elif is_unite:
            self.tax += utils.TaxTool.tax(price, 1, True,
                                          order_food.food.tax.tax)
            return totalprice + round(tmp_price, 0)
        else:
            self.tax += utils.TaxTool.tax(price, 1, True,
                                          order_food.food.tax.tax)
        return totalprice + round(tmp_price, 0)

    @list_route(methods=['post'])
    def pay(self, request):
        """
        支付
        :param request:
        :return:
        """
        # 判断登录
        if not request.user.is_authenticated():
            raise Error(err_code="401", err_message="Token error", message=u'未登录',
                        status_code=status.HTTP_401_UNAUTHORIZED)

        aes = AESCustom()
        """
        order 订单ID
        money 支付总金额
        point_pay 会员店支付金额
        gold_pay 金币支付金额
        couponcode 需领取优惠券代码
        coupon_code 不需领取优惠券代码
        """
        # 初始化参数
        self.order = aes.decrypt(request.data.get('order'))
        self.store_id = Order.objects.get(id=self.order).meal.store_id
        self.money = int(aes.decrypt(request.data.get('money')))
        # 不需要领取的优惠券

        self.point_pay = None
        self.gold_pay = None
        self.usergift = None
        # 金币支付 & 会员点支付
        if 'gold_pay' in request.data:
            self.gold_pay = int(aes.decrypt(request.data.get('gold_pay')))

        if 'point_pay' in request.data:
            self.point_pay = int(aes.decrypt(request.data.get('point_pay')))
        # couponcode = None
        if 'usergift' in request.data:
            self.usergift = int(aes.decrypt(request.data.get('usergift')))
        # 获取优惠券
        coupon = None
        if 'couponcode' in request.data:
            # 可领取优惠券
            self.couponcode = aes.decrypt(request.data.get('couponcode'))
        if 'coupon_code' in request.data:
            # 不需要领取优惠券
            self.coupon_code = aes.decrypt(request.data.get('coupon_code'))
            coupon = Coupon.objects.get(code=self.coupon_code)

        # 获取当前订单的商品列表
        order_food_list = Order_Food.objects.filter(order_id=self.order, is_active=True)

        if order_food_list.first().order.meal.status == 1:
            raise Error(err_code="401", err_message="Meal error", message=u'Meal 已离座',
                        status_code=status.HTTP_401_UNAUTHORIZED)
        # 获取会员点信息
        point = self.get_point(self.order)

        # 计算总价(不含优惠)
        totalprice = self.sum_total_price(order_food_list)

        oldprice = totalprice
        # 直接减掉优惠
        if 'less' in request.data:
            less = aes.decrypt(request.data.get('less'))
            oldprice = totalprice
            totalprice = oldprice - less
            self.couponcode = None

        if self.couponcode is not None or coupon is not None:
            if coupon is None:
                coupon = self.check_conpon(coupon)

            # 计算优惠
            if coupon.coupon_type == 0:
                """
                单品打折
                """
                for order_food in order_food_list:
                    if coupon.food.filter(id=order_food.food.id).exists():
                        if coupon.discount.coupon_type == 0:
                            # 定额
                            food = order_food_list.filter(food_id__in=coupon.food.all()).distinct()
                            price = 0
                            for f in food:
                                if self.point_pay == self.money:
                                    price += f.food_spec.vip_price * f.num
                                else:
                                    price += f.food_spec.price * f.num
                                totalprice = self.less_food_price(totalprice, f)

                            price -= coupon.discount.quota

                            totalprice = self.add_food_price(totalprice, price, order_food, False, True)
                            break

                            # if self.money == self.point_pay:
                            #     price = order_food.vip_price - coupon.discount.quota
                            # else:
                            #     price = order_food.price - coupon.discount.quota
                            # totalprice = self.add_food_price(totalprice, price, order_food, discount=True)

                        elif coupon.discount.coupon_type == 1:
                            # 折扣
                            totalprice = self.less_food_price(totalprice, order_food)
                            if self.money == self.point_pay and order_food.food_spec.vip_price > 0:
                                price = order_food.food_spec.vip_price * round(
                                    Decimal((1 - int(coupon.discount.discount) / 10)), 2)
                            else:
                                price = order_food.food_spec.price * round(
                                    Decimal((1 - int(coupon.discount.discount) / 10)), 2)
                            totalprice = self.add_food_price(totalprice, price, order_food)
                        elif coupon.discount.coupon_type == 2:
                            # 满赠
                            ret = order_food_list.filter(food__in=coupon.food.all())
                            ret = sum([r.num for r in ret])
                            if ret >= coupon.discount.more_gift:
                                count = int(ret / coupon.discount.more_gift)

                                foodspec = FoodSpec.objects.filter(food_id=coupon.discount.gift.id,
                                                                   is_default=True)

                                gift = UserGift(user=request.user,
                                                store_id=order_food.order.meal.store_id,
                                                num=coupon.discount.num * count,
                                                food=foodspec.first())
                                gift.save()
                                break
            elif coupon.coupon_type == 1:
                """
                满减打折
                """
                if coupon.fullminus.coupon_type == 0:
                    """
                    减
                    """
                    ret = order_food_list.filter(food__in=coupon.food.all())
                    ret_total_price = sum(
                        [r.vip_price if self.money == self.point_pay and r.vip_price > 0 else r.price for r in ret])

                    if ret_total_price >= coupon.fullminus.full:
                        for r in ret:
                            totalprice = self.less_food_price(totalprice, r)

                        ret_total_price -= coupon.fullminus.minus
                        ret_total_price += utils.TaxTool.tax(ret_total_price, 1, False, 8)

                        # if totalprice >= coupon.fullminus.full:
                        #     total_price = 0
                        #     for r in order_food_list:
                        #         if self.money == self.point_pay and r.vip_price > 0:
                        #             total_price += r.vip_price + r.vip_tax_value
                        #
                        #         else:
                        #             total_price += r.price + r.tax_value
                        #     total_price -= coupon.fullminus.minus
                        # total_price += utils.TaxTool.tax(total_price, 1, False, 8)
                        totalprice += round(ret_total_price, 0)
                elif coupon.fullminus.coupon_type == 1:
                    """
                    赠商品
                    """
                    if totalprice >= coupon.fullminus.full:
                        foodspec = FoodSpec.objects.filter(food_id=coupon.fullminus.gift.id,
                                                           is_default=True)

                        gift = UserGift(user=request.user,
                                        store_id=order_food_list[0].order.meal.store_id,
                                        num=coupon.fullminus.num,
                                        food=foodspec.first())
                        gift.save()
                elif coupon.fullminus.coupon_type == 2:
                    """
                    赠会员点
                    """
                    if totalprice >= coupon.fullminus.full:
                        store_id = order_food_list[0].order.meal.store_id
                        current_point = StorePointLog.objects.filter(user_id=request.user.id,
                                                                     store_id=store_id).order_by('-created')
                        if current_point.exists():
                            current_point = current_point.first().current_point
                        else:
                            current_point = 0
                        ret = StorePointLog(store_id=store_id, user_id=request.user.id,
                                            recharge_point=coupon.fullminus.point)
                        ret.current_point = current_point + coupon.fullminus.point
                        ret.save()
            elif coupon.coupon_type == 2:
                """
                均一价格
                """
                if coupon.unite.coupon_type == 0:
                    """
                    系列均一
                    """
                    ret = order_food_list.filter(Q(food__category__in=coupon.category.all()) |
                                                 Q(food_id__in=coupon.food.all())).distinct()
                    for r in ret:
                        totalprice = self.less_food_price(totalprice, r)
                        totalprice = self.add_food_price(totalprice, coupon.unite.category_price * r.num, r, True)
                elif coupon.unite.coupon_type == 1:
                    """
                    多选均一
                    """
                    ret = order_food_list.filter(food__in=coupon.food.all()).order_by('-food_spec__price')
                    total_num = 0
                    for r in ret:
                        total_num += r.num
                    affected = total_num
                    coupon_sum = int(total_num / coupon.unite.select)
                    i = 0
                    j = 0
                    k = 0
                    while i < affected:
                        if k >= coupon_sum:
                            break
                        if j >= ret.count():
                            break
                        for _ in range(0, ret[j].num):
                            if i >= affected:
                                break
                            totalprice = self.less_food_price_by_once(totalprice, ret[j])
                            i += 1
                            if i % coupon.unite.select == 0:
                                totalprice = self.add_food_price(totalprice, coupon.unite.price, ret[j], True)
                                k += 1
                                if k >= coupon_sum:
                                    break
                        j += 1

        # pay

        payinfo = PayInfo(order_id=self.order, money=totalprice, user_id=request.user.id)

        # 1. 减库存

        for order_food in order_food_list:
            FoodSpec.objects.filter(id=order_food.food_spec.id).update(stock=F('stock') - 1)

        if coupon is not None:
            payinfo.coupon = coupon

        if self.couponcode is not None:
            payinfo.coupon_code = self.couponcode

        payinfo.limit_price = oldprice - totalprice
        pay_type = None
        if 'pay_type' in request.data:
            pay_type = aes.decrypt(request.data.get('pay_type'))
        # 现金支付
        if int(pay_type) == 1:
            payinfo.pay_type = 1
            if int(self.money) == round(totalprice, 0):
                payinfo.money = round(totalprice, 0)
                payinfo.money_pay = round(totalprice, 0)
                payinfo.tax = self.tax
                payinfo.save()
                Order.objects.filter(id=self.order).update(status=1, pay_time=datetime.now())
                return Response({'success': True})
            else:
                raise Error(err_code=errors.PAY_ERROR, err_message='The price is not right',
                            message='金额计算错误, money:{0}, server:{1}'.format(self.money, totalprice),
                            status_code=status.HTTP_400_BAD_REQUEST)
        # 线上支付

        payinfo.pay_type = 0
        payinfo.money = totalprice

        if self.point_pay is not None and self.gold_pay is not None:
            payinfo.point_pay = int(self.point_pay)
            payinfo.gold_pay = int(self.gold_pay)
        payinfo.money = payinfo.gold_pay + payinfo.point_pay
        payinfo.tax = self.tax
        if payinfo.money == round(totalprice, 0):
            payinfo.save()
            Order.objects.filter(id=self.order).update(status=3, pay_time=datetime.now())
        else:
            raise Error(err_code=errors.PAY_ERROR, err_message='The price is not right',
                        message='金额计算错误, money:{0}, server:{1}'.format(self.money, totalprice),
                        status_code=status.HTTP_400_BAD_REQUEST)
        if payinfo.point_pay > 0:

            current_point = StorePointLog.objects.filter(user_id=request.user.id,
                                                         point_id=point).order_by('-created')
            if current_point.exists():
                old = current_point.first().end_date
                current_point = current_point.first().current_point
            else:
                current_point = 0

            if current_point < payinfo.point_pay:
                raise Error(err_code=1006, err_message='point is not enough.',
                            message='会员点不足', status_code=status.HTTP_400_BAD_REQUEST)

            ret = StorePointLog(point_id=point.id, user_id=request.user.id, pay_type=3,
                                recharge_point=-payinfo.point_pay,
                                current_point=current_point - payinfo.point_pay,
                                end_date=old)

            ret.save()
        if payinfo.gold_pay > 0:
            current_point = GoldLog.objects.filter(user_id=request.user.id).order_by('-created')
            if current_point.exists():
                current_point = current_point.first().current_gold
            else:
                current_point = 0
            if current_point < payinfo.gold_pay:
                raise Error(err_code=1006, err_message='gold is not enough.',
                            message='金币不足', status_code=status.HTTP_400_BAD_REQUEST)
            ret = GoldLog(user_id=request.user.id, pay_type=3, store_id=self.store_id,
                          recharge_gold=-payinfo.gold_pay,
                          current_gold=int(current_point) - int(payinfo.gold_pay))
            ret.save()
        payinfo.save()
        if self.usergift is not None:
            try:
                usergift = UserGift.objects.get(id=self.usergift)
                gift_food = Order_Food(order_id=self.order, food=usergift.food.food, food_spec=usergift.food,
                                       num=usergift.num, is_gift=True)
                gift_food.save()
                usergift.is_use = True
                usergift.use_date = timezone.now()
                usergift.payinfo = payinfo
                usergift.save()
            except UserGift.DoesNotExist:
                raise Error(err_code=1006, err_message='gift id is not found.',
                            message='赠品卷未找到', status_code=status.HTTP_400_BAD_REQUEST)

        Order.objects.filter(id=self.order).update(status=3, pay_time=datetime.now())
        Order_Food.objects.filter(order_id=self.order).update(status=1)

        if self.couponcode is not None:
            self.couponcode.is_use = True
            self.couponcode.save()

        return Response({'success': True})


class StorePayTypeViewSet(ModelViewSet):
    queryset = StorePayType.objects.all()
    serializer_class = StorePayTypeSerializer
    filter_fields = ('store',)


class UserGiftViewSet(ModelViewSet):
    queryset = UserGift.objects.filter(is_use=False)
    serializer_class = UserGiftSerializer
    filter_fields = ('user', 'store')
