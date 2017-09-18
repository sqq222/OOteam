from datetime import datetime

import logging
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.db.models import Max
from django.db.models.signals import post_save
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from oauth2_provider.models import Application

logger = logging.getLogger('django')


class UploadFileForm(models.Model):
    title = models.CharField(max_length=100, blank=True)
    file = models.FileField(upload_to='uploads/')

    class Meta:
        verbose_name = 'Upload'


class UserType(models.Model):
    name = models.CharField(_(u'用户类型'), max_length=20)

    class Meta:
        verbose_name = '用户类型'


class AbstractUserManager(BaseUserManager):
    def _create_user(self, username, password, is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        now = timezone.now()
        if not username:
            raise ValueError('The given username must be set.')
        user = self.model(username=username, is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, last_login=now, date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        return self._create_user(username, password, False, False, **extra_fields)

    def create_superuser(self, username, password, **extra_fields):
        return self._create_user(username, password, True, True, **extra_fields)


def create_auth_client(sender, instance=None, created=False, **kwargs):
    if created:
        Application.objects.create(user=instance, client_type=Application.CLIENT_CONFIDENTIAL,
                                   authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS)


"""
门店管理
"""


class Store_Industry(models.Model):
    """
    行业
    """
    name = models.CharField(max_length=50, verbose_name='行业')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "门店 - 行业"
        verbose_name_plural = "门店 - 行业"


class Store_Catering(models.Model):
    """
    餐饮
    """
    name = models.CharField(max_length=50, verbose_name='餐饮')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "门店 - 餐饮"
        verbose_name_plural = "门店 - 餐饮"


class Store_Business(models.Model):
    """
    门店 - 营业设置
    """
    order_tel = models.CharField(max_length=20, verbose_name='订餐电话')
    notice = models.CharField(max_length=500, verbose_name='公告')
    desc = models.CharField(max_length=500, verbose_name='简介')
    pwd = models.CharField(max_length=10, null=True, blank=True, verbose_name='菜牌密码')

    class Meta:
        verbose_name = "门店 - 营业设置"
        verbose_name_plural = "门店 - 营业设置"

    def __str__(self):
        return self.order_tel


class Store_Business_Time(models.Model):
    """
    营业时间
    """
    start_normal = models.TimeField(verbose_name='平日开店时间')
    end_normal = models.TimeField(verbose_name='平日闭店时间')
    start_holiday = models.TimeField(verbose_name='假期开店时间')
    end_holiday = models.TimeField(verbose_name='假期闭店时间')
    last_normal = models.TimeField(verbose_name='平日最后下单时间')
    last_holiday = models.TimeField(verbose_name='假期最后下单时间')
    start_rest_normal = models.TimeField(verbose_name='平日开始休息时间')
    end_rest_normal = models.TimeField(verbose_name='平日结束休息时间')
    start_rest_holiday = models.TimeField(verbose_name='假期开始休息时间')
    end_rest_holiday = models.TimeField(verbose_name='假期结束休息时间')
    monday = models.BooleanField(default=False, verbose_name="周一")
    tuesday = models.BooleanField(default=False, verbose_name="周二")
    wednesday = models.BooleanField(default=False, verbose_name="周三")
    thursday = models.BooleanField(default=False, verbose_name="周四")
    friday = models.BooleanField(default=False, verbose_name="周五")
    saturday = models.BooleanField(default=False, verbose_name="周六")
    sunday = models.BooleanField(default=False, verbose_name="周日")

    def __str__(self):
        try:
            store = Stores.objects.get(business_time_id=self.id)
            return store.name
        except Stores.DoesNotExist:
            return 'None'

    class Meta:
        verbose_name = "门店 - 营业时间"
        verbose_name_plural = "门店 - 营业时间"


class Store_Business_Time_FreeDay(models.Model):
    """
    定休日
    """
    store_business_time = models.ForeignKey(Store_Business_Time, verbose_name='营业时间属性')
    free_day = models.DateField(verbose_name='定休日')

    def __str__(self):
        return str(self.free_day)

    class Meta:
        verbose_name = "门店 - 定休日"
        verbose_name_plural = "门店 - 定休日"


class Store_License(models.Model):
    """
    营业执照
    """
    STATUS_CHOICES = (
        (1, '未审核',),
        (2, '审核中',),
        (3, '已通过',),
        (0, '审核失败',),
    )

    front = models.ImageField(upload_to='store_license')
    backend = models.ImageField(upload_to='store_license')
    business_name = models.CharField(max_length=100, verbose_name='企业名称')
    business_license = models.CharField(max_length=50, verbose_name='注册号')
    business_address = models.CharField(max_length=200, verbose_name='地址')
    business_enddate = models.DateField(null=True, blank=True, verbose_name='到期日期')
    legal_person = models.CharField(max_length=20, null=True, blank=True, verbose_name='法人')
    status = models.IntegerField(default=1, choices=STATUS_CHOICES)

    def __str__(self):
        return self.get_status_display()

    class Meta:
        verbose_name = "门店 - 营业执照"
        verbose_name_plural = "门店 - 营业执照"


class Store_Auth(models.Model):
    """
    身份认证
    """
    STATUS_CHOICES = (
        (1, '已认证',),
        (0, '未认证',),
    )

    email = models.EmailField(verbose_name='email地址')
    status = models.IntegerField(default=0, choices=STATUS_CHOICES, verbose_name='状态')

    def __str__(self):
        return self.get_status_display()

    class Meta:
        verbose_name = "门店 - 身份认证"
        verbose_name_plural = "门店 - 身份认证"


class Store_Food_Safety(models.Model):
    """
    食品安全等级
    """
    STATUS_CHOICES = (
        (1, '未审核',),
        (2, '审核中',),
        (3, '已通过',),
        (0, '审核失败',),
    )
    img = models.ImageField(upload_to='store_food_safety/')
    status = models.IntegerField(default=0, choices=STATUS_CHOICES, verbose_name='状态')

    def __str__(self):
        return self.get_status_display()

    class Meta:
        verbose_name = "门店 - 食品安全等级"
        verbose_name_plural = "门店 - 食品安全等级"


class StoreCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name='门店分类')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "门店 - 分类"
        verbose_name_plural = "门店 - 分类"


class FoodWord(models.Model):
    word = models.CharField(max_length=100, verbose_name='注目语')

    def __str__(self):
        return "{0}".format(self.word)

    class Meta:
        verbose_name = "商品 - 注目语"
        verbose_name_plural = "商品 - 注目语"


class Stores(models.Model):
    """
    门店基础信息
    """
    STATUS_CHOICES = (
        (0, '正常营业',),
        (1, '休息中',),
        (2, '停业',),
    )

    logo = models.ImageField(upload_to='logo/', verbose_name='LOGO')
    name = models.CharField(max_length=20, verbose_name='名称')
    category = models.ManyToManyField(StoreCategory, verbose_name='分类')
    address = models.CharField(max_length=100, verbose_name='地址')
    tel = models.CharField(max_length=20, verbose_name='电话')
    latitude = models.DecimalField(default=0, max_digits=6, decimal_places=3)
    longitude = models.DecimalField(default=0, max_digits=6, decimal_places=3)
    business = models.OneToOneField(Store_Business, verbose_name="营业设置")
    license = models.OneToOneField(Store_License, verbose_name="营业执照认证", null=True, blank=True)
    auth = models.OneToOneField(Store_Auth, verbose_name='身份认证', null=True, blank=True)
    send_food = models.BooleanField(default=True, verbose_name='是否送菜')
    open_menu = models.BooleanField(default=True, verbose_name='公开菜牌')
    catering = models.ManyToManyField(Store_Catering, verbose_name="餐饮", blank=True)
    industry = models.ManyToManyField(Store_Industry, verbose_name="行业", blank=True)
    food_safety = models.OneToOneField(Store_Food_Safety, verbose_name="食品安全等级", null=True, blank=True)
    business_time = models.OneToOneField(Store_Business_Time, verbose_name="营业时间", null=True, blank=True)
    principal = models.CharField(max_length=50, verbose_name='负责人')
    principal_tel = models.CharField(max_length=30, verbose_name='负责人手机')
    bank_num = models.CharField(max_length=50, null=True, blank=True, verbose_name='银行卡号')
    url = models.CharField(max_length=200, null=True, blank=True, verbose_name='网址')
    in_business = models.BooleanField(default=False, verbose_name='是否营业')
    is_active = models.BooleanField(default=True, verbose_name='是否正常')
    status = models.IntegerField(default=1, choices=STATUS_CHOICES, verbose_name='状态')
    is_queue = models.BooleanField(default=False, verbose_name='是否排队')

    class Meta:
        verbose_name = "门店 - 基础信息"
        verbose_name_plural = "门店 - 基础信息"

    def __str__(self):
        return self.name


class Store_Rotation(models.Model):
    """
    轮播图
    """
    store = models.ForeignKey(Stores, verbose_name='门店', related_name='store_rotation')
    rotation = models.ImageField(upload_to='rotation/', verbose_name="轮播图")

    def __str__(self):
        return self.rotation.url

    class Meta:
        verbose_name = "门店 - 轮播图"
        verbose_name_plural = "门店 - 轮播图"


class Store_Image(models.Model):
    """
    门店
    """
    store = models.ForeignKey(Stores)
    img = models.ImageField(upload_to='store/')

    def __str__(self):
        return self.img.url

    class Meta:
        verbose_name = "门店 - 门店图片"
        verbose_name_plural = "门店 - 门店图片"


class Store_Lobby(models.Model):
    """
    大堂
    """
    store = models.ForeignKey(Stores)
    img = models.ImageField(upload_to='store/')

    def __str__(self):
        return self.img.url

    class Meta:
        verbose_name = "门店 - 大堂图片"
        verbose_name_plural = "门店 - 大堂图片"


class Store_Kitchen(models.Model):
    """
    后厨
    """
    store = models.ForeignKey(Stores)
    img = models.ImageField(upload_to='store/')

    def __str__(self):
        return self.img.url

    class Meta:
        verbose_name = "门店 - 后厨图片"
        verbose_name_plural = "门店 - 后厨图片"


class Store_Other(models.Model):
    """
    其他
    """
    store = models.ForeignKey(Stores)
    img = models.ImageField(upload_to='store/')

    def __str__(self):
        return self.img.url

    class Meta:
        verbose_name = "门店 - 其他图片"
        verbose_name_plural = "门店 - 其他图片"


class Store_Ad(models.Model):
    """
    广告位
    """
    store = models.ForeignKey(Stores, related_name='store_ad_img')
    img = models.ImageField(upload_to='store_ad/')

    def __str__(self):
        return self.img.url

    class Meta:
        verbose_name = "门店 - 广告图片"
        verbose_name_plural = "门店 - 广告图片"


class AbstractUser(AbstractBaseUser, PermissionsMixin):
    SEX_CHOICES = (
        (1, '男',),
        (2, '女',),
        (0, '保密',),
    )
    STATUS_CHOICES = (
        (0, '激活',),
        (1, '锁定',),
    )
    username = models.CharField(_('用户名'), max_length=50, unique=True, help_text=_('请输入用户名'))
    email = models.EmailField(_('Email'), help_text=_('请输入Email'))
    code = models.CharField(max_length=10, verbose_name="激活码")
    fullname = models.CharField(
        _('姓名'), max_length=80, blank=True, null=True)
    full_name_spell = models.CharField(max_length=100, verbose_name="姓名拼写", null=True, blank=True)
    is_active = models.BooleanField(_('active'), default=False,
                                    help_text=_('指定此账号是否为活动，取消此选项，不会删除用户'))
    is_superuser = models.BooleanField(
        _('管理员'), default=False, help_text=_('指定此账号是否为后台管理员，取消此选项，该用户不能登录后台管理系统'))
    is_staff = models.BooleanField(_('员工状态'), default=False,
                                   help_text=_('指定此账号是否可以登录管理员界面'))
    user_type = models.ForeignKey(UserType, null=True, blank=True)
    date_joined = models.DateTimeField(_('注册时间'), default=timezone.now)
    sex = models.IntegerField(_('性别'), default=0, choices=SEX_CHOICES)
    birthday = models.DateField(_('生日'), null=True, blank=True)
    status = models.IntegerField(_('状态'), default=0, choices=STATUS_CHOICES)
    ip_address = models.GenericIPAddressField(_('IP地址'), null=True, blank=True)
    region = models.CharField(_('地理位置'), max_length=100, null=True, blank=True)
    address = models.CharField(max_length=200, verbose_name='地址详情', null=True, blank=True)
    store = models.ForeignKey(Stores, null=True, blank=True)
    industry = models.CharField(max_length=100, verbose_name='行业', null=True, blank=True)
    telephone = models.CharField(max_length=20, verbose_name='手机号码', null=True, blank=True)
    cardno = models.CharField(max_length=30, verbose_name='身份证号', null=True, blank=True)
    post = models.CharField(max_length=30, verbose_name='职位', null=True, blank=True)
    objects = AbstractUserManager()
    USERNAME_FIELD = 'username'

    class Meta:
        verbose_name = "账户"
        verbose_name_plural = "账户"

    def __unicode__(self):
        return "{0}".format(self.fullname)

    def get_full_name(self):
        """
        Return fullname field.
        """
        return self.fullname

    def get_short_name(self):
        """
        Return fullname field.
        """
        return self.fullname


post_save.connect(create_auth_client, sender=AbstractUser)


# ---------商品 ----------

class FoodCategory(models.Model):
    name = models.CharField(max_length=50, verbose_name="类别名称")
    desc = models.CharField(max_length=100, verbose_name="注释")
    is_display = models.BooleanField(default=True, verbose_name="是否表示")
    store = models.ForeignKey(Stores, verbose_name="店铺")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "商品 - 类别"
        verbose_name_plural = "商品 - 类别"


class Kitchen(models.Model):
    name = models.CharField(max_length=50, verbose_name="厨房")
    store = models.ForeignKey(Stores, verbose_name="店铺")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "商品 - 厨房"
        verbose_name_plural = "商品 - 厨房"


class Tax(models.Model):
    tax = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="税率")
    store = models.ForeignKey(Stores, verbose_name="店铺")

    def __str__(self):
        return str(self.tax)

    class Meta:
        verbose_name = "商品 - 税率"
        verbose_name_plural = "商品 - 税率"


