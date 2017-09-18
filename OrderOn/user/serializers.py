from django.db.models import Sum
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField, CharField, DecimalField
from rest_framework.serializers import ModelSerializer, ListSerializer
from shop.user.models import *
from django.contrib.auth import authenticate


class CurrentDateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        try:
            tz = timezone.get_default_timezone()
            # timezone.localtime() defaults to the current tz, you only
            # need the `tz` arg if the current tz != default tz
            # value = timezone.localtime(value, timezone=tz)
            # py3 notation below, for py2 do:
            # return super(CustomDateTimeField, self).to_representation(value)
            return super().to_representation(value)
        except:
            return None


class CurrentTimeField(serializers.TimeField):
    def to_representation(self, value):
        try:
            tz = timezone.get_default_timezone()
            # timezone.localtime() defaults to the current tz, you only
            # need the `tz` arg if the current tz != default tz
            # value = timezone.localtime(value, timezone=tz)
            # py3 notation below, for py2 do:
            # return super(CustomDateTimeField, self).to_representation(value)
            return super().to_representation(value)
        except:
            return None


class UploadFileFormSerializer(ModelSerializer):
    class Meta:
        model = UploadFileForm
        fields = '__all__'


class Store_IndustrySerializer(ModelSerializer):
    class Meta:
        model = Store_Industry
        fields = '__all__'


class Store_CateringSerializer(ModelSerializer):
    def to_representation(self, instance):
        return instance.name

    class Meta:
        model = Store_Catering
        fields = '__all__'


class Store_BusinessSerializer(ModelSerializer):
    class Meta:
        model = Store_Business
        fields = '__all__'


class Store_Business_TimeSerializer(ModelSerializer):
    class Meta:
        model = Store_Business_Time
        fields = '__all__'


class Store_Business_Time_FreeDaySerializer(ModelSerializer):
    class Meta:
        model = Store_Business_Time_FreeDay
        fields = '__all__'


class Store_LicenseSerializer(ModelSerializer):
    class Meta:
        model = Store_License
        fields = '__all__'


class Store_AuthSerializer(ModelSerializer):
    class Meta:
        model = Store_Auth
        fields = '__all__'


class Store_Food_SafetySerializer(ModelSerializer):
    class Meta:
        model = Store_Food_Safety
        fields = '__all__'


class StoresSerializer(ModelSerializer):
    class Meta:
        model = Stores
        fields = '__all__'


class Store_RotationSerializer(ModelSerializer):
    def to_representation(self, instance):
        return self.context['request'].build_absolute_uri(instance.rotation.url)

    class Meta:
        model = Store_Rotation
        fields = '__all__'


class Store_AdSerializer(ModelSerializer):
    def to_representation(self, instance):
        return self.context['request'].build_absolute_uri(instance.img.url)

    class Meta:
        model = Store_Ad
        fields = '__all__'


class MealStoreIndexSerializer(ModelSerializer):
    last_unpay_order_id = SerializerMethodField()
    desk_display_number = CharField(source='desk.display_number')

    def get_last_unpay_order_id(self, obj):
        ret = Order.objects.filter(meal_id=obj.id, status=0).order_by('-created')
        return ret.first().id if ret.exists() else None

    class Meta:
        model = Meal
        fields = ('id', 'desk', 'last_unpay_order_id', 'desk_display_number')


class StoreIndexSerializer(ModelSerializer):
    rotation = Store_RotationSerializer(source='store_rotation', many=True)
    store_ad = Store_AdSerializer(source='store_ad_img', many=True)
    catering = Store_CateringSerializer(many=True)
    last_normal = serializers.TimeField(source='business_time.last_normal', format='%H:%M')
    last_holiday = serializers.TimeField(source='business_time.last_holiday', format='%H:%M')
    meal = SerializerMethodField()
    queue_id = SerializerMethodField()

    def get_queue_id(self, obj):
        if self.context['request'].user.is_authenticated():
            ret = QueueLog.objects.filter(store_id=obj.id, is_use=False,
                                          queue__created__year=datetime.now().year,
                                          queue__created__month=datetime.now().month,
                                          queue__created__day=datetime.now().day, ).order_by('-queue__created')
            return ret.first().id if ret.exists() else None
        else:
            return None

    def get_meal(self, obj):
        request = self.context.get("request")
        ret = Meal.objects.filter(store_id=request.GET.get('store'), is_active=True,
                                  status=0, user__in=[request.user.id, ]).order_by(
            'created').first()
        return MealStoreIndexSerializer(ret).data if ret is not None else None

    class Meta:
        model = Stores
        fields = ('rotation', 'store_ad', 'name', 'logo', 'catering', 'last_normal', 'last_holiday', 'status', 'meal',
                  'is_queue', 'queue_id')


