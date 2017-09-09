import base64
from collections import OrderedDict
from datetime import timedelta

import itertools
import oauth2_provider
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.validators import RegexValidator
from django.db.models import Q
from rest_framework import serializers, status
from rest_framework.fields import CharField, SkipField
from rest_framework.validators import UniqueValidator

from shop.api.exception_handler import Error
from shop.user.models import *


def get_package_version(package):
    """
    Return the version number of a Python package as a list of integers
    e.g., 1.7.2 will return [1, 7, 2]
    """
    return [int(num) for num in package.__version__.split('.')]


AbstractUser = get_user_model()
oauth_toolkit_version = get_package_version(oauth2_provider)


class CurrentDateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        # tz = timezone.get_default_timezone()
        # # timezone.localtime() defaults to the current tz, you only
        # # need the `tz` arg if the current tz != default tz
        # value = timezone.localtime(value, timezone=tz)
        # # py3 notation below, for py2 do:
        # # return super(CustomDateTimeField, self).to_representation(value)
        # return super().to_representation(value)
        return super(CurrentDateTimeField, self).to_representation(value)


class AuthSerializerMixin(object):
    def create(self, validated_data):
        if validated_data.get('username', None):
            validated_data['username'] = validated_data['username'].lower()
        if validated_data.get('email', None):
            validated_data['email'] = validated_data['email'].lower()
        if validated_data.get('password', None):
            validated_data['password'] = make_password(validated_data['password'])

        return super(AuthSerializerMixin, self).create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get('username', None):
            validated_data['username'] = validated_data['username'].lower()
        if validated_data.get('email', None):
            validated_data['email'] = validated_data['email'].lower()
        if validated_data.get('password', None):
            validated_data['password'] = make_password(validated_data['password'])

        return super(AuthSerializerMixin, self).update(instance, validated_data)

    def validate_username(self, value):
        username = self.context['request'].user.username if self.context['request'].user.is_authenticated() else None
        if value and value != username and AbstractUser.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Username is taken')
        return value

    def validate_email(self, value):
        email = self.context['request'].user.email if self.context['request'].user.is_authenticated() else None
        if value and value != email and AbstractUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('an account already exists whith the email')
        return value

    def validate_password(self, value):
        value = base64.decodebytes(bytes(value, 'utf-8')).decode()
        if len(value) < 6:
            raise serializers.ValidationError('Password must be at least 6 characters')
        return value


class LoginSerializer(serializers.ModelSerializer):
    client_id = serializers.SerializerMethodField()
    client_secret = serializers.SerializerMethodField()

    class Meta:
        model = AbstractUser
        fields = ('client_id', 'client_secret')

    def get_application(self, obj):
        # If we're using version 0.8.0 or higher
        if oauth_toolkit_version[0] >= 0 and oauth_toolkit_version[1] >= 8:
            return obj.oauth2_provider_application.first()
        else:
            return obj.application_set.first()

    def get_client_id(self, obj):
        return self.get_application(obj).client_id

    def get_client_secret(self, obj):
        return self.get_application(obj).client_secret


class SignUpSerializer(AuthSerializerMixin, LoginSerializer):
    password = CharField(max_length=128, write_only=True, error_messages={'required': 'Password'})
    username = CharField(error_messages={'required': 'Username'},
                         max_length=30,
                         validators=[RegexValidator(),
                                     UniqueValidator(queryset=AbstractUser.objects.all(), message='Username taken')])
    email = CharField(allow_blank=True, allow_null=True, max_length=75, required=True,
                      validators=[UniqueValidator(queryset=AbstractUser.objects.all(), message='Email taken')])

    class Meta(LoginSerializer.Meta):
        fields = ('fullname', 'username', 'sex', 'birthday', 'region', 'email',)


class UserSerializer(serializers.ModelSerializer):
    sex = CharField(source='get_sex_display')
    store_name = serializers.CharField(source='store.name')

    class Meta:
        model = AbstractUser
        fields = (
            'id', 'img', 'username', 'fullname', 'sex', 'birthday', 'telephone', 'store', 'user_type', 'is_basemob',
            'store_name')


class StoreSerializer(serializers.ModelSerializer):
    store_logo = serializers.CharField(source='store.logo')
    store_name = serializers.CharField(source='store.name')
    store_address = serializers.CharField(source='store.address')
    store_tel = serializers.CharField(source='store.tel')
    store_order_tel = serializers.CharField(source='store.business.order_tel')
    store_notice = serializers.CharField(source='store.business.notice')
    store_desc = serializers.CharField(source='store.business.desc')
    store_images = serializers.SerializerMethodField()
    store_license = serializers.CharField(source='store.license.status')
    store_personal = serializers.SerializerMethodField()
    store_food_safety = serializers.CharField(source='store.food_safety.status')
    store_principal = serializers.CharField(source='store.principal')
    store_principal_tel = serializers.CharField(source='store.principal_tel')
    store_bank_num = serializers.CharField(source='store.bank_num')

    def get_store_images(self, obj):
        return True if Store_Image.objects.filter(Store_id=obj.store.id).count() > 0 else False

    def get_store_personal(self, obj):
        return False if obj.store.license is None else True

    class Meta:
        model = AbstractUser
        fields = (
            'store_logo', 'store_name', 'store_address', 'store_tel', 'store_order_tel', 'store_notice', 'store_desc',
            'store_images', 'store_license', 'store_personal', 'store_food_safety')


class FreeDaySerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return instance.free_day

    class Meta:
        model = Store_Business_Time_FreeDay
        fields = ('free_day',)


