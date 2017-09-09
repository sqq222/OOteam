from django.apps import AppConfig
from suit.apps import DjangoSuitConfig
from suit.menu import ParentItem, ChildItem


class UserConfig(AppConfig):
    name = 'user'


class SuitConfig(DjangoSuitConfig):
    layout = 'vertical'

    menu = (
        ParentItem(
            '账户管理',
            children=[
                ChildItem(model='user.abstractuser', label='账户'),
                ChildItem(model='auth.group', label='用户组'),
            ]),
        ParentItem(
            '门店管理',
            children=[
                ChildItem(model='user.stores', label='门店信息'),
                ChildItem(model='user.storecategory', label='门店分类'),
                ChildItem(model='user.store_license'),
                ChildItem(model='user.store_business_time_freeday'),
                ChildItem(model='user.store_business_time'),
                ChildItem(model='user.store_business'),
                ChildItem(model='user.store_food_safety'),
                ChildItem(model='user.store_rotation'),
                ChildItem(model='user.store_image'),
                ChildItem(model='user.store_lobby'),
                ChildItem(model='user.store_kitchen'),
                ChildItem(model='user.store_other'),
                ChildItem(model='user.store_ad'),
                ChildItem(model='user.storepaytype'),
                ChildItem(model='user.deskcategory'),
                ChildItem(model='user.desk'),
                ChildItem(model='user.storeunreserve'),
                ChildItem(model='user.storepaytype'),
                ChildItem(model='user.store_industry'),
            ]),
        ParentItem(
            '商品管理',
            children=[
                ChildItem(model='user.foodcategory'),
                ChildItem(model='user.kitchen'),
                ChildItem(model='user.tax'),
                ChildItem(model='user.tagcategory'),
                ChildItem(model='user.tag'),
                ChildItem(model='user.foodunit'),
                ChildItem(model='user.allergens'),
                ChildItem(model='user.food'),
                ChildItem(model='user.sellperiod'),
                ChildItem(model='user.foodimage'),
                ChildItem(model='user.foodspec'),
                ChildItem(model='user.foodcount'),
            ]),
        ParentItem(
            '音频管理',
            children=[
                ChildItem(model='user.foodaudio'),
                ChildItem(model='user.tagaudio'),
                ChildItem(model='user.countaudio'),
                ChildItem(model='user.unitaudio'),
                ChildItem(model='user.deskaudio'),
            ]),
        ParentItem(
            '预约管理',
            children=[
                ChildItem(model='user.reserve'),
            ]),
        ParentItem(
            '用餐管理',
            children=[
                ChildItem(model='user.meal'),
            ]),
        ParentItem(
            '订单管理',
            children=[
                ChildItem(model='user.order'),
                ChildItem(model='user.order_food'),
                ChildItem(model='user.order_food_comment'),
                ChildItem(model='user.order_comment'),
            ]),
        ParentItem(
            '收藏管理',
            children=[
                ChildItem(model='user.store_favorite'),
            ]),
        ParentItem(
            '优惠券管理',
            children=[
                ChildItem(model='user.coupon'),
                ChildItem(model='user.discountcoupon'),
                ChildItem(model='user.fullminuscoupon'),
                ChildItem(model='user.unitecoupon'),
                ChildItem(model='user.coupontime'),
                ChildItem(model='user.couponcode'),
                ChildItem(model='user.usergift'),
            ]),
        ParentItem(
            '排队管理',
            children=[
                ChildItem(model='user.queue'),
                ChildItem(model='user.queuelog'),
            ]),
        ParentItem(
            '会员点管理',
            children=[
                ChildItem(model='user.storepoint'),
            ]),
        ParentItem(
            '支付管理',
            children=[
                ChildItem(model='user.storepointlog'),
                ChildItem(model='user.goldlog'),
                ChildItem(model='user.payinfo'),
            ]),
        ParentItem(
            '退款管理',
            children=[
                ChildItem(model='user.refundorder'),
            ]),

    )

    def ready(self):
        super(SuitConfig, self).ready()

        # DO NOT COPY FOLLOWING LINE
        # It is only to prevent updating last_login in DB for demo app
        self.prevent_user_last_login()

    def prevent_user_last_login(self):
        """
        Disconnect last login signal
        """
        from django.contrib.auth import user_logged_in
        from django.contrib.auth.models import update_last_login
        user_logged_in.disconnect(update_last_login)