class StoreDetailSerializer(ModelSerializer):
    is_fav = SerializerMethodField()
    desc = CharField(source='business.desc')
    start_normal = CharField(source='business_time.start_normal')
    end_normal = CharField(source='business_time.end_normal')
    start_holiday = CharField(source='business_time.start_holiday')
    end_holiday = CharField(source='business_time.end_holiday')
    easemob_id = SerializerMethodField()

    def get_easemob_id(self, obj):
        user = AbstractUser.objects.filter(store_id=obj.id, is_basemob=True)
        if user.exists():
            return user.first().username
        else:
            return None

    def get_is_fav(self, obj):
        request = self.context.get("request")
        if request.user.is_authenticated():
            return Store_Favorite.objects.filter(user=request.user, store=obj).exists()
        else:
            return False

    class Meta:
        model = Stores
        fields = ('logo', 'name', 'in_business', 'is_fav', 'desc', 'start_normal', 'end_normal', 'tel', 'url',
                  'start_holiday', 'end_holiday', 'easemob_id')


class Store_ImageSerializer(ModelSerializer):
    # def to_representation(self, instance):
    #     return self.context['request'].build_absolute_uri(instance.img.url)

    class Meta:
        model = Store_Image
        fields = ('img',)


class Store_LobbySerializer(ModelSerializer):
    class Meta:
        model = Store_Lobby
        fields = '__all__'


class Store_KitchenSerializer(ModelSerializer):
    class Meta:
        model = Store_Kitchen
        fields = '__all__'


class Store_OtherSerializer(ModelSerializer):
    class Meta:
        model = Store_Other
        fields = '__all__'


class AbstractUserSerializer(ModelSerializer):
    class Meta:
        model = AbstractUser
        fields = '__all__'


class FoodCategorySerializer(ModelSerializer):
    class Meta:
        model = FoodCategory
        fields = ('id', 'name', 'desc','store')


class KitchenSerializer(ModelSerializer):
    class Meta:
        model = Kitchen
        exclude = ('store',)


class ReserveReturnSerializer(ModelSerializer):
    desc = SerializerMethodField()
    logo = SerializerMethodField()
    name = CharField(source='store.name', read_only=True)
    datetime = CurrentDateTimeField(format=settings.DATETIME_FORMAT)
    created = CurrentDateTimeField(format=settings.DATETIME_FORMAT)

    def get_logo(self, obj):
        return self.context['request'].build_absolute_uri(obj.store.logo.url)

    def get_desc(self, obj):
        if obj.desc is None:
            return ''
        return obj.desc

    class Meta:
        model = Reserve
        fields = (
            'id', 'desc', 'status', 'tel', 'name', 'num', 'chindren_num', 'no_smoking', 'datetime', 'created', 'store',
            'desk_category', 'logo', 'name')


class ReserveSerializer(ModelSerializer):
    class Meta:
        model = Reserve
        fields = '__all__'


class TaxSerializer(ModelSerializer):
    class Meta:
        model = Tax
        fields = '__all__'


class SellPeriodSerializer(ModelSerializer):
    class Meta:
        model = SellPeriod
        fields = '__all__'


class FoodImageSerializer(ModelSerializer):
    def to_representation(self, instance):
        return self.context['request'].build_absolute_uri(instance.image.url)

    class Meta:
        model = FoodImage
        fields = ('image',)


class TagCategorySerializer(ModelSerializer):
    class Meta:
        model = TagCategory
        fields = '__all__'


class TagSerializer(ModelSerializer):
    category = CharField(source='category.name')
    choice = CharField(source='category.choice')

    class Meta:
        model = Tag
        fields = ('id', 'name', 'category', 'choice')


class FoodWordSerializer(ModelSerializer):
    def to_representation(self, instance):
        return instance.word

    class Meta:
        model = FoodWord
        fields = ('word',)


class FoodUnitSerializer(ModelSerializer):
    class Meta:
        model = FoodUnit
        fields = '__all__'


class FoodSpecSerializer(ModelSerializer):
    # def to_representation(self, instance):
    #     return instance.name
    num = SerializerMethodField()
    price = SerializerMethodField()
    vip_price = SerializerMethodField()

    def get_price(self, obj):
        return obj.in_tax_price if obj.food.is_include_tax else obj.price

    def get_vip_price(self, obj):
        return obj.in_tax_vip_price if obj.food.is_include_tax else obj.vip_price

    def get_num(self, obj):
        if 'request' in self.context:
            if 'order' in self.context['request'].GET:
                try:
                    order_food = Order_Food.objects.filter(
                        order_id=self.context['request'].GET.get('order'),
                        food_spec_id=obj.id)
                    result = 0
                    for r in order_food:
                        result += r.num
                    return result
                except Order_Food.DoesNotExist:
                    return 0
            else:
                return 0
        return 0

    class Meta:
        model = FoodSpec
        fields = ('id', 'name', 'price', 'vip_price', 'is_default', 'num', 'stock')