class Store_Business_Time_Serializer(serializers.ModelSerializer):
    freeday = serializers.SerializerMethodField()

    def get_freeday(self, obj):
        freeday = Store_Business_Time_FreeDay.objects.filter(store_business_time_id=obj.id)
        return FreeDaySerializer(freeday, many=True).data

    class Meta:
        model = Store_Business_Time
        fields = ('start_normal', 'end_normal', 'start_holiday', 'end_holiday', 'last_normal', 'last_holiday',
                  'start_rest_normal',
                  'end_rest_normal', 'start_rest_holiday',
                  'end_rest_holiday', 'monday', 'tuesday', 'wednesday', 'thursday',
                  'friday', 'saturday', 'sunday', 'freeday')


class Store_Image_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Store_Image
        fields = ('img',)


class Store_Lobby_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Store_Lobby
        fields = ('img',)


class Store_Kitchen_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Store_Kitchen
        fields = ('img',)


class Store_Other_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Store_Other
        fields = ('img',)


class StorePayTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorePayType
        exclude = ('id',)


class Store_Ad_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Store_Ad
        fields = ('img',)


class Store_Rotation_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Store_Rotation
        fields = ('rotation',)


class Store_License_Serializer(serializers.ModelSerializer):
    store = serializers.SerializerMethodField()

    def get_store(self, obj):
        # try:
        #     return Stores.objects.get(license_id=obj.id)
        # except Stores.DoesNotExist:
        #     return ''
        # return Stores.objects.get(license__id=obj.id).id
        return 0

    def create(self, validated_data):
        license = Store_License(
            front=validated_data['front'],  # HERE
            backend=validated_data['backend'],
            business_address=validated_data['business_address'],
            business_enddate=validated_data['business_enddate'],
            business_name=validated_data['business_name'],
            business_license=validated_data['business_license'],

        )
        license.save()
        Stores.objects.filter(pk=self.data['store']).update(license_id=license.id)

        return license

    class Meta:
        model = Store_License
        fields = '__all__'


class DiscountCouponSerializer(serializers.ModelSerializer):
    food = serializers.SerializerMethodField()
    coupon_type = serializers.CharField(source='get_coupon_type_display')
    coupon_type_value = serializers.CharField(source='coupon_type')
    gift = serializers.CharField(source='gift.name')
    price = serializers.SerializerMethodField()

    def to_representation(self, instance):

        ret = super(DiscountCouponSerializer, self).to_representation(instance)
        if instance.coupon.food.count() == 1 and instance.coupon.category.count() == 0:
            return ret
        else:
            ret.pop('price')
            return ret

    def get_price(self, obj):
        try:
            return obj.coupon.food.all()[0].foodspec.filter(
                is_default=True).first().price if obj.coupon.food.count() == 1 and obj.coupon.category.count() == 0 \
                else None
        except:
            return None

    def get_food(self, obj):

        return obj.coupon.food.all()[
            0].name if obj.coupon.food.count() == 1 and obj.coupon.category.count() == 0 else None

    class Meta:
        model = DiscountCoupon
        fields = ('coupon_type', 'coupon_type_value', 'unit', 'food', 'quota', 'price', 'discount', 'more_gift', 'gift',
                  'num',)


# class FullMinusDetailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FullMinusDetail
#         fields = ('fullminus',)

class FullMinusCouponSerializer(serializers.ModelSerializer):
    coupon_type = serializers.CharField(source='get_coupon_type_display')
    coupon_type_value = serializers.CharField(source='coupon_type')
    gift = serializers.CharField(source='gift.name')

    class Meta:
        model = FullMinusCoupon
        fields = ('full', 'coupon_type', 'coupon_type_value', 'minus', 'gift', 'num', 'point')


class UniteCouponSerializer(serializers.ModelSerializer):
    coupon_type = serializers.CharField(source='get_coupon_type_display')
    coupon_type_value = serializers.CharField(source='coupon_type')

    class Meta:
        model = UniteCoupon
        fields = ('coupon_type', 'coupon_type_value', 'category_price', 'select', 'price', 'unit')


class CouponTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponTime
        fields = '__all__'


class CouponFoodSerializer(serializers.ModelSerializer):
    # def to_representation(self, instance):
    #     return instance.name

    class Meta:
        model = Food
        fields = ('id', 'name',)


class CouponCategorySerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return instance.name

    class Meta:
        model = FoodCategory
        fields = ('name',)


class CouponSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', help_text='店铺ID')
    coupon_code = serializers.CharField(source='code')
    coupon_name = serializers.CharField(source='name')
    activity_start = CurrentDateTimeField(source='start', format=settings.DATETIME_FORMAT)
    activity_end = CurrentDateTimeField(source='end', format=settings.DATETIME_FORMAT)
    coupon_type = serializers.CharField(source='get_coupon_type_display')
    coupon_type_value = serializers.CharField(source='coupon_type')
    is_all_category = serializers.SerializerMethodField()
    is_all_food = serializers.SerializerMethodField()
    discount = DiscountCouponSerializer()
    fullminus = FullMinusCouponSerializer()
    unite = UniteCouponSerializer()
    coupon_time = CouponTimeSerializer()
    food = CouponFoodSerializer(read_only=True, many=True)
    category = CouponCategorySerializer(read_only=True, many=True)
    can_receive = serializers.SerializerMethodField()

    def get_can_receive(self, obj):
        """
        是否领取
        :param obj: 
        :return: 
        """
        # 是否发放完毕
        if CouponCode.objects.filter(coupon=obj).count() >= obj.count:
            return False
        # 是否有request
        if 'request' not in self.context:
            return False
        # 是否登录
        request = self.context['request']
        if request.user.is_authenticated():
            # 是否超过单人限额
            user_coupon = CouponCode.objects.filter(coupon=obj, receive_user_id=request.user.id)
            if user_coupon.count() >= obj.single_limit:
                return False
            # 是否超过每人每日限额
            receive_count = CouponCode.objects.filter(coupon=obj, receive_time__date=datetime.today(),
                                                      receive_user=request.user).count()
            if obj.daily_limit is not None and receive_count >= obj.daily_limit:
                return False

            return True
        return False

    def to_representation(self, instance):

        ret = super(CouponSerializer, self).to_representation(instance)
        if instance.coupon_type == 0:
            ret.pop('fullminus')
            ret.pop('unite')
        elif instance.coupon_type == 1:
            ret.pop('discount')
            ret.pop('unite')
        elif instance.coupon_type == 2:
            ret.pop('discount')
            ret.pop('fullminus')
        return ret

    def get_is_all_category(self, obj):
        return True if FoodCategory.objects.filter(store=obj.store).count() == obj.category.count() else False

    def get_is_all_food(self, obj):
        return True if Food.objects.filter(store=obj.store).count() == obj.food.count() else False

    class Meta:
        model = Coupon
        fields = ('id', 'store_name', 'coupon_code', 'coupon_name', 'activity_start', 'activity_end', 'coupon_type',
                  'coupon_type_value', 'discount', 'fullminus', 'unite', 'slogan', 'detail_master', 'detail_minor',
                  'daily_limit', 'single_limit', 'background', 'show_img', 'coupon_time', 'is_all_category',
                  'is_all_food', 'category', 'food', 'is_receive', 'can_receive', 'display_background')


