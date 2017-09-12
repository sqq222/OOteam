import base64

import oauth2_provider
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.validators import RegexValidator
from django.db.models import Sum
from rest_framework import serializers
from rest_framework.fields import CharField
from rest_framework.validators import UniqueValidator

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
        tz = timezone.get_default_timezone()
        # timezone.localtime() defaults to the current tz, you only
        # need the `tz` arg if the current tz != default tz
        value = timezone.localtime(value, timezone=tz)
        # py3 notation below, for py2 do:
        # return super(CustomDateTimeField, self).to_representation(value)
        return super().to_representation(value)


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

    class Meta:
        model = AbstractUser
        fields = ('id', 'username', 'fullname', 'sex', 'birthday', 'telephone')


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
    def to_representation(self, instance):
        return instance.name

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
        # 是否发放完毕
        if CouponCode.objects.filter(coupon=obj, is_receive=True).count() >= obj.count:
            return False
        # 是否有request
        if 'request' not in self.context:
            return False
        # 是否登录
        if self.context['request'].user is not None:
            # 是否超过单人限额
            user_coupon = CouponCode.objects.filter(coupon=obj, receive_user=self.context['request'].user)
            if user_coupon.count() >= obj.single_limit:
                return False
            # 是否超过每人每日限额
            receive_count = CouponCode.objects.filter(coupon=obj, receive_time__year=datetime.now().year,
                                                      receive_time__month=datetime.now().month,
                                                      receive_time__day=datetime.now().day,
                                                      receive_user=self.context['request'].user).count()
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
                  'is_all_food', 'category', 'food', 'is_receive','can_receive')


class CouponCodeSerializer(serializers.ModelSerializer):
    receive_time = CurrentDateTimeField(format=settings.DATETIME_FORMAT)
    coupon = CouponSerializer()

    class Meta:
        model = CouponCode
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return instance.name

    class Meta:
        model = Tag
        fields = ('name',)


class OrderFoodCreateSerializer(serializers.ModelSerializer):
    tag = TagSerializer(many=True)
    food = serializers.CharField(source='food.name')
    food_spec = serializers.CharField(source='food_spec.name')

    class Meta:
        model = Order_Food
        fields = '__all__'


class OrderFoodSerializer(serializers.ModelSerializer):
    food_name = serializers.CharField(source='food.name')
    food_spec = serializers.CharField(source='food_spec.name')
    food_id = serializers.CharField(source='food.id')
    food_is_include_tax = serializers.BooleanField(source='food.is_include_tax')
    tax = serializers.SerializerMethodField()
    vip_tax = serializers.SerializerMethodField()
    img = serializers.SerializerMethodField()
    tags = TagSerializer(source='tag', many=True, read_only=True)
    food_vip_price = serializers.CharField(source='food_spec.vip_price')
    food_price = serializers.CharField(source='food_spec.price')

    def get_tax(self, obj):
        if obj.food.is_include_tax:
            # 商品价格含税
            return int(round(obj.food_spec.price - (obj.food_spec.price / (1 + obj.food.tax.tax / 100)), 0))
        else:
            return int(round(obj.food_spec.price * (obj.food.tax.tax / 100), 0))

    def get_vip_tax(self, obj):
        if obj.food.is_include_tax:
            # 商品价格含税
            return int(round(obj.food_spec.vip_price - (obj.food_spec.vip_price / (1 + obj.food.tax.tax / 100)), 0))
        else:
            return int(round(obj.food_spec.vip_price * (obj.food.tax.tax / 100), 0))

    def get_img(self, obj):
        img = FoodImage.objects.filter(food=obj.food).first()
        if img is None:
            return None
        else:
            return self.context['request'].build_absolute_uri(img.image.url)

    class Meta:
        model = Order_Food
        fields = (
            'id', 'food_name', 'food_id', 'food_spec', 'img', 'tags', 'desc', 'food_vip_price', 'food_price', 'num',
            'price', 'food_is_include_tax', 'tax', 'vip_tax')


class OrderSerializer(serializers.ModelSerializer):
    created = CurrentDateTimeField(format=settings.DATETIME_FORMAT)
    detail = OrderFoodSerializer(source='order_food', many=True)

    class Meta:
        model = Order
        fields = ('id', 'code', 'total_price', 'created', 'status', 'meal', 'detail', 'waiter')


class MealSerializer(serializers.ModelSerializer):
    created = CurrentDateTimeField(format=settings.DATETIME_FORMAT)
    store_id = serializers.CharField(source='store.id')
    store_name = serializers.CharField(source='store.name')
    desk_id = serializers.CharField(source='desk.id')
    desk_number = serializers.CharField(source='desk.number')
    order = OrderSerializer(source='order_meal', many=True)

    class Meta:
        model = Meal
        fields = ('id', 'code', 'created', 'store_id', 'store_name', 'desk_id', 'desk_number', 'order')


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

    def get_food_count(self, obj):
        ret = Order_Food.objects.values('order').filter(order_meal__id=obj.id).annotate(count=Sum('num'))
        return ret[0]['count'] if ret.count() > 0 else 0

    def get_store_logo(self, obj):

        if obj.store.logo is None:
            return None
        else:
            return self.context['request'].build_absolute_uri(obj.store.logo.url)

    class Meta:
        model = Meal
        fields = ('id', 'code', 'created', 'store_id', 'store_logo', 'store_name', 'desk_id', 'desk_number', 'order',
                  'food_count')


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

    # password = CharField(max_length=128, write_only=True, error_messages={'required': 'Password'})
    # username = CharField(error_messages={'required': 'Username'},
    #                      max_length=30,
    #                      validators=[RegexValidator(),
    #                                  UniqueValidator(queryset=AbstractUser.objects.all(), message='Username taken')])
    # email = CharField(allow_blank=True, allow_null=True, max_length=75, required=True,
    #                   validators=[UniqueValidator(queryset=AbstractUser.objects.all(), message='Email taken')])

    class Meta(LoginSerializer.Meta):
        fields = ('order', 'food', 'food_spec', 'num', 'tag', 'price', 'desc')