class TagCategory(models.Model):
    CHOICE_CHOICES = (
        (0, '单选',),
        (1, '多选',),
    )
    store = models.ForeignKey(Stores, verbose_name="店铺")
    name = models.CharField(max_length=50, verbose_name="名称")
    desc = models.CharField(max_length=200, verbose_name="注释")
    choice = models.IntegerField(default=0, choices=CHOICE_CHOICES, verbose_name="单选/多选")

    def __str__(self):
        return "{0} - {1}".format(self.store.name, self.name)

    class Meta:
        verbose_name = "商品 - 标签类别"
        verbose_name_plural = "商品 - 标签类别"


class Tag(models.Model):
    store = models.ForeignKey(Stores, verbose_name="店铺")
    name = models.CharField(max_length=50, verbose_name="名称")
    category = models.ForeignKey(TagCategory, verbose_name="类别")

    def __str__(self):
        return "{0} - {1}".format(self.store.name, self.name)

    class Meta:
        verbose_name = "商品 - 标签"
        verbose_name_plural = "商品 - 标签"


class FoodUnit(models.Model):
    name = models.CharField(max_length=50, verbose_name="单位")

    def __str__(self):
        return "{0}".format(self.name)

    class Meta:
        verbose_name = "商品 - 商品单位"
        verbose_name_plural = "商品 - 商品单位"


