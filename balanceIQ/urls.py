from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views

import os
from django.core.management import call_command

import os
from django.core.management import call_command
from django.contrib.auth import get_user_model

# إنشاء الجداول والمستخدم تلقائياً على السيرفر
if os.environ.get('RENDER'):
    if not os.path.exists('db.sqlite3'):
        call_command('migrate', '--run-syncdb')
        
        # إنشاء المستخدم مع كلمة مرور صريحة
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            user = User.objects.create_superuser(username='admin', email='admin@admin.com', password='Admin@123456')






urlpatterns = [
    path('admin/', admin.site.urls),
    path('', accounts_views.index, name='index'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('invoice/', include('invoice.urls')),
]

# 🔥 التعديل النهائي - الطريقة الموصى بها
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=None)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)