class CouponCodeSerializer(serializers.ModelSerializer):
    receive_time = CurrentDateTimeField(format=settings.DATETIME_FORMAT)
    coupon = CouponSerializer()

    class Meta:
        model = CouponCode
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')


class OrderFoodCreateSerializer(serializers.ModelSerializer):
    tag = TagSerializer(many=True)
    food = serializers.CharField(source='food.name')
    food_spec = serializers.CharField(source='food_spec.name')

    class Meta:
        model = Order_Food
        fields = '__all__'


class OrderFoodSerializer(serializers.ModelSerializer):
    food_name = serializers.CharField(source='food.name')
    food_spec_id = serializers.CharField(source='food_spec.id')
    food_spec = serializers.CharField(source='food_spec.name')
    food_id = serializers.CharField(source='food.id')
    food_is_include_tax = serializers.BooleanField(source='food.is_include_tax')
    tax = serializers.SerializerMethodField()
    vip_tax = serializers.SerializerMethodField()
    img = serializers.SerializerMethodField()
    tags = TagSerializer(source='tag', many=True, read_only=True)
    food_vip_price = serializers.CharField(source='food_spec.vip_price')
    food_price = serializers.CharField(source='food_spec.price')
    is_one_spec = serializers.SerializerMethodField()
    food_tax = serializers.SerializerMethodField()
    include_price = serializers.DecimalField(source='food_spec.in_tax_price', max_digits=5, decimal_places=0)
    vip_include_price = serializers.DecimalField(source='food_spec.in_tax_vip_price', max_digits=5, decimal_places=0)
    total_price = serializers.SerializerMethodField()
    vip_total_price = serializers.SerializerMethodField()
    total_tax = serializers.SerializerMethodField()
    total_vip_tax = serializers.SerializerMethodField()
    include_total_price = serializers.SerializerMethodField()
    vip_include_total_price = serializers.SerializerMethodField()
    is_preferent = serializers.SerializerMethodField()

    def get_is_preferent(self, obj):
        """
        是否优惠商品
        :param obj:
        :return:
        """
        ret = PayInfo.objects.filter(Q(order_id=obj.order_id) & (Q(coupon__food__in=[obj.food])))
        if ret.exists():
            return True

        return False

    def get_total_tax(self, obj):
        """
        总税额
        :param obj:
        :return:
        """
        return obj.food_spec.tax_value * Decimal(obj.num)

    def get_total_vip_tax(self, obj):
        """
        VIP总税额
        :param obj:
        :return:
        """
        return obj.food_spec.vip_tax_value * Decimal(obj.num)

    def get_total_price(self, obj):
        """
        不含税总价格
        :param obj:
        :return:
        """
        return obj.food_spec.price * Decimal(obj.num)

    def get_vip_total_price(self, obj):
        """
        不含税VIP总价格
        :param obj:
        :return:
        """
        return obj.food_spec.vip_price * Decimal(obj.num)

    def get_include_total_price(self, obj):
        """
        含税总价格
        :param obj:
        :return:
        """
        return obj.food_spec.in_tax_price * Decimal(obj.num)

    def get_vip_include_total_price(self, obj):
        """
        含税VIP总价格
        :param obj:
        :return:
        """
        return obj.food_spec.in_tax_vip_price * Decimal(obj.num)

    def get_food_tax(self, obj):
        """
        税率
        :param obj:
        :return:
        """
        return obj.food.tax.tax

    def get_is_one_spec(self, obj):
        if FoodSpec.objects.filter(food_id=obj.food).count() > 1:
            return False
        else:
            return True

    def get_tax(self, obj):
        """
        税额
        :param obj:
        :return:
        """
        return obj.food_spec.tax_value

    def get_vip_tax(self, obj):
        """
        VIP税额
        :param obj:
        :return:
        """
        return obj.food_spec.vip_tax_value

    def get_img(self, obj):
        img = FoodImage.objects.filter(food=obj.food).first()
        if img is None:
            return None
        else:
            return self.context['request'].build_absolute_uri(img.image.url)

    class Meta:
        model = Order_Food
        fields = (
            'id', 'food_name', 'food_id', 'food_spec_id', 'food_spec', 'img', 'tags', 'desc', 'food_vip_price',
            'food_price', 'num', 'status', 'food_tax',
            'price', 'food_is_include_tax', 'tax', 'vip_tax', 'is_one_spec', 'vip_include_price', 'include_price',
            'total_price', 'vip_total_price', 'total_tax', 'total_vip_tax', 'include_total_price',
            'vip_include_total_price', 'is_preferent')