class Allergens(models.Model):
    name = models.CharField(max_length=100, verbose_name='名称')

    def __str__(self):
        return "{0}".format(self.name)

    class Meta:
        verbose_name = "商品 - 过敏物质"
        verbose_name_plural = "商品 - 过敏物质"


class Food(models.Model):
    SELL_TIME_CHOICES = (
        (0, '全天',),
        (1, '限时',),
    )
    IMAGE_SIZE_CHOICES = (
        (0, '大',),
        (1, '中',),
        (2, '小',),
    )
    store = models.ForeignKey(Stores, verbose_name="店铺")
    name = models.CharField(max_length=50, verbose_name="商品名称")
    category = models.ManyToManyField(FoodCategory, verbose_name="商品类别")
    desc = models.CharField(max_length=100, null=True, blank=True, verbose_name="描述")
    kitchen = models.ForeignKey(Kitchen, verbose_name="厨房")
    tax = models.ForeignKey(Tax, verbose_name="税率")
    is_include_tax = models.BooleanField(default=True, verbose_name="是否含税")
    purchase = models.IntegerField(verbose_name="限定")
    sell_time = models.IntegerField(default=0, choices=SELL_TIME_CHOICES, verbose_name="售时")
    monday = models.BooleanField(default=False, verbose_name="周一")
    tuesday = models.BooleanField(default=False, verbose_name="周二")
    wednesday = models.BooleanField(default=False, verbose_name="周三")
    thursday = models.BooleanField(default=False, verbose_name="周四")
    friday = models.BooleanField(default=False, verbose_name="周五")
    saturday = models.BooleanField(default=False, verbose_name="周六")
    sunday = models.BooleanField(default=False, verbose_name="周日")
    # sell_period = models.ForeignKey(SellPeriod, null=True, blank=True, verbose_name="售时时间")
    # images = models.ManyToManyField(FoodImage, verbose_name="图片")
    image_size = models.IntegerField(default=1, choices=IMAGE_SIZE_CHOICES, verbose_name="图片大小")
    # price = models.DecimalField(max_digits=5, decimal_places=0, null=True, blank=True, verbose_name="价格")
    stock = models.IntegerField(default=100, null=True, blank=True, verbose_name="库存")
    is_enable = models.BooleanField(default=True, verbose_name="是否上架")
    tag = models.ManyToManyField(Tag, verbose_name="标签")
    unit = models.ForeignKey(FoodUnit, verbose_name="单位", null=True, blank=True)
    words = models.ManyToManyField(FoodWord, blank=True, verbose_name='注目语')
    detail = models.TextField(null=True, blank=True, verbose_name='商品详情')
    allergens = models.ManyToManyField(Allergens, blank=True, verbose_name='过敏物质')
    calories = models.IntegerField(default=0, verbose_name='热量')

    def __str__(self):
        return self.store.name + self.name

    class Meta:
        verbose_name = "商品 - 商品"
        verbose_name_plural = "商品 - 商品"


