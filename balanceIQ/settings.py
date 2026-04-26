import os
from pathlib import Path
import logging
from dotenv import load_dotenv

# ==========================================
# 1. مسارات المشروع الأساسية
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent

# تحميل متغيرات البيئة المخفية من ملف .env الموجود في مجلد الجذر
load_dotenv(BASE_DIR / '.env')


# ==========================================
# 2. إعدادات الأمان الأساسية (السرية)
# ==========================================
# المفتاح السري: يقرأه من ملف .env، وإذا لم يجده يستخدم القديم كشبكة أمان لعدم تعطل الموقع محلياً
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-)hu-ahh&uj3$f2+w$f1t08bv!z)9vs3#)5u8h@)sw)rfosizi0')

# وضع التطوير: True للعمل محلياً، يجب تغييره إلى False عند رفع الموقع على الاستضافة الحقيقية!
DEBUG = True 

# المضيفون المسموح لهم: تم حذف ['*'] لأنها ثغرة أمنية قاتلة في الإنتاج
# أضف هنا عنوان IP الشبكة المحلية إذا كنت تختبر الموقع من جهاز آخر
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.1.108'] 


# ==========================================
# 3. التطبيقات المثبتة
# ==========================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts.apps.AccountsConfig',  
    'invoice.apps.InvoiceConfig',
]

# ==========================================
# 4. البرمجيات الوسيطة (Middleware)
# ==========================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'balanceIQ.urls'

# ==========================================
# 5. إعدادات القوالب (Templates)
# ==========================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.site_settings',
                'invoice.context_processors.cart_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'balanceIQ.wsgi.application'


# ==========================================
# 6. قاعدة البيانات
# ==========================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'accounting_db',
        'USER': 'root',
        # كلمة المرور تُقرأ من ملف .env، وإذا كانت فارغة محلياً تمر فارغة
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        }
    }
}


# ==========================================
# 7. التحقق من صحة كلمات المرور
# ==========================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 9}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ==========================================
# 8. اللغة والوقت
# ==========================================
LANGUAGE_CODE = 'ar'  # تم تغييرها للعربية لدعم المتجر العربي
TIME_ZONE = 'Asia/Amman'  # تم تغييرها لتوقيت بلدك (عدلها حسب دولتك مثل Asia/Riyadh أو Africa/Cairo)
USE_I18N = True
USE_TZ = True


# ==========================================
# 9. الملفات الثابتة (Static) والملفات المرفوعة (Media)
# ==========================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ==========================================
# 10. إعدادات المصادقة وتسجيل الدخول
# ==========================================
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'accounts:login'

# إعدادات الجلسات (مدة صلاحية تسجيل الدخول)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  
SESSION_COOKIE_AGE = 1209600  # أسبوعان بالثواني

# إعداد مدة صلاحية رابط إعادة تعيين كلمة المرور (24 ساعة)
PASSWORD_RESET_TIMEOUT = 86400  

# رابط الموقع الأساسي (مهم لروابط إعادة التعيين)
SITE_URL = 'http://localhost:8000'  


# ==========================================
# 11. إعدادات الأمان (مهمة جداً للإنتاج)
# ==========================================
# هذه الإعدادات معطلة (False) للعمل على الوكال هوست محلياً.
# عند الرفع على الاستضافة (التي تدعم HTTPS)، قم بتغييرها إلى True
CSRF_COOKIE_SECURE = False  
SESSION_COOKIE_SECURE = False  
# SECURE_SSL_REDIRECT = True  




# ==========================================
# 13. نظام تسجيل الأحداث (Logging)
# ==========================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}', 'style': '{'},
        'simple': {'format': '{levelname} {asctime} {message}', 'style': '{'},
        'detailed': {'format': '{asctime} | {levelname:8s} | {name:20s} | {message}', 'style': '{', 'datefmt': '%Y-%m-%d %H:%M:%S'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple', 'level': 'INFO'},
        'file_debug': {'class': 'logging.FileHandler', 'filename': os.path.join(BASE_DIR, 'logs/debug.log'), 'formatter': 'detailed', 'level': 'DEBUG'},
        'file_errors': {'class': 'logging.FileHandler', 'filename': os.path.join(BASE_DIR, 'logs/errors.log'), 'formatter': 'verbose', 'level': 'ERROR'},
        'file_info': {'class': 'logging.FileHandler', 'filename': os.path.join(BASE_DIR, 'logs/info.log'), 'formatter': 'detailed', 'level': 'INFO'},
    },
    'loggers': {
        'django': {'handlers': ['console', 'file_info'], 'level': 'INFO', 'propagate': True},
        'django.request': {'handlers': ['file_info', 'file_errors'], 'level': 'DEBUG', 'propagate': False},
        'invoice': {'handlers': ['console', 'file_debug', 'file_errors'], 'level': 'DEBUG', 'propagate': False},
        'invoice.models': {'handlers': ['file_debug'], 'level': 'DEBUG', 'propagate': False},
        'invoice.views': {'handlers': ['console', 'file_debug'], 'level': 'DEBUG', 'propagate': False},
        'invoice.forms': {'handlers': ['file_debug'], 'level': 'DEBUG', 'propagate': False},
    },
}