class OrderSerializer(serializers.ModelSerializer):
    created = CurrentDateTimeField(format=settings.DATETIME_FORMAT)
    detail = serializers.SerializerMethodField()
    total_num = serializers.SerializerMethodField()
    use_coupon_code = serializers.CharField(source='order_pay.coupon_code.code')
    pay_time = CurrentDateTimeField(source='order_pay.created', format=settings.DATETIME_FORMAT)
    pay_code = serializers.CharField(source='order_pay.code')
    pay_type = serializers.IntegerField(source='order_pay.pay_type')
    card_pay = serializers.IntegerField(source='order_pay.card_pay')
    alipay_pay = serializers.IntegerField(source='order_pay.alipay_pay')
    point_pay = serializers.IntegerField(source='order_pay.point_pay')
    gold_pay = serializers.IntegerField(source='order_pay.gold_pay')
    money_pay = serializers.IntegerField(source='order_pay.money_pay')
    coupon_name = serializers.CharField(source='order_pay.coupon.name')
    coupon_code = serializers.CharField(source='order_pay.coupon.code')
    limit_price = serializers.IntegerField(source='order_pay.limit_price')
    name = serializers.CharField(source='waiter.fullname')
    total_price = serializers.SerializerMethodField()
    total_tax = serializers.SerializerMethodField()
    total_vip_tax = serializers.SerializerMethodField()
    total_vip_price = serializers.SerializerMethodField()

    def get_detail(self, obj):
        return OrderFoodSerializer(Order_Food.objects.filter(order_id=obj.id, num__gt=0),
                                   many=True, context=self.context).data

    def get_total_tax(self, obj):
        if obj.status == 0 or obj.status == 9:
            ret = Order_Food.objects.filter(order_id=obj.id)
            total_tax = 0
            for r in ret:
                total_tax += r.tax_value
            return total_tax
        else:
            return PayInfo.objects.get(order=obj).tax

    def get_total_vip_tax(self, obj):
        if obj.status == 0 or obj.status == 9:
            ret = Order_Food.objects.filter(order_id=obj.id)
            total_tax = 0
            for r in ret:
                total_tax += r.vip_tax_value
            return total_tax
        else:
            return PayInfo.objects.get(order=obj).tax

    def get_total_price(self, obj):
        total_price = 0
        if obj.status == 0 or obj.status == 9:
            total_price += obj.total_price + obj.tax_value
        elif obj.status > 0 and obj.status is not 9:
            total_price += PayInfo.objects.get(order=obj).money if PayInfo.objects.filter(order=obj).exists() else 0
        return total_price

    def get_total_vip_price(self, obj):
        total_price = 0
        if obj.status == 0 or obj.status == 9:
            total_price += obj.total_vip_price + obj.vip_tax_value
        elif obj.status > 0 and obj.status is not 9:
            total_price += PayInfo.objects.get(order=obj).money if PayInfo.objects.filter(order=obj).exists() else 0
        return total_price

    def get_total_num(self, obj):
        ret = Order_Food.objects.filter(order_id=obj.id, is_gift=False)
        result = 0
        if ret.exists():
            for r in ret:
                result += r.num
        return result

    class Meta:
        model = Order
        fields = ('id', 'code', 'total_price', 'total_num', 'use_coupon_code', 'pay_time',
                  'pay_code', 'pay_code', 'pay_type', 'card_pay', 'alipay_pay', 'point_pay',
                  'gold_pay', 'money_pay', 'coupon_name', 'coupon_code', 'limit_price', 'created',
                  'status', 'meal', 'detail', 'name', 'total_tax', 'total_vip_tax', 'total_vip_price')


class MealSerializer(serializers.ModelSerializer):
    created = serializers.DateTimeField(format=settings.DATETIME_FORMAT)
    store_id = serializers.CharField(source='store.id')
    store_name = serializers.CharField(source='store.name')
    desk_id = serializers.CharField(source='desk.id')
    desk_number = serializers.CharField(source='desk.display_number')
    order = OrderSerializer(source='order_meal', many=True)
    num = serializers.IntegerField(source='total_user')
    food_num = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    total_tax = serializers.SerializerMethodField()
    total_vip_tax = serializers.SerializerMethodField()
    total_vip_price = serializers.SerializerMethodField()

    def get_total_vip_price(self, obj):
        order = Order.objects.filter(meal_id=obj.id)
        total_price = 0
        for o in order:
            if o.status == 0 or o.status == 9:
                total_price += o.total_vip_price + o.vip_tax_value
            elif o.status > 0:
                try:
                    total_price += PayInfo.objects.get(order=o).money
                except PayInfo.DoesNotExist:
                    total_price += o.total_vip_price
        return int(total_price)

    def get_total_tax(self, obj):
        total_tax = 0
        order = Order.objects.filter(meal=obj)
        for o in order:
            if o.status == 0 or o.status == 9:
                total_tax += o.tax_value
            else:
                total_tax += PayInfo.objects.get(order=o).tax

        return total_tax

    def get_total_vip_tax(self, obj):
        total_tax = 0
        order = Order.objects.filter(meal=obj)
        for o in order:
            if o.status == 0 or o.status == 9:
                total_tax += o.vip_tax_value
            else:
                total_tax += PayInfo.objects.get(order=o).tax

        return total_tax

    def get_total_price(self, obj):
        order = Order.objects.filter(meal_id=obj.id)
        total_price = 0
        for o in order:
            if o.status == 0 or o.status == 9:
                total_price += o.total_price + o.tax_value
            elif o.status > 0:
                total_price += PayInfo.objects.get(order=o).money
        return total_price

    def get_food_num(self, obj):
        ret = Order_Food.objects.filter(order__meal_id=obj.id, is_gift=False).values('id').annotate(sum=Sum('num'))
        result = 0
        for r in ret:
            result += r['sum']
        return result

    class Meta:
        model = Meal
        fields = ('id', 'code', 'created', 'store_id', 'store_name', 'desk_id', 'desk_number', 'order', 'num',
                  'food_num', 'total_price', 'total_vip_price', 'total_vip_tax', 'total_tax','status', )