class SellPeriod(models.Model):
    # store = models.ForeignKey(Stores, verbose_name="店铺")
    begin = models.DateTimeField(verbose_name="开始时间")
    end = models.DateTimeField(verbose_name="结束时间")
    food = models.ForeignKey(Food, verbose_name='商品', related_name='sellperiod_food')

    def __str__(self):
        return str(self.begin) + '-' + str(self.end)

    class Meta:
        verbose_name = "商品 - 售时时间"
        verbose_name_plural = "商品 - 售时时间"


class FoodImage(models.Model):
    image = models.ImageField(upload_to="food/", verbose_name="商品图片")
    food = models.ForeignKey(Food, verbose_name='商品', related_name='food_image')

    def __str__(self):
        return self.image.url

    class Meta:
        verbose_name = "商品 - 商品图片"
        verbose_name_plural = "商品 - 商品图片"


class FoodSpec(models.Model):
    name = models.CharField(max_length=50, verbose_name="名称")
    price = models.DecimalField(max_digits=5, decimal_places=0, verbose_name="价格")
    vip_price = models.DecimalField(max_digits=5, decimal_places=0, verbose_name="会员价格")
    stock = models.IntegerField(default=-1, null=True, blank=True, verbose_name="库存")
    food = models.ForeignKey(Food, verbose_name="商品", related_name='foodspec')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')

    def __str__(self):
        return "{0} - {1}".format(self.food.name, self.name)

    class Meta:
        verbose_name = "商品 - 商品规格"
        verbose_name_plural = "商品 - 商品规格"


class DeskCategory(models.Model):
    store = models.ForeignKey(Stores, verbose_name="店铺")
    name = models.CharField(max_length=20, verbose_name="名称")
    num = models.IntegerField(verbose_name="最多人数")

    def __str__(self):
        return self.store.name + self.name

    class Meta:
        verbose_name = "商品 - 餐桌类别"
        verbose_name_plural = "商品 - 餐桌类别"