class FoodCouponSerializer(ModelSerializer):
    coupon_type_value = serializers.CharField(source='get_coupon_type_display')

    class Meta:
        model = Coupon
        fields = ('id', 'coupon_type', 'coupon_type_value')


class TagFoodSerializer(serializers.ModelSerializer):
    category = CharField(source='category.name')
    choice = CharField(source='category.choice')

    class Meta:
        model = Tag
        fields = ('id', 'name', 'category', 'choice')


class AllergensSerializer(ModelSerializer):
    def to_representation(self, instance):
        return instance.name

    class Meta:
        model = Allergens
        fields = ('name',)


class FoodSerializer(ModelSerializer):
    tag = TagFoodSerializer(many=True, read_only=True)
    words = FoodWordSerializer(many=True, read_only=True)
    foodspec = SerializerMethodField()
    image = SerializerMethodField()

    coupon = SerializerMethodField()

    def get_coupon(self, obj):
        return FoodCouponSerializer(obj.coupon_food.all(), many=True, read_only=True).data

    def get_foodspec(self, obj):
        foodspec = FoodSpec.objects.filter(food_id=obj.id)
        return FoodSpecSerializer(foodspec, context={'request': self.context['request']}, many=True).data

    def get_image(self, obj):
        result = FoodImage.objects.filter(food_id=obj.id).first()
        if result is not None:
            return self.context['request'].build_absolute_uri(result.image.url)
        else:
            return ''

    class Meta:
        model = Food
        fields = ('id', 'name', 'image', 'image_size', 'desc', 'tag', 'words', 'foodspec', 'coupon', 'is_include_tax')


class FoodDetailSerializer(ModelSerializer):
    tag = TagSerializer(many=True, read_only=True)
    words = FoodWordSerializer(many=True, read_only=True)
    foodspec = SerializerMethodField()
    images = SerializerMethodField()
    allergens = AllergensSerializer(many=True, read_only=True)
    coupon = SerializerMethodField()

    def get_coupon(self, obj):
        return FoodCouponSerializer(obj.coupon_food.all(), many=True, read_only=True).data

    def get_foodspec(self, obj):
        foodspec = FoodSpec.objects.filter(food_id=obj.id)
        return FoodSpecSerializer(foodspec, context=self.context, many=True).data

    def get_images(self, obj):
        images = FoodImage.objects.filter(food_id=obj.id)
        return FoodImageSerializer(images, many=True, context=self.context).data

    class Meta:
        model = Food
        fields = ('id', 'images', 'name', 'desc', 'tag', 'words', 'foodspec', 'detail',
                  'allergens', 'calories', 'coupon')


class DeskCategorySerializer(ModelSerializer):
    class Meta:
        model = DeskCategory
        fields = '__all__'


class DeskSerializer(ModelSerializer):
    class Meta:
        model = Desk
        fields = '__all__'


class FoodCountSerializer(ModelSerializer):
    class Meta:
        model = FoodCount
        fields = '__all__'


class FoodAudioSerializer(ModelSerializer):
    class Meta:
        model = FoodAudio
        fields = '__all__'


class TagAudioSerializer(ModelSerializer):
    class Meta:
        model = TagAudio
        fields = '__all__'


class CountAudioSerializer(ModelSerializer):
    class Meta:
        model = CountAudio
        fields = '__all__'


class UnitAudioSerializer(ModelSerializer):
    class Meta:
        model = UnitAudio
        fields = '__all__'


class DeskAudioSerializer(ModelSerializer):
    class Meta:
        model = DeskAudio
        fields = '__all__'


class StoreCategorySerializer(ModelSerializer):
    class Meta:
        model = StoreCategory
        fields = '__all__'


class Store_FavoriteSerializer(ModelSerializer):
    store = StoresSerializer()

    class Meta:
        model = Store_Favorite
        fields = '__all__'


class StoreUnReserveSerializer(ModelSerializer):
    class Meta:
        model = StoreUnReserve
        fields = '__all__'


class UserGiftSerializer(ModelSerializer):
    store_id = CharField(source='store.id')
    store_name = CharField(source='store.name')
    img = SerializerMethodField()
    price = SerializerMethodField()
    food_name = CharField(source='food.food.name')
    food_id = CharField(source='food.id')
    start = CurrentDateTimeField(source='created')
    end = SerializerMethodField()

    def get_end(self, obj):
        # tz = timezone.get_default_timezone()
        value = obj.created + timezone.timedelta(days=90)
        return value.strftime('%Y-%m-%d %H:%M')

    def get_price(self, obj):
        if obj.food.food.is_include_tax:
            return obj.food.in_tax_price
        else:
            return obj.food.price

    def get_img(self, obj):
        return self.context['request'].build_absolute_uri(
            FoodImage.objects.filter(food=obj.food.food).first().image.url)

    class Meta:
        model = UserGift
        # fields = '__all__'
        exclude = ('created', 'store', 'food')