class MyOrderSerializer(serializers.ModelSerializer):
    created = CurrentDateTimeField(format=settings.DATETIME_FORMAT)
    detail = OrderFoodSerializer(source='order_food.first')

    class Meta:
        model = Order
        fields = ('id', 'code', 'total_price', 'created', 'status', 'meal', 'detail')


class MyMealSerializer(serializers.ModelSerializer):
    created = CurrentDateTimeField(format=settings.DATETIME_FORMAT)
    store_id = serializers.CharField(source='store.id')
    store_name = serializers.CharField(source='store.name')
    store_logo = serializers.SerializerMethodField()
    desk_id = serializers.CharField(source='desk')
    desk_number = serializers.CharField(source='desk.number')
    order = MyOrderSerializer(source='order_meal.first')
    food_count = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, obj):
        order = Order.objects.filter(meal_id=obj.id)
        total_price = 0
        for o in order:
            if o.status == 0:
                total_price += o.total_price
            elif o.status > 0:
                try:
                    total_price += PayInfo.objects.get(order=o).money
                except PayInfo.DoesNotExist:
                    total_price += o.total_price
        return total_price

    def get_food_count(self, obj):
        ret = Order_Food.objects.values('order').filter(order__meal_id=obj.id).annotate(count=Sum('num'))
        return ret[0]['count'] if ret.exists() else 0

    def get_store_logo(self, obj):

        if obj.store.logo is None:
            return None
        else:
            return self.context['request'].build_absolute_uri(obj.store.logo.url)

    class Meta:
        model = Meal
        fields = ('id', 'code', 'created', 'store_id', 'store_logo', 'store_name', 'desk_id', 'desk_number', 'order',
                  'food_count', 'total_price')


class AddCartSerializer(serializers.ModelSerializer):
    """
    添加购物车
    """
    order = serializers.IntegerField(required=True)
    food = serializers.IntegerField(required=True)
    food_spec = serializers.IntegerField(required=True)
    num = serializers.IntegerField(required=True)
    tag = serializers.CharField(required=False)
    price = serializers.IntegerField(required=True)
    desc = serializers.CharField(required=False)

    def validate_order(self, value):
        if value and not Order.objects.filter(id=value).exists():
            raise serializers.ValidationError('Order not exist.')
        return value

    def validate_food(self, value):
        if value and not Food.objects.filter(id=value).exists():
            raise serializers.ValidationError('Food not exist.')
        return value

    def validate_food_spec(self, value):
        if value and not FoodSpec.objects.filter(id=value).exists():
            raise serializers.ValidationError('Food spec not exist.')
        return value

    def validate_tag(self, value):
        tags = value.split(',')
        if value and not Tag.objects.filter(id__in=tags).exists():
            raise serializers.ValidationError('Tag not exist.')
        return value

    def validate(self, attrs):
        order = Order.objects.filter(id=attrs['order'])
        if order.exists():
            order = order.first()
            meal = order.meal
            if meal.status == 1:
                raise Error(err_code="401", err_message="Meal error", message=u'Meal 已离座',
                            status_code=status.HTTP_401_UNAUTHORIZED)
            else:
                return attrs
        return attrs

    # password = CharField(max_length=128, write_only=True, error_messages={'required': 'Password'})
    # username = CharField(error_messages={'required': 'Username'},
    #                      max_length=30,
    #                      validators=[RegexValidator(),
    #                                  UniqueValidator(queryset=AbstractUser.objects.all(), message='Username taken')])
    # email = CharField(allow_blank=True, allow_null=True, max_length=75, required=True,
    #                   validators=[UniqueValidator(queryset=AbstractUser.objects.all(), message='Email taken')])

    class Meta(LoginSerializer.Meta):
        fields = ('order', 'food', 'food_spec', 'num', 'tag', 'price', 'desc')


class QueueSerializer(serializers.ModelSerializer):
    created = CurrentDateTimeField(format=settings.DATETIME_FORMAT)
    desk_category = serializers.CharField(source='desk_category.name')

    class Meta:
        model = Queue
        fields = '__all__'


class QueueLogSerializer(serializers.ModelSerializer):
    queue = QueueSerializer()

    class Meta:
        model = QueueLog
        fields = '__all__'


class PayInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayInfo
        fields = '__all__'


class KitchenFoodSerializer(serializers.ModelSerializer):
    food_name = serializers.CharField(source='food.name')
    # logo = serializers.SerializerMethodField()  #
    logo = serializers.ImageField(source='food.food_image.first.image')
    tag = TagSerializer(many=True)
    food_spec = serializers.CharField(source='food_spec.name')
    is_tax = serializers.BooleanField(source='food.is_include_tax')
    tax = serializers.SerializerMethodField()
    one_spec = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    def get_price(self, obj):
        if obj.food.is_include_tax:
            return round(obj.food_spec.in_tax_price, 0)
        else:
            return round(obj.food_spec.price, 0)

    def get_one_spec(self, obj):
        if FoodSpec.objects.filter(food_id=obj.food.id).count() > 1:
            return False
        else:
            return True

    def get_logo(self, obj):
        return FoodImage.objects.filter(food_id=obj.food.id).first().image.url

    def get_tax(self, obj):
        return obj.tax_value

    class Meta:
        model = Order_Food
        fields = ('id', 'food_name', 'logo', 'desc', 'tag', 'food_spec',
                  'num', 'price', 'is_tax', 'tax', 'status', 'one_spec')


class KitChenRefundSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return instance.id

    class Meta:
        model = RefundOrder
        fields = ('id',)