class Desk(models.Model):
    store = models.ForeignKey(Stores, verbose_name="店铺")
    number = models.CharField(max_length=20, verbose_name="桌号")
    display_number = models.CharField(max_length=20, verbose_name="显示桌号")
    category = models.ForeignKey(DeskCategory, verbose_name="类别")
    no_smoking = models.BooleanField(default=False, verbose_name="禁烟")
    is_active = models.BooleanField(default=True, verbose_name='是否正常')

    def __str__(self):
        return "{0} - {1} - {2}".format(self.store.name, self.category.name, self.display_number)

    class Meta:
        verbose_name = "商品 - 餐桌"
        verbose_name_plural = "商品 - 餐桌"


class FoodCount(models.Model):
    number = models.IntegerField(verbose_name="数量")

    def __str__(self):
        return "{0}".format(self.number)

    class Meta:
        verbose_name = "商品 - 商品数量"
        verbose_name_plural = "商品 - 商品数量"


class FoodAudio(models.Model):
    food = models.OneToOneField(Food, verbose_name="商品")
    url = models.CharField(max_length=200, verbose_name="音频路径")
    is_enable = models.BooleanField(default=True, verbose_name="是否启用")

    def __str__(self):
        return "{0} - {1}".format(self.food.name, self.url)

    class Meta:
        verbose_name = "商品 - 商品音频"
        verbose_name_plural = "商品 - 商品音频"


class TagAudio(models.Model):
    tag = models.OneToOneField(Tag, verbose_name="标签")
    url = models.CharField(max_length=200, verbose_name="音频路径")
    is_enable = models.BooleanField(default=True, verbose_name="是否启用")

    def __str__(self):
        return "{0} - {1}".format(self.tag.name, self.url)

    class Meta:
        verbose_name = "商品 - 标签音频"
        verbose_name_plural = "商品 - 标签音频"


class CountAudio(models.Model):
    count = models.OneToOneField(FoodCount, verbose_name="数量")
    url = models.CharField(max_length=200, verbose_name="音频路径")
    is_enable = models.BooleanField(default=True, verbose_name="是否启用")

    def __str__(self):
        return "{0} - {1}".format(self.count.number, self.url)

    class Meta:
        verbose_name = "商品 - 数量音频"
        verbose_name_plural = "商品 - 数量音频"


class UnitAudio(models.Model):
    unit = models.OneToOneField(FoodUnit, verbose_name="单位")
    url = models.CharField(max_length=200, verbose_name="音频路径")
    is_enable = models.BooleanField(default=True, verbose_name="是否启用")

    def __str__(self):
        return "{0} - {1}".format(self.unit.name, self.url)

    class Meta:
        verbose_name = "商品 - 单位音频"
        verbose_name_plural = "商品 - 单位音频"


class DeskAudio(models.Model):
    desk = models.OneToOneField(Desk, verbose_name="餐桌音频")
    url = models.CharField(max_length=200, verbose_name="音频路径")
    is_enable = models.BooleanField(default=True, verbose_name="是否启用")

    def __str__(self):
        return "{0} - {1}".format(self.desk.display_number, self.url)

    class Meta:
        verbose_name = "商品 - 餐桌音频"
        verbose_name_plural = "商品 - 餐桌音频"


class Reserve(models.Model):
    STATUS_CHOICES = (
        (0, '提交',),
        (1, '门店接受',),
        (2, '门店拒绝',),
        (3, '已取消',),
    )
    store = models.ForeignKey(Stores)
    status = models.IntegerField(default=0, choices=STATUS_CHOICES, verbose_name='状态')
    desk = models.ForeignKey(Desk, null=True, blank=True, verbose_name='桌号')
    user = models.ForeignKey(AbstractUser, verbose_name='预约用户')
    tel = models.CharField(max_length=20, verbose_name='手机号')
    name = models.CharField(max_length=50, verbose_name='昵称')
    desk_category = models.ForeignKey(DeskCategory, verbose_name='桌位类型')
    num = models.IntegerField(verbose_name='用餐人数')
    chindren_num = models.IntegerField(default=0, verbose_name='小孩人数')
    no_smoking = models.BooleanField(default=False, verbose_name="禁烟")
    datetime = models.DateTimeField(verbose_name='用餐时间')
    created = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    desc = models.CharField(max_length=200, null=True, blank=True, verbose_name='备注')

    def __str__(self):
        return "{0} - {1} - {2} - {3}".format(self.store.name, self.num, self.datetime, self.get_status_display())

    class Meta:
        verbose_name = "预约"
        verbose_name_plural = "预约"


class Meal(models.Model):
    STATUS_CHOICES = (
        (0, '用餐中',),
        (1, '用餐结束',),
    )
    user = models.ManyToManyField(AbstractUser, verbose_name='用餐用户')
    code = models.CharField(max_length=50, null=True, blank=True, verbose_name='订单编号')
    created = models.DateTimeField(auto_now_add=True, verbose_name='用餐时间')
    store = models.ForeignKey(Stores, verbose_name='用餐店铺')
    desk = models.ForeignKey(Desk, verbose_name='桌号')
    status = models.IntegerField(default=0, choices=STATUS_CHOICES, verbose_name='用餐状态')
    is_active = models.BooleanField(default=True, verbose_name='是否正常')

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # super(Order, self).save(*args, **kwargs)

        self.code = timezone.now().strftime(settings.CODE_DATETIME_FORMAT) \
                    + get_random_string(length=9, allowed_chars='0123456789')
        super(Meal, self).save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return "{0} - {1}".format(self.store.name, self.created)

    class Meta:
        verbose_name = '用餐'
        verbose_name_plural = '用餐'


