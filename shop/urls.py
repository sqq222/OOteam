"""planet_scientist URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
# from rest_framework_swagger.views import get_swagger_view
from rest_framework_swagger.views import get_swagger_view
# from rest_framework.schemas import get_schema_view
from django.conf import settings
from django.conf.urls.static import static

schema_view = get_swagger_view(title='API')
# schema_view = get_schema_view(title='API')




urlpatterns = [
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    # url(r'^user/', include('shop.user.urls')),
    url(r'^admin/', admin.site.urls),
    # url(r'^admin/', include('shop.admin.urls')),
    url(r'^api/v1.0/', include('shop.api.urls')),
    url(r'^nested_admin/', include('nested_admin.urls')),
    url(r'^$', schema_view),

]

urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [url(r'^silk/', include('silk.urls', namespace='silk'))]
