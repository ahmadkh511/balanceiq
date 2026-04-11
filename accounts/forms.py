from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError
from urllib.parse import urlparse
from .models import Profile


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'البريد الإلكتروني'
    }))
    
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'اسم المستخدم'
    }))
    
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'كلمة المرور'
    }))
    
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'تأكيد كلمة المرور'
    }))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        """
        التحقق من أن البريد الإلكتروني غير مسجل من قبل.
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("هذا البريد الإلكتروني مسجل بالفعل. يرجى استخدام بريد إلكتروني آخر.")
        return email


class UserUpdateForm(forms.ModelForm):
    """
    نموذج لتحديث بيانات المستخدم الأساسية (بدون كلمة المرور).
    """
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'username': 'اسم المستخدم',
            'email': 'البريد الإلكتروني',
            'first_name': 'الاسم الأول',
            'last_name': 'الاسم الأخير',
            'is_active': 'حساب نشط',
            'is_staff': 'موظف (صلاحيات إدارية)',
        }
    
    def clean_email(self):
        """
        التحقق من أن البريد الإلكتروني غير مستخدم من قبل (باستثناء المستخدم الحالي).
        """
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        
        # التحقق من وجود بريد إلكتروني مكرر (باستثناء المستخدم الحالي)
        if email and User.objects.filter(email__iexact=email).exclude(username=username).exists():
            raise forms.ValidationError("هذا البريد الإلكتروني مستخدم من قبل مستخدم آخر.")
        return email


class UserProfileUpdateForm(forms.ModelForm):
    """
    نموذج للمستخدم لتحديث بياناته الشخصية.
    """
    # === تعديل حقل الموقع الإلكتروني ===
    # نستخدم CharField بدلاً من URLField للسماح بإدخال النص العادي
    website_display = forms.CharField(
        label="الموقع الإلكتروني",
        required=False,
        widget=forms.TextInput(attrs={ # تم التغيير إلى TextInput
            'class': 'form-control',
            'placeholder': 'مثال: google.com أو a1syria.com'
        })
    )

    class Meta:
        model = Profile
        fields = [
            'profile_picture', 'full_name', 'phone_number', 'birth_date', 'gender',
            'address', 'city', 'country', 'postal_code', 'bio', 
            'facebook', 'twitter', 'instagram', 'linkedin', 'skills', 
            'job_title', 'company', 'experience_years', 'education_level',
            'university_major', 'languages', 'is_public', 'email_notifications',
        ]
        widgets = {
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الاسم الكامل'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الهاتف'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'العنوان'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'المدينة'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'البلد'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الرمز البريدي'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'نبذة شخصية'
            }),
            'facebook': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'رابط فيسبوك'
            }),
            'twitter': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'رابط تويتر'
            }),
            'instagram': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'رابط انستغرام'
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'رابط لينكدإن'
            }),
            'skills': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'المهارات (افصل بينها بفاصلة)'
            }),
            'job_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الوظيفة'
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الشركة'
            }),
            'experience_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'سنوات الخبرة'
            }),
            'education_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'university_major': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'التخصص الجامعي'
            }),
            'languages': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اللغات (افصل بينها بفاصلة)'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.website:
                self.fields['website_display'].initial = self.instance.website.replace('https://', '')

    def clean_website_display(self):
        """
        دالة تحقق مخصصة (custom clean method) لحقل الموقع الإلكتروني.
        تسمح بإدخال اسم النطاق فقط وتتحقق من صحته.
        """
        website = self.cleaned_data.get('website_display', '').strip()
        if not website:
            return '' # إذا كان الحقل فارغاً، لا تفعل شيئاً

        # تحقق مما إذا كان الرابط يحتوي على بروتوكول
        if not website.startswith(('http://', 'https://')):
            # إذا لم يكن كذلك، أضف https:// مؤقتاً للتحقق
            test_url = 'https://' + website
        else:
            test_url = website

        # استخدم urlparse لتحليل الرابط
        try:
            parsed = urlparse(test_url)
            # تحقق من وجود اسم نطاق (netloc) وأنه لا يحتوي على مسافات
            if not parsed.netloc or ' ' in website:
                raise ValidationError('الرجاء إدخال رابط موقع إلكتروني صالح، مثل example.com')
        except ValueError:
            raise ValidationError('الرجاء إدخال رابط موقع إلكتروني صالح.')

        return website # أعد القيمة الأصلية (بدون https)

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        website_val = self.cleaned_data.get('website_display', '').strip()
        
        if website_val:
            # أضف https:// فقط إذا لم يكن موجوداً
            if not website_val.startswith('http'):
                instance.website = 'https://' + website_val
            else:
                instance.website = website_val
        else:
            instance.website = ''
        
        if commit:
            instance.save()
        
        return instance


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="البريد الإلكتروني",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'class': 'form-control',
            'placeholder': 'البريد الإلكتروني'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise ValidationError("لا يوجد حساب مسجل بهذا البريد الإلكتروني.")
        return email

        



# accounts/forms.py - أضف هذا في نهاية الملف

from .models import CompanySettings




class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        fields = '__all__'
        widgets = {
            # الحقول الموجودة سابقاً
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_address': forms.TextInput(attrs={'class': 'form-control'}),
            'social_facebook': forms.URLInput(attrs={'class': 'form-control'}),
            'social_twitter': forms.URLInput(attrs={'class': 'form-control'}),
            'social_instagram': forms.URLInput(attrs={'class': 'form-control'}),
            'social_linkedin': forms.URLInput(attrs={'class': 'form-control'}),
            'footer_quick_links_title': forms.TextInput(attrs={'class': 'form-control'}),
            'footer_features_title': forms.TextInput(attrs={'class': 'form-control'}),
            'footer_contact_title': forms.TextInput(attrs={'class': 'form-control'}),
            'footer_copyright_text': forms.TextInput(attrs={'class': 'form-control'}),
            
            # ========== الحقول الجديدة (روابط سريعة) ==========
            'quick_link_support': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/support'}),
            'quick_link_guide': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/guide'}),
            'quick_link_faq': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/faq'}),
            
            # ========== الحقول الجديدة (روابط المميزات) ==========
            'feature_invoices': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/invoices'}),
            'feature_inventory': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/inventory'}),
            'feature_reports': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/reports'}),
        }
        labels = {
            # الحقول الموجودة سابقاً
            'company_name': 'اسم الشركة',
            'company_logo': 'شعار الشركة',
            'contact_email': 'البريد الإلكتروني',
            'contact_phone': 'رقم الهاتف',
            'contact_address': 'العنوان',
            'social_facebook': 'فيسبوك',
            'social_twitter': 'تويتر',
            'social_instagram': 'انستغرام',
            'social_linkedin': 'لينكد إن',
            'footer_quick_links_title': 'عنوان روابط سريعة',
            'footer_features_title': 'عنوان المميزات',
            'footer_contact_title': 'عنوان التواصل',
            'footer_copyright_text': 'نص حقوق النشر',
            
            # الحقول الجديدة
            'quick_link_support': 'رابط الدعم الفني',
            'quick_link_guide': 'رابط دليل الاستخدام',
            'quick_link_faq': 'رابط الأسئلة الشائعة',
            'feature_invoices': 'رابط إدارة الفواتير',
            'feature_inventory': 'رابط إدارة المخزون',
            'feature_reports': 'رابط التقارير الذكية',
        }