class Order(models.Model):
    STATUS_CHOICES = (
        (0, '未支付',),
        (1, '已支付',),
        (2, '已评价',),
        (3, '申请退款',),
        (4, '已退款',),
        (5, '退款客服介入中',),
    )
    meal = models.ForeignKey(Meal, verbose_name='用餐', related_name='order_meal')
    code = models.CharField(max_length=50, verbose_name='订单编号')
    total_price = models.DecimalField(default=0, max_digits=5, decimal_places=0, verbose_name="总价")
    created = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    status = models.IntegerField(choices=STATUS_CHOICES, default=0, verbose_name='状态')
    is_active = models.BooleanField(default=True, verbose_name='是否正常')

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # super(Order, self).save(*args, **kwargs)

        self.code = timezone.now().strftime(settings.CODE_DATETIME_FORMAT) \
                    + get_random_string(length=9, allowed_chars='0123456789')
        super(Order, self).save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return "{0} - {1} - {2}".format(self.code, self.meal.store.name,
                                        self.created.strftime(settings.DATETIME_FORMAT))

    class Meta:
        verbose_name = "订单"
        verbose_name_plural = "订单"


class Order_Food(models.Model):
    order = models.ForeignKey(Order, verbose_name='订单', related_name='order_food')
    food = models.ForeignKey(Food, verbose_name='商品')
    food_spec = models.ForeignKey(FoodSpec, verbose_name='商品规格')
    num = models.IntegerField(verbose_name='数量')
    tag = models.ManyToManyField(Tag, verbose_name='标签')
    price = models.DecimalField(max_digits=5, decimal_places=0, verbose_name="价格")
    desc = models.CharField(max_length=100, null=True, blank=True, verbose_name='备注')
    is_active = models.BooleanField(default=True, verbose_name='是否正常')
    created = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.price = self.food_spec.price * Decimal(self.num)
        super(Order_Food, self).save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return self.food.name

    class Meta:
        verbose_name = "订单 - 商品"
        verbose_name_plural = "订单 - 商品"


class Order_Food_Comment(models.Model):
    order_food = models.OneToOneField(Order_Food, verbose_name='订单商品', related_name='order_food')
    food_star = models.IntegerField(verbose_name='评级')
    comment = models.CharField(max_length=200, verbose_name='评价')

    def __str__(self):
        return "{0} - {1} - {2}星".format(self.order_food.order.code, self.order_food.food.name, self.food_star)

    class Meta:
        verbose_name = "订单 - 商品评价"
        verbose_name_plural = "订单 - 商品评价"


class Order_Food_Comment_Image(models.Model):
    img = models.ImageField(upload_to='food_comment_img/', verbose_name='图片')
    order_food_comment = models.ForeignKey(Order_Food_Comment)

    def __str__(self):
        return self.img

    class Meta:
        verbose_name = "订单 - 商品评价图片"
        verbose_name_plural = "订单 - 商品评价图片"


class Order_Comment(models.Model):
    order = models.OneToOneField(Order, verbose_name='订单')
    order_star = models.IntegerField(verbose_name='星级')
    comment = models.CharField(max_length=100, verbose_name='评价')

    def __str__(self):
        return "{0} - {1}星".format(self.order.code, self.order_star)

    class Meta:
        verbose_name = "订单 - 评价"


class Order_Comment_Image(models.Model):
    img = models.ImageField(upload_to='comment_img/', verbose_name='图片')
    order_comment = models.ForeignKey(Order_Comment, verbose_name='订单评价')

    def __str__(self):
        return "{0} - {1}星".format(self.order_comment.order.code, self.order_comment)

    class Meta:
        verbose_name = "订单 - 评价图片"


class Store_Favorite(models.Model):
    user = models.ForeignKey(AbstractUser, verbose_name='用户')
    store = models.ForeignKey(Stores, verbose_name='门店')

    def __str__(self):
        return "{0} - {1}".format(self.user.fullname, self.store.name)

    class Meta:
        verbose_name = "用户收藏夹"
        verbose_name_plural = "用户收藏夹"
        ordering = ['id']


class StoreUnReserve(models.Model):
    store = models.ForeignKey(Stores, verbose_name='门店')
    begin = models.DateTimeField(verbose_name='开始时间')
    end = models.DateTimeField(verbose_name='结束时间')

    def __str__(self):
        return "{0} - {1} - {2}".format(self.store.name, self.begin, self.end)

    class Meta:
        verbose_name = "门店 - 停止预约时间段"
        verbose_name_plural = "门店 - 停止预约时间段"


