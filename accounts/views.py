# ============================================
# IMPORT STATEMENTS - استيراد المكتبات اللازمة
# ============================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.views.generic import TemplateView
from .forms import CustomUserCreationForm, CustomPasswordResetForm, UserProfileUpdateForm, UserUpdateForm
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.models import User, Group, Permission
from .models import Profile
from invoice.utils import get_active_email_connection
import os
import shutil
from urllib.parse import urlparse
from django.core.exceptions import ValidationError

from .models import CompanySettings
from .forms import CompanySettingsForm



from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.core.cache import cache


# ============================================
# الصفحة الرئيسية (index)
# ============================================


def index(request):
    if request.user.is_authenticated:
        # ===== إعداد متغير الشاشة الحمراء =====
        show_force_change = False
        if request.user.check_password('Admin@123456'):
            show_force_change = True
        # ==========================================
        
        return render(request, 'accounts/dashboard.html', {'show_force_change': show_force_change})
    else:
        return redirect('accounts:login')


# ============================================
# صفحة الشروط والأحكام (عرض ثابت)
# ============================================
class TermsView(TemplateView):
    """عرض صفحة الشروط والأحكام"""
    template_name = 'accounts/terms.html'

# ============================================
# لوحة التحكم (dashboard)
# ============================================

@login_required
def dashboard(request):
    """عرض لوحة التحكم الرئيسية (محمية بتسجيل الدخول)"""
    # ===== فخ تغيير كلمة المرور =====
    if request.session.get('force_change'):
        return redirect('accounts:force_password_change')
    # ==================================
    
    return render(request, 'accounts/dashboard.html')

# ============================================
# رفع شعار الشركة (API endpoint)
# ============================================
@csrf_exempt
@login_required
def upload_company_logo(request):
    """
    رفع شعار الشركة - يستخدم عبر AJAX
    """
    if request.method == 'POST':
        profile = request.user.profile
        if 'logo' in request.FILES:
            profile.logo = request.FILES['logo']
            profile.save()
            return JsonResponse({'success': True, 'logo_url': profile.logo.url})
        else:
            return JsonResponse({'success': False, 'error': 'لم يتم إرسال أي صورة'})
    return JsonResponse({'success': False, 'error': 'طلب غير صالح'})


