"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve

FRONTEND_DIR = settings.BASE_DIR.parent / 'gym_booking_frontend'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('gym_booking_backend.presentation.urls')),
    path('', include('gym_booking_backend.presentation.pt_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        path('', serve, {'document_root': FRONTEND_DIR, 'path': 'index.html'}),
        path('<path:path>', serve, {'document_root': FRONTEND_DIR}),
    ]