class KitChenMealSerializer(serializers.ModelSerializer):
    meal_id = serializers.IntegerField(source='id')
    meal_code = serializers.IntegerField(source='code')
    desk_id = serializers.IntegerField(source='desk.id')
    desk_num = serializers.CharField(source='desk.display_number')
    created = serializers.SerializerMethodField()
    waiting_time = serializers.SerializerMethodField()
    is_pay = serializers.SerializerMethodField()  # serializers.IntegerField(source='order_meal.status')
    finished = serializers.SerializerMethodField()
    total_food = serializers.SerializerMethodField()  # serializers.IntegerField(source='order_meal.order_food.count')
    details = serializers.SerializerMethodField()
    refund_id = serializers.SerializerMethodField()
    own_waiter = serializers.SerializerMethodField()

    # status = serializers.SerializerMethodField()
    # serializers.IntegerField(source='order_food.status')  # TODO: Fix bug: status is not exist

    def get_is_pay(self, obj):
        if Order.objects.filter(meal_id=obj.id, status=1).count() > 0:
            return False
        else:
            return True

    def get_total_food(self, obj):
        orderfood = Order_Food.objects.filter(order__meal__id=obj.id)
        result = 0
        for o in orderfood:
            result += o.num
        return result

    def get_created(self, obj):
        order = Order.objects.filter(meal_id=obj.id).order_by('created')
        result_list = []
        for o in order:
            food = Order_Food.objects.filter(order_id=o.id, status=3).count()
            if food < o.order_food.count():
                result_list.append(o)
            tz = timezone.get_default_timezone()
            # timezone.localtime() defaults to the current tz, you only
            # need the `tz` arg if the current tz != default tz

        # timezone.localtime() defaults to the current tz, you only
        # need the `tz` arg if the current tz != default tz

        return PayInfo.objects.get(order_id=result_list[0].id).created.strftime(settings.DATETIME_FORMAT) if len(
            result_list) > 0 else \
            PayInfo.objects.get(
                order_id=order.last().id).created.strftime(settings.DATETIME_FORMAT)

    def get_own_waiter(self, obj):
        order = Order.objects.filter(meal_id=obj.id).last()
        if order.waiter is None:
            return 0
        else:
            return order.waiter.user_type

    def get_refund_id(self, obj):
        return KitChenRefundSerializer(RefundOrder.objects.filter(order__in=Order.objects.filter(meal_id=obj.id)),
                                       many=True).data

    def get_finished(self, obj):
        return Order_Food.objects.filter(order__in=Order.objects.filter(meal_id=obj.id), status=3).count()

    def get_waiting_time(self, obj):
        order = Order.objects.filter(meal_id=obj.id, order_pay__isnull=False).order_by('created')
        result_list = []
        for o in order:
            food = Order_Food.objects.filter(order_id=o.id, status=3).count()
            if food < o.order_food.count():
                result_list.append(o)
        ret = 0
        try:
            ret = PayInfo.objects.get(order_id=result_list[0].id).created if len(result_list) > 0 else timezone.now()
        except PayInfo.DoesNotExist:
            ret = 0
        return round((timezone.now() - ret).seconds / 60, 0)

    def get_details(self, obj):
        detail = Order_Food.objects.filter(order__meal__id=obj.id,
                                           status=3,
                                           order__status__range=(1, 8)).order_by('created')
        detail2 = Order_Food.objects.filter(order__meal__id=obj.id,
                                            status__lt=3,
                                            order__status__range=(1, 8)).order_by('created')
        result = itertools.chain(detail, detail2)
        return KitchenFoodSerializer(result, many=True, context=self.context).data

    class Meta:
        model = Meal
        fields = (
            'meal_id', 'desk_id', 'desk_num', 'created', 'waiting_time', 'is_pay', 'finished',
            'total_food', 'details', 'refund_id', 'status', 'own_waiter', 'meal_code')


class KitChenUnFinishFoodDeskInfoSerializer(serializers.ModelSerializer):
    desk_num = serializers.CharField(source='order.meal.desk.display_number')
    total = serializers.SerializerMethodField()
    waiting_time = serializers.SerializerMethodField()

    def get_total(self, obj):
        request = self.context['request']
        ret = Order_Food.objects.filter(food_spec_id=obj.food_spec.id,
                                        order__meal__store_id=request.user.store.id,
                                        order__meal__status=0,
                                        status__lt=3,
                                        order__meal__created__range=(
                                            timezone.now() + timedelta(hours=-5), timezone.now())
                                        )
        if 'kitchen' in request.GET:
            ret = ret.filter(food__kitchen_id=request.GET.get('kitchen'))

        # ret = Meal.objects.filter(order_meal__order_food__food_spec_id=obj.food_spec.id).values('id') \
        #     .annotate(count=Sum('num'))
        result = 0
        for r in ret:
            result += r.num
        return result

    def get_waiting_time(self, obj):
        # order = Order.objects.filter(meal_id=obj.id).order_by('-created')
        # if order.count() > 0:
        #     order = order.first()
        #     pay = PayInfo.objects.filter(order_id=order.id)
        #     if pay.count() > 0:
        #         return (timezone.now() - pay.first().created).seconds / 60
        #     else:
        #         return 0
        # return 0

        order = Order.objects.filter(meal_id=obj.order.meal_id).order_by('created')
        result_list = []
        for o in order:
            food = Order_Food.objects.filter(order_id=o.id, status=3).count()
            if food < o.order_food.count():
                result_list.append(o)
        try:
            ret = PayInfo.objects.get(order_id=result_list[0].id).created if len(result_list) > 0 else timezone.now()
            return round((timezone.now() - ret).seconds / 60, 0)
        except PayInfo.DoesNotExist:
            return 0

    class Meta:
        model = Order_Food
        fields = ('desk_num', 'total', 'waiting_time')


