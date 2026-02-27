# setting 

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/


# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = 'django-insecure-nyo_fa03512tqw8lj2i=p)i9^bs+qg*%lxwm-ib-%)8u#18c@_'

# SECURITY WARNING: don't run with debug turned on in production!

DEBUG = False


ALLOWED_HOSTS = ['31.97.62.126', 'edbbilling.com', 'www.edbbilling.com']





# Application definition
INSTALLED_APPS = [

    'jazzmin',  # for admin interface customization
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # For human-friendly formatting of numbers and dates
    
    
    # Your apps
    'projects',

    
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
     'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoiseMiddleware for serving static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',  # SessionMiddleware should be here
    'projects.middleware.BlockUnauthorizedMiddleware',  # Your custom middleware should come after
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

JAZZMIN_SETTINGS = {
    "site_title": "Elite Dream Admin",
    "site_header": "The Elite Dream Builders Admin",
    "site_brand": "Elite Dream Builders",
    "welcome_sign": "Welcome to The Elite Dream Builders Dashboard",
    "copyright": "Elite Dream Builders",
    
    "icons": {
        # Your app models
        "projects.Project": "fas fa-project-diagram",
        "projects.Expense": "fas fa-file-invoice-dollar",
        "projects.Payment": "fas fa-money-bill-wave",
        "projects.DailyExpense": "fas fa-calendar-day",
        "projects.CustomProject": "fas fa-folder-plus",
        "projects.SiteImage": "fas fa-image",

        # Built-in auth models
        "auth.User": "fas fa-user",
        "auth.Group": "fas fa-users-cog",
    },

    "topmenu_links": [
        {"name": "Home", "url": "/", "permissions": ["auth.view_user"]},
    ],

    "show_sidebar": True,
    "navigation_expanded": True,
}



# Expire session after 10 minutes of inactivity
SESSION_COOKIE_AGE = 600  # 10 minutes in seconds

# Reset the session timer on every request
SESSION_SAVE_EVERY_REQUEST = True

# Optional: Ensure session expires when browser closes
SESSION_EXPIRE_AT_BROWSER_CLOSE = True




ROOT_URLCONF = 'ledger_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'projects', 'templates')],  # important: fixed here
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ledger_system.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # Use PostgreSQL as the database backend
        'NAME': 'billingdb',
        'USER': 'billinguser',# billinguser for production
        'PASSWORD': 'Admin123',
        'HOST': '127.0.0.1',
        'PORT': '5432',# 5432 is the default port for PostgreSQL
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'ledger_system', 'static'),
]


STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Where collectstatic dumps files


STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]


STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Optional: override for production
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'



import os
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')



# Security settings (good practice for production)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = False if DEBUG else True
CSRF_COOKIE_SECURE = False if DEBUG else True

# Login redirect
LOGIN_URL = '/admin/login/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


JAZZMIN_SETTINGS = {
    "site_title": "Elite Admin",
    "site_header": "The Elite Dream Builders",
    "site_brand": "Elite Admin",
    "welcome_sign": "Welcome to The Elite Dream Builders Admin",
    "site_logo": "images/logo.PNG",  # path relative to STATICFILES_DIRS
    "site_logo_classes": "img-circle",  # optional: add Bootstrap classes
    "site_icon": "images/logo.PNG",     # favicon
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
}

# Set session to expire after 5 minutes (300 seconds)
SESSION_COOKIE_AGE = 300  # 5 minutes in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True
