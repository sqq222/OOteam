import logging

import pytz
from django.contrib.auth import authenticate
from django.db.models import Q, Sum, FieldDoesNotExist
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.utils.crypto import get_random_string
from rest_framework import views, generics, permissions
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import list_route
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.utils import timezone as tz
from django_filters.rest_framework import DjangoFilterBackend

from shop.api import errors
from shop.api.renderer import ImageJSONRenderer
from shop.user.models import *
from shop.user.serializers import *
from rest_framework import status
from .serializers import *
from .exception_handler import Error, ErrorResponse, ForeignObjectRelDeleteError, ModelDontHaveIsActiveFiled
from django.utils.timezone import utc
from datetime import datetime
from pytz import timezone

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
    page_size = 15
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
    authentication_classes = (BasicAuthentication,)


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


class Store_RotationViewSet(ModelViewSet):
    queryset = Store_Rotation.objects.all()
    serializer_class = Store_RotationSerializer
    # renderer_classes = ImageJSONRenderer
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

    @list_route(methods=['get'])
    def me(self, request):

        print(self.request.authenticators)
        print(self.request.authenticators[0].authenticate(self.request))
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
    now = pytz.timezone("Asia/Shanghai").localize(datetime.now())
    queryset = Food.objects.filter(Q(Q(Q(sellperiod_food__begin__lt=now) & Q(sellperiod_food__end__gt=now))
                                     & Q(sell_time=1)) | Q(sell_time=0))
    serializer_class = FoodSerializer
    pagination_class = StandardResultsSetPagination
    paginate_by = 15
    filter_fields = ('store', 'category')
    search_fields = ('name',)

    def get_queryset(self):
        now = pytz.timezone("Asia/Shanghai").localize(datetime.now())
        if now.weekday() == 1:
            return self.queryset.filter(Q(Q(monday=True) & Q(sell_time=2)) | Q(sell_time=0))
        elif now.weekday() == 2:
            return self.queryset.filter(Q(Q(tuesday=True) & Q(sell_time=2)) | Q(sell_time=0))
        elif now.weekday() == 3:
            return self.queryset.filter(Q(Q(wednesday=True) & Q(sell_time=2)) | Q(sell_time=0))
        elif now.weekday() == 4:
            return self.queryset.filter(Q(Q(thursday=True) & Q(sell_time=2)) | Q(sell_time=0))
        elif now.weekday() == 5:
            return self.queryset.filter(Q(Q(friday=True) & Q(sell_time=2)) | Q(sell_time=0))
        elif now.weekday() == 6:
            return self.queryset.filter(Q(Q(saturday=True) & Q(sell_time=2)) | Q(sell_time=0))
        elif now.weekday() == 7:
            return self.queryset.filter(Q(Q(sunday=True) & Q(sell_time=2)) | Q(sell_time=0))

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
    search_fields = ('number', 'display_number', 'category__id', 'category__name', 'store__id')

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
    from django.utils.dateparse import parse_datetime
    datetime = pytz.timezone("Asia/Shanghai").localize(datetime.now())
    queryset = Coupon.objects.filter(start_show__lt=datetime, end__gt=datetime, status=0)
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
                coupon_code = CouponCode.objects.filter(coupon__store_id=request.GET.get('store'),
                                                        receive_user=request.user)
            else:
                coupon_code = CouponCode.objects.filter(receive_user=request.user)
            return Response(CouponCodeSerializer(coupon_code, many=True).data)
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
            if CouponCode.objects.filter(coupon=coupon, is_receive=False).count() == 0:
                return Response({'success': False, 'message': '优惠券已全部发放'})
            coupon_code = CouponCode.objects.filter(coupon_id=request.data['coupon'], is_receive=False).first()
            coupon_code.receive_user = request.user
            coupon_code.is_receive = True
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

    @list_route(methods=['get'])
    def my_meal(self, request):
        if request.user.is_authenticated():
            queryset = self.filter_queryset(self.get_queryset().filter(user=request.user).order_by('-created'))

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
        if request.user is not None:
            try:
                if request.POST.get('spell') is True:
                    raise Meal.DoesNotExist()
                result = Meal.objects.get(desk_id=request.POST.get('desk'), store_id=request.POST.get('store'),
                                          status=1)
                if result is not None:
                    user_add = AbstractUser.objects.get(id=request.POST.get('user'))
                    result.user.add(user_add)
                    order = Order.objects.filter(meal=result).order_by('created').last()
                    return Response({'success': True, 'meal_id': result.id, 'order_id': order.id})
            except Meal.DoesNotExist:
                meal = Meal(desk_id=request.POST.get('desk'), store_id=request.POST.get('store'))
                meal.save()
                user = AbstractUser.objects.get(id=request.POST.get('user'))
                meal.user.add(user)
                from django.utils import timezone

                code = timezone.localtime(timezone.now()).strftime(settings.CODE_DATETIME_FORMAT) + \
                       get_random_string(length=9, allowed_chars='0123456789')
                order = Order(meal=meal, code=code)
                order.save()
                return Response({'success': True, 'meal_id': meal.id, 'order_id': order.id})
        else:
            raise Error(err_code="401", err_message="Token error", message=u'未登录',
                        status_code=status.HTTP_401_UNAUTHORIZED)

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
        if request.user is not None:
            try:
                meal = Meal.objects.filter(id=request.POST.get('meal')).update(status=1)
            except Meal.DoesNotExist:
                raise Error(err_code='404', err_message='Not found', message=u'用餐信息不存在',
                            status_code=status.HTTP_404_NOT_FOUND)
            if meal.order_meal.count() == Order.objects.filter(meal=meal, status__lt=0).count():
                meal.status = 2
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

    @list_route(methods=['get'])
    def get_food_num(self, request):
        return Response({'success': True,
                         'num': Order_Food.objects.values('order').filter(order_id=request.GET.get('id'))
                        .annotate(count=Sum('num'))[0]['count']})


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
    def add_cart(self, request):
        """
        添加购物车
        """
        serializer = AddCartSerializer(data=request.data)

        if serializer.is_valid():
            order_food = Order_Food.objects.filter(order_id=serializer.initial_data['order'],
                                                   food_id=serializer.initial_data['food'],
                                                   food_spec_id=serializer.initial_data['food_spec'])
            if 'tag' in serializer.initial_data:
                tags = serializer.initial_data['tag']
                tags = tags.split(',')
                for tag in tags:
                    order_food = order_food.filter(tag=tag)

            if order_food.count() > 0:
                if order_food.first().num + int(serializer.initial_data['num']) <= 0:
                    order_food.delete()
                order_food = order_food.first()
                order_food.num += int(serializer.initial_data['num'])
                order_food.desc = serializer.initial_data['desc']
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
