from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from django.views.generic import CreateView 
from .forms import CustomUserCreationForm, CustomPasswordResetForm
from django.conf import settings

app_name = 'accounts' 
urlpatterns = [
    

    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    
    
    path('logout/', auth_views.LogoutView.as_view(
        next_page='accounts:login'
    ), name='logout'),

    path('register/', views.register_view, name='register'),
    

    # مسارات استعادة كلمة المرور
    path('password_reset/', 
         views.CustomPasswordResetView.as_view(
             template_name='accounts/password_reset_form.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url=reverse_lazy('accounts:password_reset_done'),
             html_email_template_name='accounts/password_reset_email.html',
             from_email=settings.DEFAULT_FROM_EMAIL,
             form_class=CustomPasswordResetForm
         ), 
         name='password_reset'),

    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url=reverse_lazy('accounts:password_reset_complete'),
             post_reset_login=True,
         ), 
         name='password_reset_confirm'),

    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),

    path('upload-logo/', views.upload_company_logo, name='upload_company_logo'),


    path('terms/', views.TermsView.as_view(), name='terms'),

    path('profile/', views.profile_view, name='profile'),


    

    path('logs/', views.system_logs_view, name='system_logs'),

    path('profile/', views.profile_view, name='profile'),
    
    
    # === مسارات تغيير كلمة المرور (الأسلوب الموصى به) ===
    path('change-password/', 
         auth_views.PasswordChangeView.as_view(
             template_name='accounts/change_password.html',
             success_url=reverse_lazy('accounts:change_password_done')
         ), 
         name='change_password'),

    path('change-password/done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='accounts/change_password_done.html'
         ), 
         name='change_password_done'),



    path('users/', views.user_list_view, name='user_list'),  # لعرض قائمة المستخدمين
    path('users/<int:pk>/edit/', views.user_edit_view, name='user_edit'),  # لتحرير مستخدم معين
    path('permissions/', views.permissions_view, name='permissions'),  # لصفحة الصلاحيات (تجريبية)

    path('company-settings/', views.company_settings_view, name='company_settings'),

    #path('force-change-password/', views.force_password_change, name='force_password_change'),

    #path('dashboard/', views.dashboard, name='dashboard'),

]