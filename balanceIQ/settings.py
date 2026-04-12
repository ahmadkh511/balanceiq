from pathlib import Path
import os
import logging

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent



# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-)hu-ahh&uj3$f2+w$f1t08bv!z)9vs3#)5u8h@)sw)rfosizi0'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


# Application definition

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

BASE_DIR = Path(__file__).resolve().parent.parent

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # ✓ صحيح
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


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        #'NAME': BASE_DIR / 'db.sqlite30',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators



AUTH_PASSWORD_VALIDATORS = [
    # يتحقق من أن كلمة المرور ليست مشابهة جدًا لمعلومات المستخدم الشخصية
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    # يفرض طولًا أدنى لكلمة المرور
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 9,  # الحد الأدنى هو 9 أحرف
        }
    },
    # يتحقق من أن كلمة المرور ليست من ضمن قائمة الكلمات الشائعة والسهلة
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    # يتحقق من أن كلمة المرور ليست أرقامًا فقط
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

# إعدادات Static Files
STATIC_URL = '/static/'

# هذا ضروري للعثور على static files المشتركة في التنمية
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # ← أضف هذا!
]

# هذا للتجميع في الإنتاج فقط (عند تشغيل collectstatic)
STATIC_ROOT = BASE_DIR / 'staticfiles'





# إعدادات للملفات التي يرفعها المستخدمون (Media Files)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'



# إعدادات المصادقة
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'accounts:login'

# إعدادات CSRF (مهمة لتسجيل الخروج)
CSRF_COOKIE_SECURE = False  # للتطوير فقط، اجعلها True في الإنتاج
SESSION_COOKIE_SECURE = False  # للتطوير فقط، اجعلها True في الإنتاج


# ======================
# إعدادات الأمان (مهمة جداً للإطلاق الفعلي)
# ======================

# SECURE_SSL_REDIRECT = True  # توجيه جميع طلبات HTTP إلى HTTPS
# SESSION_COOKIE_SECURE = True  # إرسال ملفات تعريف الارتباط للجلسات عبر HTTPS فقط
# CSRF_COOKIE_SECURE = True     # إرسال ملفات تعريف الارتباط CSRF عبر HTTPS فقط


# إعدادات إعادة تعيين كلمة المرور
PASSWORD_RESET_TIMEOUT = 86400  # 24 ساعة بالثواني

# إعدادات إضافية لحل مشاكل الروابط
SITE_URL = 'http://localhost:8000'  # غير هذا الرابط حسب إعدادات الخادم الخاص بك

# إعدادات إضافية لضمان عمل روابط إعادة تعيين كلمة المرور
# إعدادات إضافية لضمان عمل روابط إعادة تعيين كلمة المرور
#ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.1.108']  # تم استبدال النطاق بالـ IP

ALLOWED_HOSTS = ['*']







LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
        'detailed': {
            'format': '{asctime} | {levelname:8s} | {name:20s} | {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'INFO',
        },
        'file_debug': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/debug.log'),
            'formatter': 'detailed',
            'level': 'DEBUG',
        },
        'file_errors': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/errors.log'),
            'formatter': 'verbose',
            'level': 'ERROR',
        },
        'file_info': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/info.log'),
            'formatter': 'detailed',
            'level': 'INFO',
        },
    },
    'loggers': {
        # Django logger
        'django': {
            'handlers': ['console', 'file_info'],
            'level': 'INFO',
            'propagate': True,
        },
        # Django request logger
        'django.request': {
            'handlers': ['file_info', 'file_errors'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # Your app logger (اسم التطبيق الرئيسي)
        'invoice': {  # تغيير هذا لاسم تطبيقك
            'handlers': ['console', 'file_debug', 'file_errors'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # Models logger
        'invoice.models': {  # سجلات الموديلات
            'handlers': ['file_debug'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # Views logger
        'invoice.views': {  # سجلات الفيوز
            'handlers': ['console', 'file_debug'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # Forms logger
        'invoice.forms': {  # سجلات الفورمز
            'handlers': ['file_debug'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}



SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # عدد الثواني (أسبوعين). يمكنك تغييره ليوم واحد مثلاً: 86400  # من اجل تحديد وقت جلسة تغير كلمة المرور  مدة اسبوع
SESSION_COOKIE_AGE = 1209600  


# إعدادات البريد الإلكتروني
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#EMAIL_HOST = 'smtp.gmail.com'
#EMAIL_PORT = 587
#EMAIL_USE_TLS = True
#EMAIL_HOST_USER = 'berutech1@gmail.com'
#EMAIL_HOST_PASSWORD = 'xsiw lyuk jqxw jlvh'
#DEFAULT_FROM_EMAIL = 'berutech1@gmail.com'