class KitChenUnFinishFood(serializers.ModelSerializer):
    food_id = serializers.CharField(source='food.id')
    food_name = serializers.CharField(source='food.name')
    logo = serializers.ImageField(source='food.food_image.first.image')
    all_num = serializers.SerializerMethodField()
    desk_info = serializers.SerializerMethodField()
    one_spec = serializers.SerializerMethodField()

    def get_one_spec(self, obj):
        if FoodSpec.objects.filter(food_id=obj.food.id).count() > 1:
            return False
        else:
            return True

    def get_desk_info(self, obj):
        meal = Order_Food.objects.filter(food_spec_id=obj.id, order__meal__status=0, status__lt=3,
                                         order__meal__created__range=(
                                             timezone.now() + timedelta(hours=-5), timezone.now())) \
            .order_by('food_spec_id').distinct('food_spec_id')

        return KitChenUnFinishFoodDeskInfoSerializer(meal, context=self.context, many=True).data

    def get_all_num(self, obj):
        ret = Order_Food.objects.filter(food_spec_id=obj.id, order__meal__status=0, status__lt=3,
                                        order__meal__created__range=(
                                            timezone.now() + timedelta(hours=-5), timezone.now()))
        result = 0
        for r in ret:
            result += r.num
        return result

    class Meta:
        model = FoodSpec
        fields = ('id', 'name', 'food_id', 'food_name', 'logo', 'all_num', 'desk_info', 'one_spec')


class UnpayDeskSerializer(serializers.ModelSerializer):
    desk_id = serializers.CharField(source='desk.id')
    desk_num = serializers.CharField(source='desk.display_number')

    class Meta:
        model = Meal
        fields = ('desk_id', 'desk_num')


class KitChenOrderSerializer(serializers.Serializer):
    login_name = serializers.SerializerMethodField()
    unfinish_order = serializers.SerializerMethodField()
    kitchen_meal = serializers.SerializerMethodField()
    unfinish_food = serializers.SerializerMethodField()
    unpay_desk = serializers.SerializerMethodField()

    def get_login_name(self, obj):
        return self.context['request'].user.fullname

    def get_unfinish_order(self, obj):
        meal = Meal.objects.filter(created__range=(timezone.now() + timedelta(hours=-5), timezone.now()),
                                   status=0)
        result_list = []
        for m in meal:
            food_count = Order_Food.objects.filter(order__meal=m, order__status__range=(1, 8)).count()
            finish_food_count = Order_Food.objects.filter(order__meal=m, status=3, order__status__range=(1, 8)).count()
            if food_count > finish_food_count:
                result_list.append(m)

        return len(result_list)

    def get_kitchen_meal(self, obj):
        request = self.context['request']
        meal = Meal.objects.filter(created__range=(timezone.now() + timedelta(hours=-5), timezone.now()),
                                   status=0, order_meal__status__range=(1, 8), store=request.user.store).distinct()
        if 'kitchen' in request.GET:
            meal = meal.filter(order_meal__order_food__kitchen_id=request.GET.get('kitchen')).order_by('created')

        result_list1 = []
        result_list2 = []
        # 分组
        for m in meal:
            if m.is_all_finish:
                result_list1.append(m)
            else:
                result_list2.append(m)

        # 排序
        result_list2 = sorted(result_list2, key=lambda x: x.order_time, reverse=False)

        # order = order.filter(order_food__food__kitchen_id=request.GET.get('kitchen'))
        # order.order_by('created')
        result = itertools.chain(result_list1, result_list2)
        return KitChenMealSerializer(result, context=self.context, many=True).data

    def get_unfinish_food(self, obj):
        request = self.context['request']
        food_spec = FoodSpec.objects.filter(food__store_id=request.user.store_id, order_food_spec__status__lte=1,
                                            order_food_spec__order__status__range=(1, 8),
                                            order_food_spec__order__meal__status=0,
                                            order_food_spec__order__meal__created__range=(
                                                timezone.now() + timedelta(hours=-5), timezone.now())).distinct()
        # food_spec = FoodSpec.objects.filter(order_food_spec__order__meal__store__id=request.user.store_id)
        if 'kitchen' in request.GET:
            food_spec = food_spec.filter(food__kitchen_id=request.GET.get('kitchen'))

        result_list = []
        for f in food_spec:
            if f.all_num > 0:
                result_list.append(f)

        return KitChenUnFinishFood(result_list, context=self.context, many=True).data

    def get_unpay_desk(self, obj):
        request = self.context['request']
        ret = Meal.objects.filter(status=0, store_id=request.user.store_id,
                                  created__range=(timezone.now() + timedelta(hours=-5), timezone.now()))

        result_list = []

        for item in ret:

            if item.is_unpay:
                result_list.append(item)

        return UnpayDeskSerializer(result_list, context=self.context, many=True).data

    class Meta:
        fields = ('login_name', 'unfinish_order', 'kitchen_meal', 'unfinish_food', 'unpay_desk')


class OrderInMealSerializer(serializers.ModelSerializer):
    meal_id = serializers.CharField(source='id')
    desk_num = serializers.CharField(source='desk.display_number')
    meal_code = serializers.CharField(source='code')
    food_total = serializers.SerializerMethodField()
    user_total = serializers.IntegerField(source='total_user')
    total_tax = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        order = Order.objects.filter(meal_id=obj.id)
        result = True
        for o in order:
            if o.pay_time is None:
                result = False
            elif o.status == 1:
                return True
            elif o.order_food.count() == 0:
                result = False
            elif PayInfo.objects.filter(order_id=o.id).exists():
                result = False
            else:
                return True
        return result

    def get_total_tax(self, obj):
        ret = Order_Food.objects.filter(order__meal__id=obj.id)
        total_tax = 0
        for r in ret:
            total_tax += r.tax_value

        return total_tax

    def get_total_price(self, obj):
        payinfo = PayInfo.objects.filter(order__meal=obj)
        result = 0
        for p in payinfo:
            result += p.money

        return result

    def get_food_total(self, obj):
        ret = Order_Food.objects.filter(order__meal__id=obj.id)
        result = 0
        for r in ret:
            result += r.num
        return result

    class Meta:
        model = Meal
        fields = ('meal_id', 'desk_num', 'meal_code', 'food_total',
                  'total_price', 'user_total', 'status', 'total_tax', 'total_price')


class RefundOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundOrder
        fields = '__all__'


class RefundOrderViewSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name')
    store_logo = serializers.ImageField(source='store.logo')
    food_name = serializers.CharField(source='food.food.name')
    food_logo = serializers.SerializerMethodField()

    def get_food_logo(self, obj):
        ret = FoodImage.objects.filter(food_id=obj.food_id)
        if ret.exists():
            return self.context['request'].build_absolute_uri(ret.first().image.url)
        else:
            return None

    class Meta:
        model = RefundOrder
        fields = ('id',
                  'store_name', 'store_logo', 'food_name', 'food_logo', 'refund_point', 'refund_gold', 'refund_cash',
                  'status')


class RefundOrderFoodSerializer(serializers.ModelSerializer):
    food_name = serializers.CharField(source='food.name')
    food_spec = serializers.CharField(source='food_spec.name')

    class Meta:
        model = Order_Food
        fields = ('food_name', 'food_spec', 'num')


class RefundCouponCodeSerializer(serializers.ModelSerializer):
    coupon_name = serializers.CharField(source='coupon.name')

    class Meta:
        model = CouponCode
        fields = ('coupon_name', 'code')


class RefundOrderDetailSerializer(serializers.ModelSerializer):
    user_fullname = serializers.CharField(source='user.fullname')
    created = CurrentDateTimeField(format=settings.DATETIME_FORMAT)
    order_food = serializers.SerializerMethodField()
    order_code = serializers.CharField(source='order.code')
    pay_type = serializers.IntegerField(source='order.order_pay.pay_type')
    coupon = serializers.SerializerMethodField()
    desk_name = serializers.SerializerMethodField()
    store_name = serializers.CharField(source='store.name')

    def get_desk_name(self, obj):
        if obj.refund_type == 0:
            return obj.order.meal.desk.number
        else:
            return obj.food.order.meal.desk.number

    def get_coupon(self, obj):
        if obj.refund_type == 0:
            try:
                coupon_code = PayInfo.objects.get(order_id=obj.order_id).coupon_code
                return RefundCouponCodeSerializer(coupon_code).data
            except PayInfo.DoesNotExist:
                return None

    def get_order_food(self, obj):
        if obj.refund_type == 0:
            # 订单退款
            order_food = Order_Food.objects.filter(order_id=obj.order_id)
            return RefundOrderFoodSerializer(order_food, many=True).data
        else:
            order_food = Order_Food.objects.get(id=obj.food_id)
            return RefundOrderFoodSerializer(order_food).data

    class Meta:
        model = RefundOrder
        fields = ('user_fullname', 'store_name', 'created', 'process_date', 'refund_type', 'order_food', 'order_code',
                  'refund_point', 'refund_gold', 'refund_cash', 'pay_type', 'desc', 'code', 'reason',
                  'image1', 'image2', 'image3', 'image4', 'coupon', 'desk_name')


class MealOrderMealSerializer(serializers.ModelSerializer):
    meal_id = serializers.CharField(source='id')
    order = serializers.SerializerMethodField()

    def get_order(self, obj):
        order = Order.objects.filter(meal=obj, status__lt=0).order_by('created').last()
        return order.id if order.exists() else None

    class Meta:
        model = Meal
        fields = ('meal_id', 'order')


class MealOrderByStoreSerializer(serializers.ModelSerializer):
    meal_id = serializers.IntegerField(source='id')
    desk_num = serializers.CharField(source='desk.display_number')
    meal_code = serializers.CharField(source='code')
    food_total = serializers.SerializerMethodField()
    user_total = serializers.IntegerField(source='total_user')
    total_tax = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, obj):
        ret = Order.objects.filter(meal_id=obj.id)
        result = 0
        for r in ret:
            payinfo = PayInfo.objects.filter(order=r.id)
            if payinfo.exists():
                result += payinfo.first().money
        return result

    def get_total_tax(self, obj):
        ret = Order_Food.objects.filter(order__meal_id=obj.id)
        result = 0
        for r in ret:
            result += r.tax_value
        return result

    def get_food_total(self, obj):
        ret = Order_Food.objects.filter(order__meal_id=obj.id).values('id').annotate(count=Sum('num'))
        result = 0
        for r in ret:
            result += r['count']
        return result

    class Meta:
        model = Meal
        fields = ('meal_id', 'desk_num', 'meal_code', 'food_total', 'total_price', 'user_total',
                  'total_tax', 'total_price')


class MealOrderByDeskSerializer(serializers.ModelSerializer):
    meal_id = serializers.CharField(source='id')
    meal_code = serializers.CharField(source='code')
    meal_usernum = serializers.CharField(source='total_user')
    order_id = serializers.SerializerMethodField()

    def get_order_id(self, obj):
        order = Order.objects.filter(meal=obj, status__lte=1).order_by('-created').last()
        return order.id if order is not None else None

    class Meta:
        model = Meal
        fields = ('meal_id', 'meal_code', 'meal_usernum', 'order_id')


class MealByUserSerializer(serializers.ModelSerializer):
    store_id = serializers.CharField(source='store.id')
    store_name = serializers.CharField(source='store.name')
    meal_code = serializers.CharField(source='code')
    meal_id = serializers.CharField(source='id')
    class Meta:
        model = Meal
        fields = ('store_id', 'store_name', 'meal_code', 'meal_id')
