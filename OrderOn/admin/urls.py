from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^index/$', views.index, name='index'),
    url(r'^$', views.index, name='index'),
    url(r'^login/$', views.signin, name='signin'),
    url(r'^lock/$', views.lock_view, name='lock'),
    url(r'^unlock/$', views.unlock_view, name='unlock'),
    url(r'^logout/$', views.logout_view, name='logout'),
    url(r'^login/verf/$', views.login_view, name='loginview'),
    url(r'^user/$', views.usermanage_view, name='usermanage'),
    url(r'^user/edit/$', views.user_edit_view, name='usermanage'),
    url(r'^user/lock/$', views.user_lock, name='user_lock'),
    url(r'^user/unlock/$', views.user_unlock, name='user_unlock'),
    url(r'^user/add/$', views.user_add_view, name='usr_add'),
    url(r'^user/useradd/', views.user_add, name='useradd'),
    url(r'^user/useredit/', views.user_edit, name='useredit'),
    url(r'^export/$', views.export_excel, name='export'),
    url(r'^upload/$', views.upload_view, name='upload_view'),
    url(r'^identity/$', views.identity_manage_view, name='identity_view'),
    url(r'^identity/add/$', views.identity_add_view, name='identity_add_view'),
    url(r'^identity/identityadd/$', views.identityadd, name='identityadd'),
    url(r'^identity/edit/$', views.identity_edit_view, name='identity_edit_view'),
    url(r'^user_data/basic/', views.user_data_basic_view,
        name='user_data_basic'),
    url(r'^user_data/new_player/', views.new_player_view,
        name='new_player_view'),
    url(r'^user_data/player_active/', views.player_active_view,
        name='player_active_view'),
    url(r'^user_data/player_stay/', views.player_stay_view,
        name='player_stay_view')
]
