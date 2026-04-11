# انشاءنا هذا الملف من اجل فصل المهام في الايمل 



from django.core.mail import get_connection, send_mail
from .models import EmailSetting

def get_active_email_connection():
    """
    تجلب إعدادات البريد من قاعدة البيانات وتُنشئ اتصالاً جاهزاً للإرسال.
    """
    try:
        # جلب الإعدادات (نفترض أن هناك صف واحد فقط pk=1)
        config = EmailSetting.objects.get(pk=1)
        
        # إنشاء اتصال باستخدام البيانات المخزنة
        connection = get_connection(
            backend=config.email_backend,
            host=config.email_host,
            port=config.email_port,
            username=config.email_host_user,
            password=config.email_host_password,
            use_tls=config.email_use_tls,
            use_ssl=False,
        )
        return connection, config.default_from_email
    except EmailSetting.DoesNotExist:
        # في حال عدم وجود إعدادات في قاعدة البيانات
        print("Warning: Email settings are not configured in the database.")
        return None, None

def send_custom_email(subject, message, recipient_list):
    """
    دالة مخصصة للإرسال تستخدم إعدادات قاعدة البيانات.
    استخدم هذه الدالة في جميع أنحاء المشروع.
    """
    connection, from_email = get_active_email_connection()
    
    if connection and from_email:
        try:
            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                fail_silently=False,
                connection=connection 
            )
            return True, "تم الإرسال بنجاح"
        except Exception as e:
            return False, str(e)
    else:
        return False, "إعدادات البريد غير مكتملة في النظام"