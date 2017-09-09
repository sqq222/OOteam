from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .forms import AbstractUserChangeForm, AbstractUserCreationForm
from .models import *


admin.site.site_header = 'OrderOn 后台总控系统'
admin.site.site_title = 'OrderOn 后台总控系统'

class AbstractUserAdmin(UserAdmin):
    form = AbstractUserChangeForm
    add_form = AbstractUserCreationForm

    list_display = ('username', 'fullname', 'email', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password', 'user_type')}),
        (_('Personal Info'), {'fields': ('img', 'fullname', 'sex', 'store', 'full_name_spell', 'date_joined',
                                         'birthday', 'status', 'region', 'address', 'industry', 'telephone', 'cardno',
                                         'post', 'code', 'is_basemob')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff',
                                       'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined',)}),
    )
    filter_horizontal = ('user_permissions',)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'sex', 'status', 'password1', 'password2')}
         ),
    )

    search_fields = ('username', 'fullname')
    ordering = ('username', 'date_joined')


class StoreRotationInline(admin.TabularInline):
    model = Store_Rotation
    extra = 3


class StoreImageInline(admin.TabularInline):
    model = Store_Image
    extra = 3


class StoreLobbyInline(admin.TabularInline):
    model = Store_Lobby
    extra = 3


class StoreKitchenInline(admin.TabularInline):
    model = Store_Kitchen
    extra = 3


class StoreOtherInline(admin.TabularInline):
    model = Store_Other
    extra = 3


class StoreAdInline(admin.TabularInline):
    model = Store_Ad
    extra = 3


class StoreUnReserveInline(admin.TabularInline):
    model = StoreUnReserve
    extra = 3


class StoreLicenseInLine(admin.TabularInline):
    model = Store_License
    extra = 1

class StoreAdmin(admin.ModelAdmin):
    fields = ('logo', 'name', 'category', 'address', 'tel', 'license', 'auth', 'send_food',
              'open_menu', 'catering', 'industry', 'food_safety', 'business', 'business_time', 'principal',
              'principal_tel',
              'bank_num', 'url', 'in_business', 'status', 'is_queue')
    inlines = [StoreRotationInline, StoreAdInline, StoreImageInline, StoreLobbyInline, StoreKitchenInline,
               StoreOtherInline, StoreUnReserveInline] # StoreLicenseInLine
    # exclude = ('catering',)
    filter_horizontal = ('catering', 'industry', 'category')
    list_display = ('name', 'tel', 'license', 'auth', 'send_food',
                    'open_menu', 'principal', 'principal_tel',)
    list_filter = ['send_food', 'open_menu']
    search_fields = ['name', 'tel', 'address', 'principal', 'principal_tel', 'bank_num']


class FoodImageInline(admin.TabularInline):
    model = FoodImage
    extra = 3


class FoodApecInline(admin.TabularInline):
    model = FoodSpec
    extra = 1


class SellPeriodInline(admin.TabularInline):
    model = SellPeriod
    extra = 1


class FoodAdmin(admin.ModelAdmin):
    fields = (
        'store', 'name', 'category', 'desc', 'kitchen', 'tax', 'is_include_tax', 'purchase', 'sell_time', 'monday',
        'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'image_size',
        'is_enable', 'tag', 'unit', 'words', 'detail', 'allergens', 'calories')
    inlines = [FoodImageInline, FoodApecInline, SellPeriodInline]
    filter_horizontal = ('tag', 'words', 'allergens', 'category')
    list_filter = ('sell_time',)


class StoreBusinessTimeFreeDayInline(admin.TabularInline):
    model = Store_Business_Time_FreeDay
    extra = 3


class BusinessTimeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['start_normal', 'end_normal', 'start_holiday', 'end_holiday', 'last_normal', 'last_holiday',
                           'start_rest_normal', 'end_rest_normal', 'start_rest_holiday', 'end_rest_holiday']}),
        ('定休日(星期)', {'fields': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']})
    ]
    inlines = [StoreBusinessTimeFreeDayInline]


class FullMinusCouponInLine(admin.StackedInline):
    model = FullMinusCoupon
    extra = 0


class UniteCouponInLine(admin.StackedInline):
    model = UniteCoupon
    extra = 0


class DiscountCouponInLine(admin.StackedInline):
    model = DiscountCoupon
    # filter_horizontal = ('gift',)
    extra = 0


class CouponTimeInLine(admin.TabularInline):
    model = CouponTime
    extra = 0


class CouponCodeInLine(admin.TabularInline):
    model = CouponCode
    readonly_fields = ('id', 'code', 'is_receive', 'receive_user', 'receive_time', 'is_use')
    can_delete = False
    extra = 0


class CouponForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CouponForm, self).__init__(*args, **kwargs)
        wtf = FoodCategory.objects.filter(store_id=self.instance.store_id)
        w = self.fields['category'].widget
        choices = []
        for choice in wtf:
            choices.append((choice.id, choice.name))
        w.choices = choices

        wtf = Food.objects.filter(store_id=self.instance.store_id)
        w = self.fields['food'].widget
        choices = []
        for choice in wtf:
            choices.append((choice.id, choice.name))
        w.choices = choices