# ============================================
# تسجيل مستخدم جديد (register)
# ============================================
def register_view(request):
    """
    إنشاء حساب جديد للمستخدم
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

# ============================================
# استعادة كلمة المرور (Password Reset)
# ============================================
class CustomPasswordResetView(SuccessMessageMixin, PasswordResetView):
    """تخصيص عملية استعادة كلمة المرور لاستخدام إعدادات البريد من قاعدة البيانات"""
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = '/accounts/password_reset/done/'
    html_email_template_name = 'accounts/password_reset_email.html'
    success_message = "تم إرسال رابط استعادة كلمة المرور إلى بريدك الإلكتروني."
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        """تعديل إعدادات البريد مؤقتاً لاستخدام إعدادات قاعدة البيانات"""
        connection, from_email = get_active_email_connection()
        
        if connection and from_email:
            # حفظ الإعدادات الحالية
            old_host = getattr(settings, 'EMAIL_HOST', None)
            old_port = getattr(settings, 'EMAIL_PORT', None)
            old_user = getattr(settings, 'EMAIL_HOST_USER', None)
            old_pass = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
            old_tls = getattr(settings, 'EMAIL_USE_TLS', None)
            old_from = getattr(settings, 'DEFAULT_FROM_EMAIL', None)

            try:
                # تحديث الإعدادات مؤقتاً
                settings.EMAIL_HOST = connection.host
                settings.EMAIL_PORT = connection.port
                settings.EMAIL_HOST_USER = connection.username
                settings.EMAIL_HOST_PASSWORD = connection.password
                settings.EMAIL_USE_TLS = connection.use_tls
                settings.DEFAULT_FROM_EMAIL = from_email
                return super().form_valid(form)
            finally:
                # استعادة الإعدادات الأصلية
                settings.EMAIL_HOST = old_host
                settings.EMAIL_PORT = old_port
                settings.EMAIL_HOST_USER = old_user
                settings.EMAIL_HOST_PASSWORD = old_pass
                settings.EMAIL_USE_TLS = old_tls
                settings.DEFAULT_FROM_EMAIL = old_from
        else:
            return super().form_valid(form)

# ============================================
# الملف الشخصي (profile)
# ============================================
@login_required
def profile_view(request):
    """
    عرض وتعديل الملف الشخصي للمستخدم
    """
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث ملفك الشخصي بنجاح!')
            return redirect('accounts:profile')
    else:
        form = UserProfileUpdateForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile
    }
    return render(request, 'accounts/profile.html', context)

# ============================================
# سجلات النظام (system logs)
# ============================================
def is_admin_or_support(user):
    """التحقق من أن المستخدم مدير أو دعم فني"""
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(is_admin_or_support, login_url='accounts:login')
def system_logs_view(request):
    """عرض سجلات النظام مع إمكانية التصفية والحذف"""
    # معالجة طلب الحذف
    if request.method == 'POST' and request.user.is_superuser:
        log_type_to_clear = request.POST.get('log_type_to_clear')
        if log_type_to_clear in ['debug', 'errors', 'info']:
            log_file_path = os.path.join(settings.BASE_DIR, 'logs', f'{log_type_to_clear}.log')
            try:
                with open(log_file_path, 'w') as f:
                    f.truncate(0)
                messages.success(request, f'تم مسح سجلات {log_type_to_clear} بنجاح.')
                return redirect(f"{request.path}?log_type={log_type_to_clear}")
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء مسح السجلات: {str(e)}')
    
    # عرض السجلات
    log_type = request.GET.get('log_type', 'info')
    if log_type not in ['debug', 'errors', 'info']:
        log_type = 'info'
    
    log_file_path = os.path.join(settings.BASE_DIR, 'logs', f'{log_type}.log')
    
    if not os.path.exists(log_file_path):
        return render(request, 'accounts/system_logs.html', {
            'error': f'ملف السجل غير موجود. المسار المتوقع: {log_file_path}',
            'page_obj': [],
            'log_levels': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            'current_level': 'ALL',
            'current_log_type': log_type,
            'log_types': ['debug', 'errors', 'info'],
        })
    
    # قراءة وتحليل السجلات
    logs = []
    log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            lines.reverse()  # عرض الأحدث أولاً

        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            try:
                parts = line.split(' ', 3)
                if len(parts) < 4:
                    logs.append({'timestamp': '', 'level': 'RAW', 'message': line, 'level_class': 'raw'})
                    continue
                
                date_str, time_str, level_str, message = parts[0], parts[1], parts[2], ' '.join(parts[3:])
                
                level_filter = request.GET.get('level', 'ALL')
                if level_filter != 'ALL' and level_str not in level_filter:
                    continue
                
                logs.append({
                    'timestamp': f"{date_str} {time_str}",
                    'level': level_str,
                    'message': message,
                    'level_class': level_str.lower()
                })
            except Exception:
                logs.append({'timestamp': '', 'level': 'RAW', 'message': line, 'level_class': 'raw'})
    except Exception as e:
        logs.append({'timestamp': '', 'level': 'ERROR', 'message': f'حدث خطأ أثناء قراءة ملف السجل: {str(e)}', 'level_class': 'error'})
    
    # تقسيم النتائج إلى صفحات
    paginator = Paginator(logs, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'log_levels': log_levels,
        'current_level': request.GET.get('level', 'ALL'),
        'current_log_type': log_type,
        'log_types': ['debug', 'errors', 'info'],
        'is_superuser': request.user.is_superuser,
    }
    return render(request, 'accounts/system_logs.html', context)

# ============================================
# إدارة المستخدمين (user list)
# ============================================
def is_staff_user(user):
    """التحقق من أن المستخدم موظف"""
    return user.is_staff

@login_required
@user_passes_test(is_staff_user)
def user_list_view(request):
    """عرض قائمة بجميع المستخدمين في النظام"""
    users = User.objects.all().order_by('-date_joined')
    context = {
        'users': users,
        'title': 'قائمة المستخدمين'
    }
    return render(request, 'accounts/user_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def user_edit_view(request, pk):
    """تحرير بيانات مستخدم معين"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تحديث بيانات المستخدم "{user.username}" بنجاح.')
            return redirect('accounts:user_list')
    else:
        form = UserUpdateForm(instance=user)
        
    context = {
        'form': form,
        'user_to_edit': user,
        'title': f'تحرير المستخدم: {user.username}'
    }
    return render(request, 'accounts/user_edit.html', context)

