from django.conf.urls import url, include
from rest_framework.routers import SimpleRouter, DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns

from . import views
from . import views_store

router = DefaultRouter()

router.register(r'store_industry', views.Store_IndustryViewSet, base_name="store_industry")
router.register(r'store_catering', views.Store_CateringViewSet)
router.register(r'store_business', views.Store_BusinessViewSet)
router.register(r'store_business_time', views.Store_Business_TimeViewSet)
router.register(r'store_business_time_freeday', views.Store_Business_Time_FreeDayViewSet)
router.register(r'store_license', views.Store_LicenseViewSet)
router.register(r'store_auth', views.Store_AuthViewSet)
router.register(r'store_food_safety', views.Store_Food_SafetyViewSet)
router.register(r'stores', views.StoresViewSet)
router.register(r'store_rotation', views.Store_RotationViewSet)
router.register(r'store_image', views.Store_ImageViewSet)
router.register(r'store_lobby', views.Store_LobbyViewSet)
router.register(r'store_kitchen', views.Store_KitchenViewSet)
router.register(r'store_other', views.Store_OtherViewSet)
router.register(r'store_ad', views.Store_AdViewSet)
router.register(r'userprofile', views.AbstractUserViewSet)
router.register(r'foodcategory', views.FoodCategoryViewSet)
router.register(r'kitchen', views.KitchenViewSet)
router.register(r'tax', views.TaxViewSet)
router.register(r'sellperiod', views.SellPeriodViewSet)
router.register(r'foodimage', views.FoodImageViewSet)
router.register(r'tagcategory', views.TagCategoryViewSet)
router.register(r'tag', views.TagViewSet)
router.register(r'foodunit', views.FoodUnitViewSet)
router.register(r'food', views.FoodViewSet)
router.register(r'foodspec', views.FoodSpecViewSet)
router.register(r'deskcategory', views.DeskCategoryViewSet)
router.register(r'desk', views.DeskViewSet)
router.register(r'foodcount', views.FoodCountViewSet)
router.register(r'foodaudio', views.FoodAudioViewSet)
router.register(r'tagaudio', views.TagAudioViewSet)
router.register(r'countaudio', views.CountAudioViewSet)
router.register(r'unitaudio', views.UnitAudioViewSet)
router.register(r'deskaudio', views.DeskAudioViewSet)
router.register(r'store_category', views.StoreCategoryViewSet)
router.register(r'store_favorite', views.Store_FavoriteViewSet)
router.register(r'reserve', views.ReserveViewSet)
router.register(r'coupon', views.CouponViewSet)
router.register(r'couponcode', views.CouponCodeViewSet)
router.register(r'meal', views.MealViewSet)
router.register(r'order', views.OrderViewSet)
router.register(r'order_food', views.OrderFoodViewSet)
router.register(r'queue', views.QueueLogViewSet)
router.register(r'pay', views.PayViewSet)
router.register(r'refund_order', views.RefundOrderViewSet)
router.register(r'store_paytype', views.StorePayTypeViewSet)
router.register(r'user_gift', views.UserGiftViewSet)

urlpatterns = [
    url(r'^login/$', views.SignIn.as_view(), name='signin'),
    url(r'^sign_up/$', views_store.SignUp.as_view(), name='signup'),
    url(r'^sign_in/$', views.SignIn.as_view(), name='signup'),
    url(r'^check_code/$', views_store.RegCodeVer.as_view(), name='check_code'),
    url(r'^forgetpwd/check_user/$', views_store.Forget_PwdView.as_view(), name='forget_pwd'),
    url(r'^forgetpwd/check_code/$', views_store.Forget_CodeVer.as_view(), name='forget_pwd'),
    url(r'^forgetpwd/change_pwd/', views_store.Change_PwdView.as_view(), name='forget_pwd'),

    url(r'^store/$', views_store.StoreView.as_view(), name='store'),
    url(r'^store/business_time/add/$', views_store.Store_Add_Business_Time.as_view(), name='store'),
    url(r'^store/business_time/freeday/add/$', views_store.Store_Business_Time_FreeDay_View.as_view(), name='freeday'),

    url(r'^store/business_time/(?P<pk>[0-9]+)/$', views_store.Store_Business_Time_View.as_view(), name='freeday'),
    url(r'^store/(?P<pk>[0-9]+)/business/notice/$', views_store.Store_Notice.as_view(), name='freeday'),
    url(r'^store/(?P<pk>[0-9]+)/business/desc/$', views_store.Store_Desc.as_view(), name='freeday'),
    url(r'^store/(?P<pk>[0-9]+)/change_pwd/$', views_store.Store_Change_Pwd_View.as_view(), name='freeday'),
    url(r'^', include(router.urls)),

]
urlpatterns += [
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),
]


# urlpatterns = format_suffix_patterns(urlpatterns)