class Coupon(models.Model):
    TYPE_CHOICES = (
        (0, '单品打折',),
        (1, '满减打折',),
        (2, '均一价格',),
    )
    STATUS_CHOICES = (
        (0, '正常',),
        (1, '仅参与',),
        (2, '已删除',),
    )
    store = models.ForeignKey(Stores, verbose_name='门店')
    status = models.IntegerField(default=0, choices=STATUS_CHOICES, verbose_name='状态')
    name = models.CharField(max_length=50, verbose_name='名称')
    code = models.CharField(max_length=20, verbose_name='代码')
    start = models.DateTimeField(verbose_name='开始时间')
    end = models.DateTimeField(verbose_name='结束时间')
    coupon_type = models.IntegerField(choices=TYPE_CHOICES, verbose_name='优惠券类型')
    category = models.ManyToManyField(FoodCategory, blank=True, verbose_name='打折类别')
    food = models.ManyToManyField(Food, blank=True, verbose_name='打折商品', related_name='coupon_food')
    notice_before = models.IntegerField(verbose_name='提前通知天数')
    notice_content = models.CharField(max_length=200, verbose_name='通知内容')
    detail_master = models.CharField(max_length=200, verbose_name='优惠券详情 - 主')
    detail_minor = models.TextField(null=True, blank=True, verbose_name='优惠券详情 - 次')
    slogan = models.CharField(max_length=300, verbose_name='口号')
    start_show = models.DateTimeField(verbose_name='展示时间')
    count = models.IntegerField(null=True, blank=True, verbose_name='发放张数')
    daily_limit = models.IntegerField(null=True, blank=True, verbose_name='每日每人限额')
    single_limit = models.IntegerField(null=True, blank=True, verbose_name='单人限额')
    background = models.ImageField(upload_to='coupon_backgroud/', null=True, blank=True, verbose_name='背景图片')
    show_img = models.ImageField(upload_to='show_img/', null=True, blank=True, verbose_name='展示图')
    is_receive = models.BooleanField(default=True, verbose_name='是否需要领取')
    desc = models.CharField(max_length=100, null=True, blank=True, verbose_name='备注')

    def __str__(self):
        return "{0} - {1}".format(self.store.name, self.name)

    def save(self, *args, **kwargs):
        super(Coupon, self).save(*args, **kwargs)
        count = self.count
        from django.utils.crypto import get_random_string

        couponcode_list = []
        for e in range(count):
            code = get_random_string(length=9, allowed_chars='0123456789')
            couponcode_list.append(CouponCode(code=code, coupon=self))
        CouponCode.objects.bulk_create(couponcode_list)

    class Meta:
        verbose_name = "优惠券 - 优惠券"
        verbose_name_plural = "优惠券 - 优惠券"


class DiscountCoupon(models.Model):
    TYPE_CHOICES = (
        (0, '定额',),
        (1, '折扣',),
        (2, '满赠',),
    )
    coupon = models.OneToOneField(Coupon, verbose_name='优惠券', related_name='discount')
    coupon_type = models.IntegerField(default=0, choices=TYPE_CHOICES, verbose_name='折扣类型')
    quota = models.IntegerField(default=0, null=True, blank=True, verbose_name='定额优惠金额')
    discount = models.IntegerField(default=0, blank=True, verbose_name='折扣')
    more_gift = models.IntegerField(default=0, blank=True, verbose_name='满赠个数')
    gift = models.OneToOneField(Food, null=True, blank=True, verbose_name='赠品')
    num = models.IntegerField(default=0, verbose_name='赠品数量')
    unit = models.CharField(max_length=20, null=True, blank=True, verbose_name='单位')

    def __str__(self):
        return "{0} - 折扣优惠券".format(self.coupon.name)

    class Meta:
        verbose_name = "优惠券 - 折扣优惠券"
        verbose_name_plural = "优惠券 - 折扣优惠券"


class FullMinusCoupon(models.Model):
    TYPE_CHOICES = (
        (0, '减',),
        (1, '赠商品',),
        (2, '赠会员点',),
    )
    coupon = models.OneToOneField(Coupon, verbose_name='优惠券', related_name='fullminus')
    full = models.IntegerField(verbose_name='满')
    coupon_type = models.IntegerField(choices=TYPE_CHOICES, verbose_name='促销方式')
    minus = models.IntegerField(default=0, verbose_name='减')
    gift = models.ForeignKey(Food, blank=True, verbose_name='赠品')
    num = models.IntegerField(default=0, verbose_name='数量')
    point = models.IntegerField(default=0, verbose_name='赠会员点')

    def __str__(self):
        return "{0} - 满减优惠券".format(self.coupon.name)

    class Meta:
        verbose_name = "优惠券 - 满减优惠券"
        verbose_name_plural = "优惠券 - 满减优惠券"


class UniteCoupon(models.Model):
    TYPE_CHOICES = (
        (0, '系列均一',),
        (1, '多选均一',),
    )
    coupon = models.OneToOneField(Coupon, verbose_name='优惠券', related_name='unite')
    coupon_type = models.IntegerField(choices=TYPE_CHOICES, verbose_name='类型')
    category_price = models.IntegerField(default=0, verbose_name='系列均一价格')
    select = models.IntegerField(default=0, verbose_name='选')
    price = models.IntegerField(default=0, verbose_name='多选均一价格')
    unit = models.CharField(max_length=20, null=True, blank=True, verbose_name='单位')

    def __str__(self):
        return "{0} - 均一优惠券".format(self.coupon.name)

    class Meta:
        verbose_name = "优惠券 - 均一价格"
        verbose_name_plural = "优惠券 - 均一价格"


