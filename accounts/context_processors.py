# accounts/context_processors.py

from .models import Profile, User, CompanySettings

def site_settings(request):
    """
    يجعل إعدادات الموقع متاحة في جميع القوالب.
    """
    context_data = {
        'company_logo': None,
        'user_profile_picture': None,
        'company_settings': None,
    }
    
    # ========== 1. جلب إعدادات الشركة من النموذج الجديد ==========
    try:
        settings = CompanySettings.get_settings()
        context_data['company_settings'] = settings
    except Exception:
        pass
    
    # ========== 2. جلب شعار الشركة من أول سوبر يوزر (للخلفية) ==========
    try:
        superuser = User.objects.filter(is_superuser=True).first()
        if superuser and hasattr(superuser, 'profile'):
            context_data['company_logo'] = superuser.profile.logo
    except (User.DoesNotExist, Profile.DoesNotExist):
        pass
    
    # ========== 3. إضافة صورة البروفايل للمستخدم الحالي ==========
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            if profile.profile_picture and hasattr(profile.profile_picture, 'url'):
                context_data['user_profile_picture'] = profile.profile_picture.url
            else:
                context_data['user_profile_picture'] = '/static/images/default_avatar.png'
        except:
            context_data['user_profile_picture'] = '/static/images/default_avatar.png'
    else:
        context_data['user_profile_picture'] = '/static/images/default_avatar.png'
    
    return context_data


def company_settings(request):
    """
    توفير إعدادات الشركة لجميع القوالب (اسم مختصر)
    """
    try:
        settings = CompanySettings.get_settings()
        return {
            'company_settings': settings
        }
    except Exception:
        return {
            'company_settings': None
        }