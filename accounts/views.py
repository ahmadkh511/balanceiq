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
    """الصفحة الرئيسية - لوحة التحكم الكاملة مع جميع الإحصائيات والرسوم البيانية وأفضل المنتجات"""
    
    # ===== التحقق من تسجيل الدخول =====
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    
    # ===== إعداد متغير الشاشة الحمراء (تغيير كلمة المرور الافتراضية) =====
    show_force_change = False
    if request.user.check_password('Admin@123456'):
        show_force_change = True
    
    # فخ تغيير كلمة المرور
    if request.session.get('force_change'):
        return redirect('accounts:force_password_change')
    
    # ===== الاستيرادات اللازمة =====
    from datetime import timedelta, date
    from decimal import Decimal
    from django.db.models import Sum, Q, F
    from django.urls import reverse
    from django.utils import timezone
    from invoice.models import (
        Purch, Sale, SaleReturn, PurchaseReturn, 
        Product, WebsiteOrder, SaleItem, CashTransaction
    )
    from accounts.models import CompanySettings
    
    # ===== جلب إعدادات الشركة =====
    settings = CompanySettings.get_settings()
    
    # ===== حساب الفترات الزمنية =====
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    sixty_days_ago = thirty_days_ago - timedelta(days=30)
    
    # دالة مساعدة لحساب الاتجاه
    def calc_trend(current, previous, reverse=False):
        if previous == 0:
            return 0 if current == 0 else (100 if not reverse else -100)
        change = ((current - previous) / previous) * 100
        if reverse:
            change = -change
        return round(change, 1)
    
    # ============================================
    # 1. إحصائيات فواتير الشراء
    # ============================================
    current_purch = Purch.objects.filter(purch_date__gte=thirty_days_ago).count()
    previous_purch = Purch.objects.filter(
        purch_date__gte=sixty_days_ago,
        purch_date__lt=thirty_days_ago
    ).count()
    purch_trend = calc_trend(current_purch, previous_purch)
    
    # ============================================
    # 2. إحصائيات فواتير البيع
    # ============================================
    current_sale = Sale.objects.filter(sale_date__gte=thirty_days_ago).count()
    previous_sale = Sale.objects.filter(
        sale_date__gte=sixty_days_ago,
        sale_date__lt=thirty_days_ago
    ).count()
    sale_trend = calc_trend(current_sale, previous_sale)
    
    # ============================================
    # 3. إحصائيات المرتجعات
    # ============================================
    current_return = (
        SaleReturn.objects.filter(return_date__gte=thirty_days_ago).count() +
        PurchaseReturn.objects.filter(return_date__gte=thirty_days_ago).count()
    )
    previous_return = (
        SaleReturn.objects.filter(
            return_date__gte=sixty_days_ago,
            return_date__lt=thirty_days_ago
        ).count() +
        PurchaseReturn.objects.filter(
            return_date__gte=sixty_days_ago,
            return_date__lt=thirty_days_ago
        ).count()
    )
    return_trend = calc_trend(current_return, previous_return, reverse=True)
    
    # ============================================
    # 4. عدد المنتجات
    # ============================================
    product_count = Product.objects.count()
    
    # ============================================
    # 5. طلبات المتجر الجديدة
    # ============================================
    new_orders_count = WebsiteOrder.objects.filter(status='new').count()
    
    # ============================================
    # 6. الرسم البياني للمبيعات (آخر 7 أيام)
    # ============================================
    chart_labels = []
    chart_values = []
    weekday_names = {
        0: 'الاثنين', 1: 'الثلاثاء', 2: 'الأربعاء',
        3: 'الخميس', 4: 'الجمعة', 5: 'السبت', 6: 'الأحد'
    }
    
    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        chart_labels.append(weekday_names.get(target_date.weekday(), str(target_date)))
        
        daily_total = Sale.objects.filter(sale_date=target_date).aggregate(
            total=Sum('sale_final_total')
        )['total'] or Decimal('0.00')
        chart_values.append(float(daily_total))
    
    # ============================================
    # 7. الرسم البياني المتكامل (آخر 30 يوماً)
    # ============================================
    def get_advanced_chart_data(days=30):
        """جلب بيانات متكاملة للرسم البياني"""
        adv_labels = []
        sales_data = []
        profit_data = []
        expenses_data = []
        
        for i in range(days - 1, -1, -1):
            target_date = today - timedelta(days=i)
            adv_labels.append(weekday_names.get(target_date.weekday(), str(target_date)))
            
            # المبيعات اليومية
            daily_sales = Sale.objects.filter(
                sale_date=target_date
            ).aggregate(total=Sum('sale_final_total'))['total'] or Decimal('0.00')
            sales_data.append(float(daily_sales))
            
            # تكلفة البضاعة المباعة (COGS)
            daily_sale_items = SaleItem.objects.filter(
                sale__sale_date=target_date
            ).select_related('product')
            
            daily_cogs = Decimal('0.00')
            for item in daily_sale_items:
                if item.product:
                    cost_price = item.product.average_purchase_cost or item.product.purch_price or Decimal('0.00')
                    daily_cogs += item.sold_quantity * cost_price
            
            # صافي الربح = المبيعات - التكلفة
            daily_profit = daily_sales - daily_cogs
            profit_data.append(float(daily_profit))
            
            # المصروفات اليومية
            daily_expenses = CashTransaction.objects.filter(
                transaction_date__date=target_date,
                transaction_type__in=['expense', 'withdrawal']
            ).aggregate(total=Sum('amount_out'))['total'] or Decimal('0.00')
            expenses_data.append(float(daily_expenses))
        
        return {
            'labels': adv_labels,
            'sales': sales_data,
            'profit': profit_data,
            'expenses': expenses_data,
        }
    
    advanced_chart_data = get_advanced_chart_data(days=30)
    
    # ============================================
    # 8. أفضل المنتجات مبيعاً (Top Products)
    # ============================================
    def get_top_products(limit=10):
        """جلب أفضل المنتجات مبيعاً من حيث الكمية والقيمة"""
        
        # أفضل المنتجات من حيث الكمية المباعة
        top_by_quantity = SaleItem.objects.filter(
            product__isnull=False
        ).values(
            'product__id',
            'product__product_name',
            'product__product_image'
        ).annotate(
            total_quantity=Sum('sold_quantity'),
            total_value=Sum(F('sold_quantity') * F('unit_price'))
        ).filter(
            total_quantity__gt=0
        ).order_by('-total_quantity')[:limit]
        
        # أفضل المنتجات من حيث القيمة المالية
        top_by_value = SaleItem.objects.filter(
            product__isnull=False
        ).values(
            'product__id',
            'product__product_name',
            'product__product_image'
        ).annotate(
            total_value=Sum(F('sold_quantity') * F('unit_price')),
            total_quantity=Sum('sold_quantity')
        ).filter(
            total_value__gt=0
        ).order_by('-total_value')[:limit]
        
        # تنسيق البيانات للعرض (نسخة آمنة)
        def format_product(item):
            # معالجة الصورة بشكل آمن
            image_field = item.get('product__product_image')
            image_url = None
            if image_field:
                if hasattr(image_field, 'url'):
                    image_url = image_field.url
                elif isinstance(image_field, str):
                    image_url = image_field
                else:
                    image_url = None
            
            return {
                'id': item['product__id'],
                'name': item['product__product_name'],
                'quantity': float(item['total_quantity']),
                'value': float(item['total_value']),
                'image': image_url,
            }
        
        return {
            'top_by_quantity': [format_product(item) for item in top_by_quantity],
            'top_by_value': [format_product(item) for item in top_by_value],
        }
    
    top_products = get_top_products(limit=10)
    
    # ============================================
    # 9. تنبيهات النظام
    # ============================================
    alerts = []
    
    # أ. المنتجات منخفضة المخزون
    low_stock_products = Product.objects.filter(
        current_stock_quantity__lt=5,
        current_stock_quantity__gt=0
    )[:5]
    
    for product in low_stock_products:
        alerts.append({
            'type': 'warning',
            'icon': 'fa-exclamation-triangle',
            'title': 'مخزون منخفض',
            'message': f'منتج "{product.product_name}" - المتبقي: {product.current_stock_quantity}',
            'link': reverse('invoice:product_detail', args=[product.slug]),
            'link_text': 'تحديث المخزون'
        })
    
    # ب. المنتجات المنفذة
    out_of_stock_products = Product.objects.filter(current_stock_quantity=0)[:3]
    for product in out_of_stock_products:
        alerts.append({
            'type': 'danger',
            'icon': 'fa-times-circle',
            'title': 'منتج غير متوفر',
            'message': f'منتج "{product.product_name}" نفد من المخزون',
            'link': reverse('invoice:product_detail', args=[product.slug]),
            'link_text': 'طلب شراء'
        })
    
    # ج. فواتير غير مدفوعة
    fifteen_days_ago = today - timedelta(days=15)
    unpaid_sales = Sale.objects.filter(
        is_paid=False,
        sale_date__lte=fifteen_days_ago
    )[:3]
    
    for sale in unpaid_sales:
        alerts.append({
            'type': 'danger',
            'icon': 'fa-exclamation-circle',
            'title': 'فاتورة غير مدفوعة',
            'message': f'فاتورة {sale.uniqueId} - المتبقي: {sale.balance_due}',
            'link': reverse('invoice:sale_detail', args=[sale.slug]),
            'link_text': 'متابعة التحصيل'
        })
    
    # د. طلبات متجر جديدة
    new_website_orders = WebsiteOrder.objects.filter(status='new')[:3]
    for order in new_website_orders:
        alerts.append({
            'type': 'info',
            'icon': 'fa-shopping-cart',
            'title': 'طلب جديد',
            'message': f'طلب #{order.id} - {order.full_name} - {order.total_amount}',
            'link': reverse('invoice:order_detail', args=[order.id]),
            'link_text': 'معالجة الطلب'
        })
    
    # ============================================
    # 10. تعليقات الفيسبوك
    # ============================================
    fb_comments = []
    if settings.fb_page_id and settings.fb_access_token:
        try:
            import requests
            url = f"https://graph.facebook.com/v18.0/{settings.fb_page_id}/feed"
            params = {
                'fields': 'from{name,picture},message,created_time,permalink_url',
                'access_token': settings.fb_access_token,
                'limit': 5
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for post in data.get('data', []):
                    if 'message' in post:
                        fb_comments.append(post)
        except Exception as e:
            print(f"Facebook Error: {e}")
    
    # ============================================
    # تجهيز السياق
    # ============================================
    context = {
        'user': request.user,
        'settings': settings,
        'fb_comments': fb_comments,
        'show_force_change': show_force_change,
        # الإحصائيات الأساسية
        'purch_count': current_purch,
        'purch_trend': purch_trend,
        'sale_count': current_sale,
        'sale_trend': sale_trend,
        'return_count': current_return,
        'return_trend': return_trend,
        'product_count': product_count,
        'new_orders_count': new_orders_count,
        # الرسم البياني الأساسي
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        # الرسم البياني المتكامل
        'advanced_chart_data': advanced_chart_data,
        # أفضل المنتجات مبيعاً
        'top_products': top_products,
        # تنبيهات النظام
        'alerts': alerts,
    }
    
    return render(request, 'accounts/dashboard.html', context)

# ============================================
# صفحة الشروط والأحكام (عرض ثابت)
# ============================================
class TermsView(TemplateView):
    """عرض صفحة الشروط والأحكام"""
    template_name = 'accounts/terms.html'



# ============================================
# لوحة التحكم (dashboard)
# ============================================


import requests
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# ==========================================
# استيراد CompanySettings من نفس التطبيق (accounts)
# ==========================================
from .models import CompanySettings


# أضف هذه الاستيرادات مع باقي الاستيرادات في أعلى الملف
from invoice.models import (
    Purch, Sale, SaleReturn, PurchaseReturn, 
    Product, WebsiteOrder
)
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.db.models import Sum
from django.urls import reverse



# ==========================================
# دالة لجلب البيانات المتكاملة
# ==========================================



# ==========================================
# أفضل المنتجات مبيعاً
# ==========================================



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



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
# تأكد من استيراد is_staff_user من ملف permissions أو utils الخاص بك
# from .utils import is_staff_user 

@login_required
@user_passes_test(is_staff_user)
def user_edit_view(request, pk):
    """تحرير بيانات مستخدم معين"""
    user = get_object_or_404(User, pk=pk)
    profile, created = Profile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        # تمرير is_admin=True لتفعيل حقول (زبون/مورد) وإخفاء حقول الاسم
        profile_form = UserProfileUpdateForm(request.POST, request.FILES, instance=profile, is_admin=True)
        
        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()
            messages.success(request, f'تم تحديث بيانات المستخدم "{user.username}" بنجاح.')
            return redirect('accounts:user_list')
    else:
        form = UserUpdateForm(instance=user)
        # تمرير is_admin=True هنا أيضاً عند عرض الصفحة لأول مرة
        profile_form = UserProfileUpdateForm(instance=profile, is_admin=True)
        
    context = {
        'form': form,
        'profile_form': profile_form,
        'user_to_edit': user,
        'profile': profile,
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