# ============================================
# إدارة الصلاحيات (permissions)
# ============================================
@login_required
@user_passes_test(is_staff_user)
def permissions_view(request):
    """
    صفحة لإدارة الصلاحيات والأدوار (المجموعات)
    """
    groups = Group.objects.all().prefetch_related('permissions')
    all_permissions = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename')
    
    # تنظيم الصلاحيات حسب النموذج
    permissions_by_model = {}
    for perm in all_permissions:
        model_name = perm.content_type.model_class().__name__ if perm.content_type.model_class() else perm.content_type.model
        if model_name not in permissions_by_model:
            permissions_by_model[model_name] = []
        permissions_by_model[model_name].append(perm)
    
    # إنشاء مجموعة جديدة
    if request.method == 'POST' and 'create_group' in request.POST:
        group_name = request.POST.get('group_name')
        if group_name:
            if Group.objects.filter(name=group_name).exists():
                messages.error(request, f'المجموعة "{group_name}" موجودة بالفعل.')
            else:
                new_group = Group.objects.create(name=group_name)
                selected_permissions = request.POST.getlist('permissions')
                new_group.permissions.set(selected_permissions)
                messages.success(request, f'تم إنشاء المجموعة "{group_name}" بنجاح.')
                return redirect('accounts:permissions')
        else:
            messages.error(request, 'اسم المجموعة لا يمكن أن يكون فارغًا.')
    
    # تحرير مجموعة
    if request.method == 'POST' and 'edit_group' in request.POST:
        group_id = request.POST.get('group_id')
        group_to_edit = get_object_or_404(Group, pk=group_id)
        selected_permissions = request.POST.getlist('permissions')
        group_to_edit.permissions.set(selected_permissions)
        messages.success(request, f'تم تحديث صلاحيات المجموعة "{group_to_edit.name}" بنجاح.')
        return redirect('accounts:permissions')
    
    # حذف مجموعة
    if request.method == 'POST' and 'delete_group' in request.POST:
        group_id = request.POST.get('group_id')
        group_to_delete = get_object_or_404(Group, pk=group_id)
        group_name = group_to_delete.name
        group_to_delete.delete()
        messages.success(request, f'تم حذف المجموعة "{group_name}" بنجاح.')
        return redirect('accounts:permissions')
    
    context = {
        'title': 'الصلاحيات والأدوار',
        'groups': groups,
        'permissions_by_model': permissions_by_model,
    }
    return render(request, 'accounts/permissions.html', context)





@login_required
@user_passes_test(lambda u: u.is_superuser)
def company_settings_view(request):
    """
    صفحة تعديل إعدادات الشركة والفوتر
    - فقط المدير (Superuser) يمكنه الوصول
    - تعرض نموذج تعديل جميع إعدادات الشركة
    - تمسح الكاش بعد كل حفظ لضمان ظهور البيانات الجديدة فوراً
    """
    # جلب الإعدادات الحالية
    settings = CompanySettings.get_settings()
    
    if request.method == 'POST':
        # تمرير البيانات والملفات إلى النموذج مع ربطها بالكائن الحالي
        form = CompanySettingsForm(request.POST, request.FILES, instance=settings)
        
        if form.is_valid():
            # حفظ النموذج (دالة save المخصصة ستمسح الكاش تلقائياً)
            form.save()
            
            # مسح الكاش مرة أخرى للتأكد (احتياطي)
            cache.delete('company_settings')
            
            messages.success(request, 'تم حفظ إعدادات الشركة بنجاح!')
            
            # إعادة التوجيه لمنع إعادة إرسال النموذج عند التحديث
            return redirect('accounts:company_settings')
        else:
            # عرض أخطاء النموذج
            messages.error(request, 'حدث خطأ في حفظ البيانات. يرجى التحقق من المدخلات.')
            
            # طباعة الأخطاء في الكونسول للتصحيح (يمكن حذفه لاحقاً)
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"خطأ في الحقل {field}: {error}")
    else:
        # عرض النموذج فارغ في حالة GET مع تعبئته بالبيانات الحالية
        form = CompanySettingsForm(instance=settings)
    
    # تمرير السياق للقالب
    context = {
        'form': form,
        'settings': settings,
        'title': 'إعدادات الشركة والفوتـر'
    }
    
    return render(request, 'accounts/company_settings.html', context)