class CouponTime(models.Model):
    coupon = models.OneToOneField(Coupon, verbose_name='优惠券', related_name='coupon_time')
    monday = models.BooleanField(default=False, verbose_name="周一")
    tuesday = models.BooleanField(default=False, verbose_name="周二")
    wednesday = models.BooleanField(default=False, verbose_name="周三")
    thursday = models.BooleanField(default=False, verbose_name="周四")
    friday = models.BooleanField(default=False, verbose_name="周五")
    saturday = models.BooleanField(default=False, verbose_name="周六")
    sunday = models.BooleanField(default=False, verbose_name="周日")
    start = models.DateTimeField(verbose_name='开始时间')
    end = models.DateTimeField(verbose_name='结束时间')

    def __str__(self):
        return "{0} - {1} - {2}".format(self.coupon.name, self.start, self.end)

    class Meta:
        verbose_name = "优惠券 - 有效期"
        verbose_name_plural = "优惠券 - 有效期"


class CouponCode(models.Model):
    coupon = models.ForeignKey(Coupon, verbose_name='优惠券')
    is_receive = models.BooleanField(default=False, verbose_name='是否领取')
    receive_user = models.ForeignKey(AbstractUser, blank=True, null=True, verbose_name='领取用户')
    receive_time = models.DateTimeField(blank=True, null=True, verbose_name='领取时间')
    is_use = models.BooleanField(default=False, verbose_name='是否使用')
    code = models.CharField(max_length=30, verbose_name='优惠券码')

    def __str__(self):
        return "{0} - {1}".format(self.coupon.get_coupon_type_display(), self.code)

    class Meta:
        verbose_name = "优惠券码"
        verbose_name_plural = "优惠券码"


class PayInfo(models.Model):
    TYPE_CHOICES = (
        (0, '线上支付',),
        (1, '线下支付',),
    )
    order = models.OneToOneField(Order, verbose_name='订单', related_name='order_pay')
    user = models.ForeignKey(AbstractUser, verbose_name='用户')
    pay_type = models.IntegerField(default=0, choices=TYPE_CHOICES, verbose_name='方式')
    coupon_code = models.OneToOneField(CouponCode, verbose_name='优惠券', null=True, blank=True)
    money = models.IntegerField(verbose_name='支付总额')
    card_pay = models.IntegerField(default=0, verbose_name='银行卡支付')
    alipay_pay = models.IntegerField(default=0, verbose_name='支付宝支付')
    point_pay = models.IntegerField(default=0, verbose_name='会员点支付')
    gold_pay = models.IntegerField(default=0, verbose_name='金币支付')

    def __str__(self):
        return "{0} - {1} - {2}".format(self.order.code, self.get_pay_type_display(), self.money)

    class Meta:
        verbose_name = '支付信息'
        verbose_name_plural = '支付信息'


class Queue(models.Model):
    store = models.ForeignKey(Stores, verbose_name='店铺')
    desk_category = models.ForeignKey(DeskCategory, null=True, blank=True, verbose_name='桌位类型')
    num = models.IntegerField(verbose_name='大人')
    chindren_num = models.IntegerField(default=0, verbose_name='小孩人数')
    no_smoking = models.BooleanField(default=False, verbose_name="禁烟")
    created = models.DateTimeField(auto_now_add=True, verbose_name='领取时间')

    def __str__(self):
        return "{0} - {1} - 大人{2}人 - 小孩{3}人 - 禁烟:{4}".format(self.store.name, self.desk_category.name, self.num,
                                                             self.chindren_num, self.no_smoking)

    class Meta:
        verbose_name = '排队'
        verbose_name_plural = '排队'


class QueueLog(models.Model):
    store = models.ForeignKey(Stores, verbose_name='店铺')
    queue = models.OneToOneField(Queue)
    code = models.IntegerField(default=0, verbose_name='排号')
    is_use = models.BooleanField(default=False, verbose_name='是否用餐')

    def __str__(self):
        return "{0} - {1}".format(self.queue, self.code)

    class Meta:
        verbose_name = '排队记录'
        verbose_name_plural = '排队记录'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # super(Order, self).save(*args, **kwargs)
        ret = QueueLog.objects.filter(store_id=self.store_id, queue__created__year=datetime.now().year,
                                      queue__created__month=datetime.now().month,
                                      queue__created__day=datetime.now().day).aggregate(Max('code'))

        self.code = ret['code__max'] + 1 if ret['code__max'] is not None else 1
        super(QueueLog, self).save(force_insert, force_update, using, update_fields)


class StorePointLog(models.Model):
    store = models.ForeignKey(Stores, verbose_name='门店')
    user = models.ForeignKey(AbstractUser, verbose_name='用户')
    recharge_point = models.IntegerField(verbose_name='充值会员点')
    current_point = models.IntegerField(verbose_name='剩余会员点')
    created = models.DateTimeField(auto_now_add=True, verbose_name='充值时间')

    class Meta:
        verbose_name_plural = '会员点充值'
        verbose_name = '会员点充值'

    def __str__(self):
        return "{0} - {1} - {2}".format(self.store, self.recharge_point, self.created)


class GoldLog(models.Model):
    user = models.ForeignKey(AbstractUser, verbose_name='用户')
    recharge_gold = models.IntegerField(verbose_name='充值金币')
    current_gold = models.IntegerField(verbose_name='剩余金币')
    created = models.DateTimeField(auto_now_add=True, verbose_name='充值时间')

    class Meta:
        verbose_name_plural = '金币充值'
        verbose_name = '金币充值'

    def __str__(self):
        return "{0} - {1}".format(self.recharge_gold, self.created)