class CouponAdmin(admin.ModelAdmin):
    fields = (
        'store', 'code', 'status', 'name', 'start', 'end', 'coupon_type', 'category', 'food', 'notice_before',
        'notice_content', 'detail_master', 'detail_minor', 'slogan', 'start_show', 'count', 'daily_limit',
        'single_limit', 'is_receive','background','show_img','display_background')
    inlines = [CouponTimeInLine, DiscountCouponInLine, FullMinusCouponInLine, UniteCouponInLine, CouponCodeInLine]
    # CouponCodeInLine
    filter_horizontal = ('category', 'food')

    form = CouponForm


class StorePointAdmin(admin.ModelAdmin):
    filter_horizontal = ('store',)


class PayInfoInLine(admin.TabularInline):
    model = PayInfo
    readonly_fields = ('order', 'coupon_code', 'money', 'card_pay', 'alipay_pay', 'point_pay', 'gold_pay',
                       'user','pay_type','money_pay','code','limit_price')
    can_delete = False
    extra = 1


class OrderFoodInLine(admin.StackedInline):
    model = Order_Food
    extra = 0
    filter_horizontal = ('tag',)


class OrderAdmin(admin.ModelAdmin):
    fields = ('meal', 'total_price', 'status', 'code', 'created', 'is_active')
    readonly_fields = ('code', 'created', 'total_price', 'is_active')
    inlines = [OrderFoodInLine, PayInfoInLine]
    #
    # def get_readonly_fields(self, request, obj=None):
    #     return list(self.readonly_fields) + \
    #            [field.name for field in obj._meta.fields] + \
    #            [field.name for field in obj._meta.many_to_many]


class MealAdmin(admin.ModelAdmin):
    filter_horizontal = ('user',)


class StoreCategoryResource(resources.ModelResource):
    # name = fields.Field(column_name='name')

    class Meta:
        model = StoreCategory
        fields = ('id', 'name',)


class StoreCategoryAdmin(ImportExportModelAdmin):
    resource_class = StoreCategoryResource


class GoldLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'recharge_gold', 'store', 'current_gold', 'created')


class StorePayTypeAdmin(admin.ModelAdmin):
    list_display = ('store', 'cash', 'point', 'gold', 'third_party', 'alipay')


admin.site.register(AbstractUser, AbstractUserAdmin)
# admin.site.unregister(Group)
admin.site.register(StoreCategory, StoreCategoryAdmin)
admin.site.register(Store_Industry)
admin.site.register(Store_Catering)
admin.site.register(Store_Business)
admin.site.register(Store_Business_Time, BusinessTimeAdmin)
admin.site.register(Store_Business_Time_FreeDay)
admin.site.register(Store_License)
admin.site.register(Store_Auth)
admin.site.register(Store_Food_Safety)
admin.site.register(Stores, StoreAdmin)
admin.site.register(Store_Rotation)
admin.site.register(Store_Image)
admin.site.register(Store_Lobby)
admin.site.register(Store_Kitchen)
admin.site.register(Store_Other)
admin.site.register(Store_Ad)
admin.site.register(FoodCategory)
admin.site.register(Kitchen)
admin.site.register(Tax)
admin.site.register(SellPeriod)
admin.site.register(FoodImage)
admin.site.register(Food, FoodAdmin)
admin.site.register(FoodSpec)
admin.site.register(FoodUnit)
admin.site.register(TagCategory)
admin.site.register(Tag)
admin.site.register(DeskCategory)
admin.site.register(Desk)
admin.site.register(FoodCount)
admin.site.register(FoodAudio)
admin.site.register(TagAudio)
admin.site.register(CountAudio)
admin.site.register(UnitAudio)
admin.site.register(DeskAudio)
admin.site.register(Reserve)
admin.site.register(Store_Favorite)
admin.site.register(FoodWord)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Meal, MealAdmin)
admin.site.register(Allergens)
admin.site.register(Queue)
admin.site.register(QueueLog)
admin.site.register(StorePointLog)
admin.site.register(GoldLog, GoldLogAdmin)
admin.site.register(PayInfo)
admin.site.register(RefundOrder)
admin.site.register(UserGift)
admin.site.register(StorePoint, StorePointAdmin)
admin.site.register(StorePayType, StorePayTypeAdmin)
