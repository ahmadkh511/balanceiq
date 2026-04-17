# النظام والتسجيل
import logging
import uuid
import re
from decimal import Decimal

# المكتبات الخارجية
from num2words import num2words

# إطار عمل Django
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum, F
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _



from django.db import models
from django.core.exceptions import ValidationError


# التهيئة المحلية
logger = logging.getLogger(__name__)
User = get_user_model()



#----- جداول مساعدة  ---------




#================================================
#  الصندوق
# ===============================================

class CashTransaction(models.Model):
    """نموذج لتسجيل جميع حركات الصندوق"""
    TRANSACTION_TYPES = (
        ('purchase_payment', 'دفع مشتريات'),
        ('sale_receipt', 'تحصيل مبيعات'),
        ('purchase_return', 'مرتجع مشتريات'),
        ('sale_return', 'مرتجع مبيعات'),
        ('expense', 'مصروفات تشغيلية'),
        ('deposit', 'إيداع في الصندوق'),
        ('withdrawal', 'سحب من الصندوق'),
    )

    transaction_date = models.DateTimeField(default=timezone.now, verbose_name=_("تاريخ العملية"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("ملاحظات العملية"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                  null=True, blank=True, verbose_name=_("أجرى العملية"))

    amount_in = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                   verbose_name=_("المبلغ الداخل"))
    amount_out = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                    verbose_name=_("المبلغ الخارج"))

    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, 
                                       verbose_name=_("نوع العملية"))
    payment_method = models.ForeignKey('Payment_method', on_delete=models.SET_NULL, 
                                      null=True, blank=True, verbose_name=_("طريقة الدفع"))
    
    purchase_invoice = models.ForeignKey('Purch', on_delete=models.SET_NULL, 
                                        null=True, blank=True, related_name="cash_transactions",
                                        verbose_name=_("فاتورة المشتريات المرتبطة"))
    
    sale_invoice = models.ForeignKey('Sale', on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name="cash_transactions",
                                    verbose_name=_("فاتورة المبيعات المرتبطة"))

    sale_return = models.ForeignKey('SaleReturn', on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name="cash_transactions",
                                    verbose_name=_("مرتجع المبيعات المرتبط"))
    
    # === [إضافة جديدة] ===
    purchase_return = models.ForeignKey('PurchaseReturn', on_delete=models.SET_NULL, 
                                        null=True, blank=True, related_name="cash_transactions",
                                        verbose_name=_("مرتجع المشتريات المرتبط"))

    class Meta:
        verbose_name = _("حركة صندوق")
        verbose_name_plural = _("حركات الصندوق")
        ordering = ["-transaction_date"]

    def __str__(self):
        direction = "داخل" if self.amount_in > 0 else "خارج"
        amount = self.amount_in if self.amount_in > 0 else self.amount_out
        return f"{self.get_transaction_type_display()} - {amount} ({direction})"

    def clean(self):
        if self.amount_in > 0 and self.amount_out > 0:
            raise ValidationError(_("لا يمكن أن يكون المبلغ الداخل والخارج أكبر من صفر في نفس العملية."))
        if self.amount_in <= 0 and self.amount_out <= 0:
            raise ValidationError(_("يجب أن يكون إما المبلغ الداخل أو الخارج أكبر من صفر."))
        
        # ضبط طريقة الدفع نقداً تلقائياً للسحوبات والمصروفات
        if self.transaction_type in ['withdrawal', 'expense'] and not self.payment_method:
            try:
                cash_payment_method = Payment_method.objects.get(name='نقداً')
                self.payment_method = cash_payment_method
            except Payment_method.DoesNotExist:
                # إنشاء طريقة دفع نقداً إذا لم تكن موجودة
                cash_payment_method = Payment_method.objects.create(name='نقداً')
                self.payment_method = cash_payment_method

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_cash_balance(cls):
        total_in = cls.objects.aggregate(total=Sum('amount_in'))['total'] or Decimal('0.00')
        total_out = cls.objects.aggregate(total=Sum('amount_out'))['total'] or Decimal('0.00')
        return total_in - total_out



#================================================
#  اعدادات الايمل 
# ===============================================


class EmailSetting(models.Model):
    """
    نموذج لتخزين إعدادات البريد الإلكتروني في قاعدة البيانات
    بدلاً من ملف settings.py
    """
    email_backend = models.CharField(
        max_length=255, 
        default='django.core.mail.backends.smtp.EmailBackend',
        verbose_name="Email Backend"
    )
    email_host = models.CharField(max_length=255, verbose_name="SMTP Host (e.g., smtp.gmail.com)")
    email_port = models.PositiveIntegerField(default=587, verbose_name="Port")
    email_use_tls = models.BooleanField(default=True, verbose_name="Use TLS")
    email_host_user = models.EmailField(verbose_name="Email Address")
    email_host_password = models.CharField(
        max_length=255, 
        verbose_name="Email Password (App Password)",
        help_text="For Gmail, use App Password, not your account password."
    )
    default_from_email = models.EmailField(verbose_name="Default From Email")

    class Meta:
        verbose_name = "Email Setting"
        verbose_name_plural = "Email Settings"

    def __str__(self):
        return "Email Configuration"

    def clean(self):
        # ضمان وجود صف واحد فقط
        if not self.pk and EmailSetting.objects.exists():
            raise ValidationError("You can only have one Email Setting instance.")

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)




# ================ نماذج الأنظمة الأساسية ================

class Currency(models.Model):
    """نموذج العملات مع جميع الحقول المطلوبة"""
    code = models.CharField(max_length=3, unique=True, verbose_name=_("كود العملة"))
    symbol = models.CharField(max_length=10, verbose_name=_("رمز العملة"))
    name = models.CharField(max_length=100, verbose_name=_("الاسم بالإنجليزية"))
    name_ar = models.CharField(max_length=100, verbose_name=_("الاسم بالعربية"))
    singular_ar = models.CharField(max_length=100, verbose_name=_("المفرد بالعربية"), default="")
    dual_ar = models.CharField(max_length=100, verbose_name=_("المثنى بالعربية"), default="")
    plural_ar = models.CharField(max_length=100, verbose_name=_("الجمع بالعربية"), default="")
    fraction_name_ar = models.CharField(max_length=100, verbose_name=_("اسم الكسر"), default="")
    fraction_dual_ar = models.CharField(max_length=100, verbose_name=_("مثنى الكسر"), default="")
    fraction_plural_ar = models.CharField(max_length=100, verbose_name=_("جمع الكسر"), default="")
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('1.0000'),
                                       verbose_name=_("سعر الصرف"))
    decimals = models.PositiveSmallIntegerField(default=2, verbose_name=_("المنازل العشرية"))
    is_default = models.BooleanField(default=False, verbose_name=_("العملة الأساسية"))
    is_active = models.BooleanField(default=True, verbose_name=_("نشط"))
    
    class Meta:
        verbose_name = _("عملة")
        verbose_name_plural = _("العملات")
        ordering = ['code']
    
    def __str__(self):
        return f"{self.name_ar} ({self.code})"
    
    def save(self, *args, **kwargs):
        """ملء الحقول الفارغة تلقائياً"""
        if not self.singular_ar:
            self.singular_ar = self.name_ar
        
        if not self.dual_ar:
            if self.singular_ar.endswith('ة'):
                self.dual_ar = self.singular_ar[:-1] + "تان"
            else:
                self.dual_ar = self.singular_ar + "ان"
        
        if not self.plural_ar:
            if self.singular_ar.endswith('ة'):
                self.plural_ar = self.singular_ar[:-1] + "ات"
            else:
                self.plural_ar = self.singular_ar + "ات"
        
        if not self.fraction_name_ar:
            if self.code == 'SYP':
                self.fraction_name_ar = "قرش"
            elif self.code == 'SAR':
                self.fraction_name_ar = "هللة"
            elif self.code in ['USD', 'EUR']:
                self.fraction_name_ar = "سنت"
            else:
                self.fraction_name_ar = "جزء"
        
        if not self.fraction_dual_ar:
            self.fraction_dual_ar = self.fraction_name_ar + "ان"
        
        if not self.fraction_plural_ar:
            self.fraction_plural_ar = self.fraction_name_ar + "ات"
        
        if self.is_default:
            Currency.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)


class Payment_method(models.Model):
    """نموذج لطرق الدفع"""
    name = models.CharField(max_length=100, unique=True, verbose_name=_("الاسم"))
    notes = models.TextField(blank=True, verbose_name=_("ملاحظات"))
    uniqueId = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name=_("الرقم المسلسل"))
    slug = models.SlugField(max_length=225, unique=True, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث"))
    is_cash = models.BooleanField(default=False, verbose_name=_("هل هي طريقة دفع نقدية؟"))
    
    class Meta:
        verbose_name = _("طريقة دفع")
        verbose_name_plural = _("طرق الدفع")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.uniqueId:
            self.uniqueId = str(uuid.uuid4()).replace('-', '')[:10]
        if not self.slug:
            base_slug = slugify(self.name)
            unique_slug = base_slug
            num = 1
            while Payment_method.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)


class Shipping_com_m(models.Model):
    """نموذج لشركات الشحن"""
    name = models.CharField(max_length=100, unique=True, verbose_name=_("الاسم"))
    contact_person = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("شخص الاتصال"))
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("رقم الهاتف"))
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name=_("البريد الإلكتروني"))
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("العنوان"))
    notes = models.TextField(blank=True, verbose_name=_("ملاحظات"))
    uniqueId = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name=_("الرقم المسلسل"))
    slug = models.SlugField(max_length=225, unique=True, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث"))

    class Meta:
        verbose_name = _("شركة شحن")
        verbose_name_plural = _("شركات الشحن")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.uniqueId:
            self.uniqueId = str(uuid.uuid4()).replace('-', '')[:10]
        if not self.slug:
            base_slug = slugify(self.name)
            unique_slug = base_slug
            num = 1
            while Shipping_com_m.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)


class Status(models.Model):
    """نموذج لحالات الفواتير"""
    name = models.CharField(max_length=100, unique=True, verbose_name=_("الاسم"))
    notes = models.TextField(blank=True, verbose_name=_("ملاحظات"))
    uniqueId = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name=_("الرقم المسلسل"))
    slug = models.SlugField(max_length=225, unique=True, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث"))

    class Meta:
        verbose_name = _("حالة")
        verbose_name_plural = _("الحالات")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.uniqueId:
            self.uniqueId = str(uuid.uuid4()).replace('-', '')[:10]
        if not self.slug:
            base_slug = slugify(self.name)
            unique_slug = base_slug
            num = 1
            while Status.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)


class PriceType(models.Model):
    """نموذج لأنواع الأسعار"""
    name = models.CharField(max_length=100, verbose_name=_("نوع السعر"))
    description = models.TextField(blank=True, null=True, verbose_name=_("الوصف"))
    uniqueId = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name=_("الرقم المسلسل"))
    slug = models.SlugField(max_length=225, unique=True, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث"))

    class Meta:
        verbose_name = _('نوع السعر')
        verbose_name_plural = _('أنواع الأسعار')
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.uniqueId:
            self.uniqueId = str(uuid.uuid4()).replace('-', '')[:10]
        if not self.slug:
            base_slug = slugify(self.name)
            unique_slug = base_slug
            num = 1
            while PriceType.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)





#================================================
#  المنتجات   و الباركود 
# ===============================================

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import uuid
import re
from django.template.defaultfilters import slugify

class Product(models.Model):
    """نموذج المنتج"""
    product_name = models.CharField(max_length=255, verbose_name=_("اسم المادة"))
    product_description = models.TextField(blank=True, verbose_name=_("وصف المادة"))
    
    # === حقل الباركود الأساسي (الإضافة الجديدة) ===
    main_barcode = models.CharField(
        max_length=100, 
        unique=True, 
        blank=True, 
        null=True, 
        verbose_name=_("الباركودالأساسي"),
        help_text=_("ادخل الرمز الشريطي الرئيسي للمنتج")
    )

    # === حقل التصنيف ===
    category = models.ForeignKey(
        'Category', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name=_("التصنيف"),
        related_name='products',
        help_text=_("اختر التصنيف الذي يتبع له هذا المنتج (اختياري)")
    )

    # --- العملة والتكلفة ---
    foreign_currency = models.ForeignKey('Currency', on_delete=models.SET_NULL, null=True, blank=True, 
                                       verbose_name=_("العملة الأجنبية"), related_name="products")
    cost_in_foreign_currency = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'),
                                                 verbose_name=_("التكلفة بالعملة الأجنبية"))
    purch_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'),
                                     verbose_name=_("سعر الشراء الافتراضي"))
    
    # --- الأسعار الأساسية ---
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'),
                                   verbose_name=_("سعر البيع النهائي"))
    
    # --- هوامش الربح (للاستخدام في الحسابات اليدوية أو التلقائية) ---
    retail_profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('25.00'),
                                              verbose_name=_("هامش الربح للمفرق (%)"))
    semi_wholesale_profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20.00'),
                                                      verbose_name=_("هامش الربح لنصف الجملة (%)"))
    wholesale_profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('15.00'),
                                                 verbose_name=_("هامش الربح للجملة (%)"))
    
    price_adjustment = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'),
                                         verbose_name=_("تعديل السعر (+/-)"))
    
    # --- أسعار البيع (التي ستعرض وتحفظ) ---
    wholesale_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'),
                                        verbose_name=_("سعر البيع جملة"))
    semi_wholesale_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'),
                                             verbose_name=_("سعر البيع نصف جملة"))
    retail_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'),
                                     verbose_name=_("سعر البيع مفرق"))
    foreign_currency_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'),
                                               verbose_name=_("السعر بالعملة الأجنبية"))
    
    # --- حقول العروض الجديدة (من 1 إلى 6) ---
    # هذه الحقول لتخزين السعر الرقمي النهائي للعرض
    offer_1_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'),
                                      verbose_name=_("سعر العرض 1"))
    offer_2_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'),
                                      verbose_name=_("سعر العرض 2"))
    offer_3_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'),
                                      verbose_name=_("سعر العرض 3"))
    offer_4_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'),
                                      verbose_name=_("سعر العرض 4"))
    offer_5_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'),
                                      verbose_name=_("سعر العرض 5"))
    offer_6_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'),
                                      verbose_name=_("سعر العرض 6"))

    # --- المخزون والحسابات ---
    current_stock_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'),
                                                verbose_name=_("الكمية الحالية في المخزون"))
    average_purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'),
                                              verbose_name=_("متوسط تكلفة الشراء"))
    
    product_image = models.ImageField(upload_to='products/%Y/%m/%d/', blank=True, null=True,
                                     verbose_name=_("صورة المنتج"))
    
    OPERATION_TYPES = (
        ('purchase', 'مشتريات'),
        ('sale', 'مبيعات'),
    )
    last_operation_type = models.CharField(max_length=10, choices=OPERATION_TYPES, null=True, blank=True,
                                          verbose_name=_("نوع آخر عملية"))
    
    uniqueId = models.CharField(max_length=100, unique=True, blank=True, null=True,
                               verbose_name=_("الرقم المسلسل"))
    slug = models.SlugField(max_length=225, unique=True, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث"))
    
    class Meta:
        verbose_name = _("مادة")
        verbose_name_plural = _("المواد")
        ordering = ["-date_created"]
    
    def __str__(self):
        return self.product_name
    
    def save(self, *args, **kwargs):
        """
        دالة save المعدلة - تتعامل مع slugs السالبة بشكل آمن
        """
        # إنشاء uniqueId إذا لم يكن موجوداً
        if not self.uniqueId:
            self.uniqueId = str(uuid.uuid4()).replace('-', '')[:10]
        
        # معالجة slug بشكل صحيح
        needs_new_slug = False
        
        if not self.slug:
            needs_new_slug = True
        elif self.slug and self.slug.startswith('-'):
            needs_new_slug = True
        elif self.slug and (not self.slug.strip() or self.slug.isspace()):
            needs_new_slug = True
        
        if needs_new_slug:
            base_slug = slugify(self.product_name)
            
            if not base_slug or base_slug == '' or base_slug.isspace():
                base_slug = f"product-{self.uniqueId}"
            
            if base_slug.startswith('-'):
                base_slug = base_slug.lstrip('-')
            
            if base_slug.endswith('-'):
                base_slug = base_slug.rstrip('-')
            
            base_slug = re.sub(r'-+', '-', base_slug)
            
            if not base_slug or base_slug == '':
                base_slug = f"product-{self.id if self.id else self.uniqueId}"
            
            original_slug = base_slug
            counter = 1
            
            while Product.objects.filter(slug=base_slug).exclude(pk=self.pk if self.pk else None).exists():
                base_slug = f"{original_slug}-{counter}"
                counter += 1
                if counter > 100:
                    base_slug = f"{original_slug}-{self.uniqueId}"
                    break
            
            self.slug = base_slug
        
        # ملاحظة: تمت إزالة الحساب التلقائي للأسعار من هنا ليتم التحكم به عبر Views
        # كما طلبت، ليتم الحساب بناءً على مدخلات المستخدم في القالب
        
        super().save(*args, **kwargs)

    @property
    def primary_barcode(self):
        primary_barcode = self.barcodes.filter(is_primary=True).first()
        return primary_barcode.barcode_in if primary_barcode else None


class Barcode(models.Model):
    """نموذج للباركودات"""
    BARCODE_STATUS_CHOICES = [
        ('active', _('نشط')),
        ('returned', _('مرتجع')),
        ('sold', _('مباع')),
        ('damaged', _('تالف')),
        ('expired', _('منتهي الصلاحية')),
    ]
    
    barcode_in = models.CharField(max_length=255, unique=True, verbose_name=_("الباركود الداخل"))
    barcode_out = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("الباركود الخارج"))
    suffix = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("اللاحقة"))
    notes = models.TextField(blank=True, verbose_name=_("ملاحظات"))
    
    product = models.ForeignKey('Product', on_delete=models.CASCADE, 
                              related_name='barcodes', verbose_name=_("المنتج"))
    
    status = models.CharField(max_length=20, choices=BARCODE_STATUS_CHOICES, default='active',
                            verbose_name=_("حالة الباركود"))
    is_primary = models.BooleanField(default=False, verbose_name=_("باركود أساسي"))

    uniqueId = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name=_("الرقم المسلسل"))
    slug = models.SlugField(max_length=225, unique=True, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث"))

    class Meta:
        verbose_name = _("باركود")
        verbose_name_plural = _("باركودات")
        ordering = ["-date_created"]

    def __str__(self):
        return f"{self.barcode_in} - {self.product.product_name}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            Barcode.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        
        if not self.uniqueId:
            self.uniqueId = str(uuid.uuid4()).replace('-', '')[:10]
        if not self.slug:
            base_slug = slugify(f"{self.barcode_in}-{self.product.product_name}")
            unique_slug = base_slug
            num = 1
            while Barcode.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def is_available_for_sale(self):
        return self.status == 'active'



#================================================
#  المشتريات 
# ===============================================


class Purch(models.Model):
    """نموذج فاتورة المشتريات"""
    uniqueId = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name=_("الرقم المسلسل"))
    slug = models.SlugField(max_length=225, unique=True, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث"))
    _last_invoice_number = models.IntegerField(default=0, editable=False)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='purchases_created', verbose_name=_("تم الإنشاء بواسطة"))
    purch_supplier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='supplier_purchases', verbose_name=_("المورد"))
    
    purch_date = models.DateField(blank=True, null=True, verbose_name=_("تاريخ فاتورة الشراء"))
    purch_supplier_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("هاتف المورد"))
    purch_address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("عنوان المورد"))
    supplier_invoice_number = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("رقم فاتورة المورد"))
    purch_delivery_method = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("طريقة التسليم"))
    purch_delivery_tracking_number = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("رقم تتبع الشحنة"))
    purch_payment_method = models.ForeignKey('Payment_method', on_delete=models.SET_NULL, null=True, blank=True, 
                                           verbose_name=_("طريقة الدفع"))
    purch_notes = models.TextField(max_length=200, blank=True, verbose_name=_("ملاحظات الفاتورة"))
    purch_currency = models.ForeignKey('Currency', on_delete=models.SET_NULL, null=True, blank=True, 
                                     verbose_name=_("العملة"))
    purch_invoice_date = models.DateField(blank=True, null=True, verbose_name=_("تاريخ الفاتورة (من المورد)"))
    purch_type = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("نوع الشراء"))
    purch_status = models.ForeignKey('Status', on_delete=models.SET_NULL, null=True, blank=True, 
                                   verbose_name=_("حالة الفاتورة"))
    purch_shipping_company = models.ForeignKey('Shipping_com_m', on_delete=models.SET_NULL, null=True, blank=True, 
                                             verbose_name=_("شركة الشحن"))
    purch_shipping_num = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("رقم الشحنة"))
    purch_due_date = models.DateField(blank=True, null=True, verbose_name=_("تاريخ الاستحقاق"))
    purch_image = models.ImageField(upload_to='purch_invoice_images/%y/%m/%d/', blank=True, null=True, 
                                  verbose_name=_("صورة الفاتورة"))
    
    purch_tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), 
                                            verbose_name=_("نسبة الضريبة (%)"))
    purch_discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                       verbose_name=_("قيمة الخصم"))
    purch_addition = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                       verbose_name=_("قيمة الإضافة"))
    
    purch_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                         verbose_name=_("إجمالي البنود"))
    purch_tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                          verbose_name=_("قيمة الضريبة"))
    purch_final_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                           verbose_name=_("الإجمالي النهائي"))
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                     verbose_name=_("المبلغ المتبقي"))
    
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                     verbose_name=_("المبلغ المدفوع"))
    is_paid = models.BooleanField(default=False, verbose_name=_("تم الدفع بالكامل"))
    
    class Meta:
        verbose_name = _("فاتورة شراء")
        verbose_name_plural = _("فواتير الشراء")
        ordering = ["-date_created"]
    
    def __str__(self):
        return f"فاتورة شراء {self.uniqueId}"
    
    def save(self, *args, **kwargs):
        if not self.purch_date:
            self.purch_date = timezone.now().date()
        if not self.purch_invoice_date:
            self.purch_invoice_date = self.purch_date
        
        if not self.uniqueId:
            last_invoice = Purch.objects.order_by('-_last_invoice_number').first()
            last_number = last_invoice._last_invoice_number if last_invoice else 0
            new_number = last_number + 1
            self._last_invoice_number = new_number
            self.uniqueId = f"P{new_number:04d}"
        
        if not self.slug:
            self.slug = slugify(f"purch-{self.uniqueId}")
        
        super().save(*args, **kwargs)
    
    def clean_arabic_words(self, text):
        """تنظيف وتحسين النص العربي"""
        corrections = {
            'واحد': 'واحد',
            'اثنان': 'اثنان',
            'اثنين': 'اثنين',
            'ثلاثة': 'ثلاثة',
            'أربعة': 'أربعة',
            'خمسة': 'خمسة',
            'ستة': 'ستة',
            'سبعة': 'سبعة',
            'ثمانية': 'ثمانية',
            'تسعة': 'تسعة',
            'عشرة': 'عشرة',
            'مئة': 'مائة',
            'مئتان': 'مئتان',
            'مئتين': 'مئتين',
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        return text
    
    def get_amount_parts(self):
        """تقسيم المبلغ إلى جزء صحيح وكسري"""
        if not self.purch_final_total:
            return 0, 0
        
        amount = float(self.purch_final_total)
        currency_info = self.get_currency_info()
        decimals = currency_info.get('decimals', 2)
        
        integer_part = int(amount)
        fractional_part = int(round((amount - integer_part) * (10 ** decimals)))
        
        return integer_part, fractional_part
    
    @property
    def total_in_words(self):
        """تحويل الإجمالي إلى كلمات عربية"""
        return self.get_total_in_words()
    
    def get_total_in_words(self):
        """الدالة الرئيسية لتحويل الإجمالي إلى كلمات"""
        if not self.purch_final_total:
            return ""
        
        try:
            currency_info = self.get_currency_info()
            integer_part, fractional_part = self.get_amount_parts()
            
            # تحويل الجزء الصحيح
            integer_words = num2words(integer_part, lang='ar')
            integer_words = self.clean_arabic_words(integer_words)
            
            # تحديد صيغة العملة
            if integer_part == 0:
                currency_word = currency_info['singular']
            elif integer_part == 1:
                currency_word = currency_info['singular']
            elif integer_part == 2:
                currency_word = currency_info['dual']
            elif integer_part <= 10:
                currency_word = currency_info['singular']
            else:
                currency_word = currency_info['plural']
            
            # بناء النتيجة
            result = f"{integer_words} {currency_word}".strip()
            
            # إضافة الجزء الكسري
            if fractional_part > 0:
                fraction_words = num2words(fractional_part, lang='ar')
                fraction_words = self.clean_arabic_words(fraction_words)
                
                # تحديد صيغة الكسر
                if fractional_part == 1:
                    fraction_currency = currency_info['fraction']
                elif fractional_part == 2:
                    fraction_currency = currency_info['fraction_dual']
                elif fractional_part <= 10:
                    fraction_currency = currency_info['fraction']
                else:
                    fraction_currency = currency_info['fraction_plural']
                
                if integer_part == 0:
                    result = f"{fraction_words} {fraction_currency}"
                else:
                    result += f" و{fraction_words} {fraction_currency}"
            
            result += " فقط لا غير"
            
            return result
            
        except Exception as e:
            logger.error(f"خطأ في تحويل المبلغ إلى كلمات: {e}", exc_info=True)
            currency_name = currency_info.get('singular', 'ليرة سورية') if 'currency_info' in locals() else 'ليرة سورية'
            return f"{self.purch_final_total} {currency_name} فقط لا غير"
    
    def get_currency_info(self):
        """الحصول على معلومات العملة"""
        if not self.purch_currency:
            return {
                'name': 'ليرة سورية',
                'singular': 'ليرة سورية',
                'dual': 'ليرتان سوريتان',
                'plural': 'ليرات سورية',
                'fraction': 'قرش',
                'fraction_dual': 'قرشان',
                'fraction_plural': 'قروش',
                'decimals': 2
            }
        
        return {
            'name': self.purch_currency.name_ar,
            'singular': self.purch_currency.singular_ar,
            'dual': self.purch_currency.dual_ar,
            'plural': self.purch_currency.plural_ar,
            'fraction': self.purch_currency.fraction_name_ar,
            'fraction_dual': self.purch_currency.fraction_dual_ar,
            'fraction_plural': self.purch_currency.fraction_plural_ar,
            'decimals': self.purch_currency.decimals
        }
    
    def calculate_and_save_totals(self):
        """حساب وتحديث جميع الإجماليات المالية"""
        try:
            self.purch_subtotal = self.purchitem_set.aggregate(total_sum=Sum('purch_total'))['total_sum'] or Decimal('0.00')
            self.purch_tax_amount = (self.purch_subtotal * (self.purch_tax_percentage / Decimal('100.00'))).quantize(Decimal('0.01'))
            self.purch_final_total = self.purch_subtotal + self.purch_tax_amount + self.purch_addition - self.purch_discount
            self.balance_due = max(self.purch_final_total - self.paid_amount, Decimal('0.00'))
            self.is_paid = self.paid_amount >= self.purch_final_total
            
            super().save(update_fields=[
                'purch_subtotal', 'purch_tax_amount', 'purch_final_total', 
                'balance_due', 'is_paid', 'purch_tax_percentage', 'purch_discount', 'purch_addition', 'paid_amount'
            ])
            
            logger.info(f"تم تحديث الإجماليات المالية: الإجمالي {self.purch_final_total}")
            
        except Exception as e:
            logger.error(f"خطأ في حساب الإجماليات المالية: {e}")
            raise
    
    def update_financial_fields(self, tax_percentage, discount, addition, paid_amount):
        """تحديث الحقول المالية يدوياً"""
        try:
            self.purch_tax_percentage = Decimal(str(tax_percentage))
            self.purch_discount = Decimal(str(discount))
            self.purch_addition = Decimal(str(addition))
            self.paid_amount = Decimal(str(paid_amount))
            self.calculate_and_save_totals()
            
            logger.info(f"تم تحديث الحقول المالية للفاتورة {self.uniqueId}")
            
        except Exception as e:
            logger.error(f"خطأ في تحديث الحقول المالية: {e}")
            raise
    
    def create_cash_transaction(self):
        """إنشاء حركة صندوق مرتبطة بالفاتورة"""
        from .models import CashTransaction
        
        existing_transaction = CashTransaction.objects.filter(
            purchase_invoice=self,
            transaction_type='purchase_payment'
        ).first()
        
        if not existing_transaction and self.paid_amount > 0:
            CashTransaction.objects.create(
                transaction_date=timezone.now(),
                amount_out=self.paid_amount,
                transaction_type='purchase_payment',
                payment_method=self.purch_payment_method,
                purchase_invoice=self,
                notes=f"دفعة مقابل فاتورة شراء {self.uniqueId}",
                created_by=self.created_by
            )
        elif existing_transaction and existing_transaction.amount_out != self.paid_amount:
            existing_transaction.amount_out = self.paid_amount
            existing_transaction.save()
    
    @property
    def total_items_count(self):
        if self.pk is None:
            return 0
        return self.purchitem_set.count()
    
    @property
    def total_quantity_purchased(self):
        if self.pk is None:
            return Decimal('0.00')
        total_qty = self.purchitem_set.aggregate(total_qty=Sum('purchased_quantity'))['total_qty']
        return total_qty or Decimal('0.00')

    # أضف هذه الخاصية داخل كلاس Purch في models.py

    @property
    def has_return(self):
        """للتحقق مما إذا كانت الفاتورة لها مرتجعات"""
        return self.purchase_returns.exists()


class PurchItem(models.Model):
    """نموذج بنود فاتورة المشتريات"""
    purch = models.ForeignKey('Purch', on_delete=models.CASCADE, verbose_name=_("فاتورة الشراء"))
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='purch_items', verbose_name=_("المنتج المرتبط"))
    
    item_name = models.CharField(max_length=255, blank=True, verbose_name=_("اسم المادة"))
    purchased_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'), 
                                           verbose_name=_("الكمية المشتراة"))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                   verbose_name=_("سعر الوحدة"))
    
    notes = models.CharField(max_length=255, blank=True, verbose_name=_("ملاحظات"))
    purch_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                    verbose_name=_("إجمالي البند"))
    
    purch_currency = models.ForeignKey("Currency", on_delete=models.PROTECT, 
                                     related_name='purch_items_by_currency', 
                                     verbose_name=_("عملة الشراء لهذا البند"), null=True, blank=True)
    exchange_rate_at_purchase = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('1.00'), 
                                                  verbose_name=_("سعر الصرف وقت الشراء"))
    unit_price_base_currency = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                                 verbose_name=_("سعر الوحدة (بالعملة الأساسية)"))
    
    purch_item_image = models.ImageField(upload_to='purch_items_image/%y/%m/%d/', max_length=100, 
                                       blank=True, null=True, verbose_name=_("صورة المادة"))
    
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث"))

    class Meta:
        verbose_name = _("بند فاتورة الشراء")
        verbose_name_plural = _("بنود فواتير الشراء")
        ordering = ["id"]

    def __str__(self):
        if self.product:
            return f"{self.product.product_name} - {self.purchased_quantity} × {self.unit_price} = {self.purch_total}"
        return f"{self.item_name} - {self.purchased_quantity} × {self.unit_price} = {self.purch_total}"
    
    def save(self, *args, **kwargs):
        """
        دالة save المعدلة - لا تقوم بتحديث المخزون تلقائياً
        يتم تحديث المخزون من views عند الحاجة فقط
        """
        if not self.item_name and self.product:
            self.item_name = self.product.product_name
        elif not self.item_name:
            self.item_name = "مادة غير محددة"
        
        # حساب الإجمالي
        if self.purchased_quantity and self.unit_price:
            subtotal = self.purchased_quantity * self.unit_price
            self.purch_total = subtotal.quantize(Decimal('0.01'))
        
        # حساب سعر الوحدة بالعملة الأساسية
        try:
            self.unit_price_base_currency = self.unit_price
        except Exception:
            self.unit_price_base_currency = self.unit_price
        
        # حفظ البند بدون تحديث المخزون
        super().save(*args, **kwargs)
    


# في ملف models.py، داخل كلاس PurchItem

    def update_product_stock(self, old_quantity=None, old_product=None):
        """
        دالة منفصلة لتحديث المخزون يمكن استدعاؤها حسب الحاجة
        (نسخة مشخصة للفحص)
        """
        try:
            if not self.product:
                logger.warning(f"⚠️ لا يوجد منتج مرتبط بالبند: {self.id}")
                return
            
            product = self.product
            
            # === بداية قسم التشخيص ===
            print("="*50)
            print(f"🔍 تشخيص تحديث المخزون للبند رقم: {self.id}")
            print(f"🔍 المنتج: {product.product_name}")
            
            # قراءة قيم المنتج الحالية من قاعدة البيانات مباشرة
            product.refresh_from_db()
            print(f"📊 حالة المنتج قبل التحديث:")
            print(f"   - الكمية الحالية (current_stock_quantity): {product.current_stock_quantity}")
            print(f"   - متوسط التكلفة (average_purchase_cost): {product.average_purchase_cost}")
            print(f"📊 بيانات الفاتورة الجديدة:")
            print(f"   - الكمية المشتراة (purchased_quantity): {self.purchased_quantity}")
            print(f"   - سعر الوحدة (unit_price_base_currency): {self.unit_price_base_currency}")
            print(f"📊 بيانات التعديل (إن وجدت):")
            print(f"   - الكمية القديمة (old_quantity): {old_quantity}")
            print(f"   - المنتج القديم (old_product): {old_product.product_name if old_product else 'None'}")
            print("="*50)
            # === نهاية قسم التشخيص ===

            if old_quantity is not None and old_product is not None:
                # حالة التعديل: خصم الكمية القديمة أولاً
                logger.info(f"🔄 تعديل مخزون: بند {self.id}, منتج {product.product_name}")
                logger.info(f"📊 الكمية القديمة: {old_quantity}, المنتج القديم: {old_product.product_name if old_product else 'لا يوجد'}")
                logger.info(f"📊 الكمية الجديدة: {self.purchased_quantity}, المنتج الجديد: {product.product_name}")
                
                if old_product and product.id == old_product.id:
                    # نفس المنتج، احسب الفرق
                    quantity_difference = self.purchased_quantity - Decimal(str(old_quantity))
                    logger.info(f"📊 فرق الكمية لنفس المنتج: {quantity_difference}")
                    
                    # تحديث المخزون
                    product.current_stock_quantity += quantity_difference
                    
                    # تحديث متوسط التكلفة
                    if product.current_stock_quantity > 0:
                        if quantity_difference > 0:
                            # إضافة كمية جديدة
                            current_stock = Decimal(str(product.current_stock_quantity))
                            quantity_diff_dec = Decimal(str(quantity_difference))
                            
                            old_total_value = (current_stock - quantity_diff_dec) * product.average_purchase_cost
                            new_total_value = old_total_value + (quantity_diff_dec * self.unit_price_base_currency)
                            product.average_purchase_cost = (new_total_value / current_stock).quantize(Decimal('0.01'))
                        elif quantity_difference < 0:
                            # تقليل الكمية
                            product.average_purchase_cost = product.average_purchase_cost  # يبقى كما هو
                    
                else:
                    # منتج مختلف: خصم من القديم، أضف للجديد
                    if old_product:
                        old_product.refresh_from_db()
                        old_product.current_stock_quantity -= Decimal(str(old_quantity))
                        old_product.save()
                        logger.info(f"📉 خصم من المنتج القديم: {old_quantity}")
                    
                    # أضف للمنتج الجديد
                    product.current_stock_quantity += self.purchased_quantity
                    product.average_purchase_cost = self.unit_price_base_currency
                    logger.info(f"📈 إضافة للمنتج الجديد: {self.purchased_quantity}")
                        
            else:
                # حالة الإنشاء الجديد
                logger.info(f"🆕 إنشاء مخزون جديد: بند {self.id}, منتج {product.product_name}")
                
                # === نقطة الاشتباه الرئيسية ===
                # هنا نضيف الكمية المشتراة مباشرة للكمية الحالية
                # إذا كانت الكمية الحالية هي "الكمية المبدئية"، فسيتم جمعها مع كمية الشراء
                product.current_stock_quantity += self.purchased_quantity
                
                # تحديث متوسط التكلفة للإنشاء الجديد
                if product.current_stock_quantity > 0:
                    old_total_value = (product.current_stock_quantity - self.purchased_quantity) * product.average_purchase_cost
                    new_total_value = old_total_value + (self.purchased_quantity * self.unit_price_base_currency)
                    product.average_purchase_cost = (new_total_value / product.current_stock_quantity).quantize(Decimal('0.01'))
            
            # تحديث نوع آخر عملية
            product.last_operation_type = 'purchase'
            
            # حفظ المنتج
            product.save()
            
            # === تشخيص ما بعد الحفظ ===
            print(f"✅ تم تحديث مخزون المنتج {product.product_name} إلى: {product.current_stock_quantity}")
            print(f"💰 متوسط التكلفة الجديد: {product.average_purchase_cost}")
            print("="*50)
            # === نهاية التشخيص ===
            
            logger.info(f"✅ تم تحديث مخزون المنتج {product.product_name} إلى: {product.current_stock_quantity}")
            logger.info(f"💰 متوسط التكلفة: {product.average_purchase_cost}")
                
        except Product.DoesNotExist:
            logger.error(f"❌ المنتج غير موجود: {self.product_id}")
        except Exception as e:
            # === تشخيص الخطأ ===
            print(f"❌❌❌ خطأ في تحديث المخزون للبند {self.id}: {e}")
            import traceback
            traceback.print_exc() # هذا سيطبع الخطأ بالتفصيل في الكونسول
            logger.error(f"❌ خطأ في تحديث المخزون: {e}")
            import traceback
            logger.error(traceback.format_exc())


        def delete(self, *args, **kwargs):
            """
            دالة حذف البند مع تراجع المخزون
            """
            try:
                # حفظ بيانات المنتج والكمية قبل الحذف
                product = self.product
                purchased_quantity = self.purchased_quantity
                
                if product:
                    # تراجع عن المخزون
                    product.current_stock_quantity -= purchased_quantity
                    
                    # تحديث متوسط التكلفة إذا بقي مخزون
                    if product.current_stock_quantity > 0:
                        # إعادة حساب متوسط التكلفة بعد حذف الكمية
                        old_total_value = product.current_stock_quantity * product.average_purchase_cost
                        removed_value = purchased_quantity * self.unit_price_base_currency
                        new_total_value = old_total_value - removed_value
                        
                        if new_total_value > 0:
                            product.average_purchase_cost = (new_total_value / product.current_stock_quantity).quantize(Decimal('0.01'))
                        else:
                            product.average_purchase_cost = Decimal('0.00')
                    
                    product.save()
                    logger.info(f"↩️ تم التراجع عن مخزون المنتج بعد الحذف: {product.product_name}")
                
                # حذف البند
                super().delete(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"❌ خطأ في حذف البند: {e}")
                raise

class PurchItemBarcode(models.Model):
    """نموذج لربط الباركودات ببنود فواتير الشراء - معدل"""
    purch_item = models.ForeignKey('PurchItem', on_delete=models.CASCADE, 
                                 related_name='item_barcodes', verbose_name=_("بند الشراء"))
    barcode = models.ForeignKey('Barcode', on_delete=models.CASCADE, 
                              related_name='purch_items', verbose_name=_("الباركود"))
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'),
                                      verbose_name=_("الكمية المرتبطة"))
    
    barcode_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'نشط'),
            ('returned', 'مرتجع'),
            ('damaged', 'تالف'),
        ],
        default='active',
        verbose_name=_("حالة الباركود في الفاتورة")
    )
    
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث"))

    class Meta:
        verbose_name = _("باركود بند الشراء")
        verbose_name_plural = _("باركودات بنود الشراء")
        unique_together = ('purch_item', 'barcode')
        ordering = ['-date_created']

    def __str__(self):
        return f"{self.purch_item.item_name} - {self.barcode.barcode_in}"

    def save(self, *args, **kwargs):
        if not self.barcode_status:
            self.barcode_status = 'active'
        
        # تحديث حالة الباركود الرئيسي
        if self.barcode_status == 'active':
            self.barcode.status = 'active'
        elif self.barcode_status == 'returned':
            self.barcode.status = 'returned'
        elif self.barcode_status == 'damaged':
            self.barcode.status = 'damaged'
        
        self.barcode.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """تجاوز دالة الحذف للتحقق من الباركودات غير المستخدمة"""
        barcode_to_check = self.barcode
        super().delete(*args, **kwargs)
        
        # التحقق إذا كان الباركود مستخدم في أي علاقة أخرى
        if not PurchItemBarcode.objects.filter(barcode=barcode_to_check).exists():
            # إذا لم يكن مستخدم في أي علاقة أخرى، يمكن حذفه
            if not hasattr(barcode_to_check, 'sale_items') or not barcode_to_check.sale_items.exists():
                if not hasattr(barcode_to_check, 'inventory_items') or not barcode_to_check.inventory_items.exists():
                    barcode_to_check.delete()





#================================================
#           مرتجع المشتريات 
# ===============================================


class PurchaseReturn(models.Model):
    """نموذج فاتورة مرتجع المشتريات"""
    
    # إضافة خيارات حالة التسوية
    SETTLEMENT_STATUS = (
        ('pending', 'في انتظار الاستلام'),
        ('partial', 'تم الاستلام جزئياً'),
        ('settled', 'تم الاستلام كاملاً'),
    )
    
    # الحقول الموجودة (كما هي)
    original_purchase = models.ForeignKey('Purch', on_delete=models.CASCADE, 
                                        related_name='purchase_returns', 
                                        verbose_name=_("فاتورة الشراء الأصلية"))
    uniqueId = models.CharField(max_length=100, unique=True, blank=True, null=True, 
                               verbose_name=_("الرقم المسلسل"))
    slug = models.SlugField(max_length=225, unique=True, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث"))
    _last_return_number = models.IntegerField(default=0, editable=False)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='returns_created', verbose_name=_("تم الإنشاء بواسطة"))
    
    return_date = models.DateField(default=timezone.now, verbose_name=_("تاريخ المرتجع"))
    return_notes = models.TextField(max_length=500, blank=True, verbose_name=_("ملاحظات المرتجع"))
    
    purch_supplier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='supplier_returns', verbose_name=_("المورد"))
    purch_currency = models.ForeignKey('Currency', on_delete=models.SET_NULL, null=True, blank=True, 
                                     verbose_name=_("العملة"))
    
    return_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                         verbose_name=_("إجمالي بنود المرتجع"))
    return_tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                          verbose_name=_("قيمة الضريبة المعادة"))
    return_final_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                           verbose_name=_("الإجمالي النهائي للمرتجع"))
    
    # ========== الحقول الجديدة للتسوية المالية ==========
    paid_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name=_("المبلغ المستلم من المورد")
    )
    
    remaining_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name=_("المبلغ المتبقي للمورد")
    )
    
    settlement_status = models.CharField(
        max_length=20,
        choices=SETTLEMENT_STATUS,
        default='pending',
        verbose_name=_("حالة التسوية المالية")
    )
    
    # ========== نهاية الحقول الجديدة ==========

    class Meta:
        verbose_name = _("فاتورة مرتجع شراء")
        verbose_name_plural = _("فواتير مرتجع الشراء")
        ordering = ["-date_created"]
    
    def __str__(self):
        return f"مرتجع شراء {self.uniqueId} لفاتورة {self.original_purchase.uniqueId}"
    
    def save(self, *args, **kwargs):
        # إنشاء الرقم المسلسل (كما هو)
        if not self.uniqueId:
            last_return = PurchaseReturn.objects.order_by('-_last_return_number').first()
            if last_return:
                last_number = last_return._last_return_number
            else:
                last_number = 0
            
            new_number = last_number + 1
            self._last_return_number = new_number
            self.uniqueId = f"PR{new_number:05d}"
        else:
            try:
                if self.uniqueId.startswith('PR'):
                    num_part = self.uniqueId[2:]
                    self._last_return_number = int(num_part)
            except (ValueError, IndexError):
                pass
        
        # إنشاء slug (كما هو)
        if not self.slug:
            self.slug = slugify(f"purchase-return-{self.uniqueId}")
        
        # تعيين المورد والعملة من الفاتورة الأصلية (كما هو)
        if self.original_purchase:
            if not self.purch_supplier:
                self.purch_supplier = self.original_purchase.purch_supplier
            if not self.purch_currency and hasattr(self.original_purchase, 'purch_currency'):
                self.purch_currency = self.original_purchase.purch_currency
        
        # حساب المبلغ المتبقي قبل الحفظ
        self.remaining_amount = self.return_final_total - self.paid_amount
        
        # تحديث حالة التسوية
        self.update_settlement_status()
        
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"خطأ في حفظ PurchaseReturn: {e}")
            raise

    def calculate_and_save_totals(self):
        """حساب وتحديث جميع الإجماليات المالية للمرتجع"""
        try:
            total_result = self.return_items.aggregate(
                total_sum=Sum('return_total')
            )
            return_subtotal = total_result['total_sum'] or Decimal('0.00')
            
            self.return_subtotal = return_subtotal
            self.return_final_total = return_subtotal
            
            # تحديث المبلغ المتبقي بناءً على الإجمالي الجديد
            self.remaining_amount = self.return_final_total - self.paid_amount
            
            self.save(update_fields=['return_subtotal', 'return_final_total', 'remaining_amount'])
            
            logger.info(f"تم تحديث الإجماليات المالية لمرتجع: {self.uniqueId}")
            return True
        except Exception as e:
            logger.error(f"خطأ في حساب إجماليات المرتجع {self.uniqueId}: {e}")
            return False

    def update_settlement_status(self):
        """تحديث حالة التسوية بناءً على المبالغ"""
        if self.remaining_amount <= 0:
            self.settlement_status = 'settled'
        elif self.paid_amount > 0:
            self.settlement_status = 'partial'
        else:
            self.settlement_status = 'pending'
    
    def get_available_items_for_return(self):
        """الحصول على البنود المتاحة للإرجاع (كما هو)"""
        items_data = []
        
        if not self.original_purchase:
            return items_data
            
        for original_item in self.original_purchase.purchitem_set.all():
            total_returned = original_item.returned_items.aggregate(
                total=Sum('returned_quantity')
            )['total'] or Decimal('0.00')
            
            available_quantity = original_item.purchased_quantity - total_returned
            
            if available_quantity > 0:
                items_data.append({
                    'original_item': original_item,
                    'available_quantity': available_quantity,
                    'previously_returned': total_returned,
                })
        
        return items_data


class PurchaseReturnItem(models.Model):
    """نموذج بنود فاتورة مرتجع المشتريات"""
    purchase_return = models.ForeignKey(PurchaseReturn, on_delete=models.CASCADE, 
                                       related_name='return_items', verbose_name=_("فاتورة المرتجع"))
    original_item = models.ForeignKey('PurchItem', on_delete=models.CASCADE, 
                                     related_name='returned_items', verbose_name=_("بند الشراء الأصلي"))
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True, 
                              verbose_name=_("المادة"))
    
    purchased_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), 
                                           verbose_name=_("الكمية الأساسية (من الفاتورة الأصلية)"))
    
    returned_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), 
                                           verbose_name=_("الكمية المرتجعة"))
    
    return_unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                          verbose_name=_("سعر الوحدة (إجمالي المرتجع للوحدة)"))
    
    return_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                      verbose_name=_("إجمالي المرتجع للبند"))
    
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث"))

    class Meta:
        verbose_name = _("بند مرتجع الشراء")
        verbose_name_plural = _("بنود مرتجع الشراء")
        ordering = ["id"]

    def __str__(self):
        product_name = self.product.product_name if self.product else 'غير محدد'
        return f"مرتجع {product_name} - {self.returned_quantity} × {self.return_unit_price}"

    def save(self, *args, **kwargs):
        if self.original_item:
            if not self.product:
                self.product = self.original_item.product
            if not self.purchased_quantity:
                self.purchased_quantity = self.original_item.purchased_quantity
            if not self.return_unit_price:
                self.return_unit_price = self.original_item.unit_price
        
        if self.returned_quantity and self.return_unit_price:
            self.return_total = Decimal(str(self.returned_quantity)) * Decimal(str(self.return_unit_price))
            self.return_total = self.return_total.quantize(Decimal('0.01'))
        
        super().save(*args, **kwargs)
        
        if self.product and self.returned_quantity > Decimal('0.00'):
            try:
                # استخدام F expression لتجنب مشاكل التزامن
                self.product.current_stock_quantity = F('current_stock_quantity') - self.returned_quantity
                self.product.save(update_fields=['current_stock_quantity'])
                logger.info(f"تم إنقاص مخزون {self.product.product_name} بمقدار {self.returned_quantity}")
            except Exception as e:
                logger.error(f"خطأ في تحديث المخزون: {e}")

    def delete(self, *args, **kwargs):
        if self.product and self.returned_quantity > Decimal('0.00'):
            try:
                self.product.current_stock_quantity = F('current_stock_quantity') + self.returned_quantity
                self.product.save(update_fields=['current_stock_quantity'])
                logger.info(f"تم إرجاع الكمية {self.returned_quantity} للمخزون بعد حذف بند المرتجع")
            except Exception as e:
                logger.error(f"خطأ في استعادة المخزون: {e}")
        
        super().delete(*args, **kwargs)



class PurchaseReturnItemBarcode(models.Model):
    """نموذج لربط باركود معين ببند مرتجع المشتريات"""
    purchase_return_item = models.ForeignKey('PurchaseReturnItem', on_delete=models.CASCADE, 
                                           related_name='returned_barcodes', verbose_name=_("بند المرتجع"))
    barcode = models.ForeignKey('Barcode', on_delete=models.CASCADE, 
                              related_name='purchase_return_items', verbose_name=_("الباركود المرتجع"))
    
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))

    class Meta:
        verbose_name = _("باركود بند المرتجع")
        verbose_name_plural = _("باركودات بنود المرتجع")
        unique_together = ('purchase_return_item', 'barcode')

    def __str__(self):
        return f"مرتجع: {self.barcode.barcode_in} لـ {self.purchase_return_item.product.product_name if self.purchase_return_item.product else 'N/A'}"

    def save(self, *args, **kwargs):
        """
        عند حفظ باركود المرتجع:
        1. نحذف رابط الباركود من جدول مشتريات المورد (PurchItemBarcode) لأنه لم يعد ضمن مخزوننا.
        2. نغير حالة الباركود نفسه إلى 'returned' بدلاً من حذفه من قاعدة البيانات.
        """
        super().save(*args, **kwargs)
        
        # استيراد النموذج داخل الدالة لتجنب الاستيراد الدائري
        from invoice.models import PurchItemBarcode
        
        # 1. حذف الربط مع فاتورة الشراء الأصلية (لأنه خرج من المخزون)
        PurchItemBarcode.objects.filter(barcode=self.barcode).delete()
        
        # 2. تغيير حالة الباركود إلى 'returned' بدلاً من حذفه
        # نفترض أن نموذج Barcode يحتوي على حقل status أو barcode_status
        # إذا كان اسم الحقل مختلفاً يرجى تعديله ليطابق نموذجك
        if hasattr(self.barcode, 'status'):
            self.barcode.status = 'returned' 
            self.barcode.save(update_fields=['status'])
            logger.info(f"تم تغيير حالة الباركود {self.barcode.barcode_in} إلى 'مرتجع'")
        elif hasattr(self.barcode, 'barcode_status'):
             self.barcode.barcode_status = 'returned'
             self.barcode.save(update_fields=['barcode_status'])
             logger.info(f"تم تغيير حالة الباركود {self.barcode.barcode_in} إلى 'مرتجع'")
        else:
            # في حال لا يوجد حقل حالة، نكتفي بتسجيل المعلومة
            logger.warning(f"تم ربط الباركود {self.barcode.barcode_in} بالمرتجع ولكن لم يتم العثور على حقل حالة لتحديثه")

    def delete(self, *args, **kwargs):
        """
        عند حذف سجل المرتجع (إلغاء العملية):
        1. نعيد حالة الباركود إلى 'active'.
        2. نعيد ربطه بفاتورة الشراء الأصلية (PurchItemBarcode) ليظهر في المخزون مجدداً.
        """
        from invoice.models import PurchItemBarcode
        
        barcode_instance = self.barcode
        original_item = self.purchase_return_item.original_item
        
        # 1. إعادة إنشاء رابط المخزون (PurchItemBarcode)
        # نتأكد من عدم وجوده مسبقاً لتفادي التكرار
        if original_item:
            PurchItemBarcode.objects.get_or_create(
                purch_item=original_item,
                barcode=barcode_instance,
                defaults={'barcode_status': 'active'}
            )
            logger.info(f"تم إعادة ربط الباركود {barcode_instance.barcode_in} بالمخزون")

        # 2. إعادة حالة الباركود إلى نشط
        if hasattr(barcode_instance, 'status'):
            barcode_instance.status = 'active'
            barcode_instance.save(update_fields=['status'])
        elif hasattr(barcode_instance, 'barcode_status'):
            barcode_instance.barcode_status = 'active'
            barcode_instance.save(update_fields=['barcode_status'])
            
        logger.info(f"تم استعادة حالة الباركود {barcode_instance.barcode_in} إلى 'نشط'")
        
        super().delete(*args, **kwargs)


#=========================================
#             المبيعات 
# ========================================


class Sale(models.Model):
    """نموذج فاتورة المبيعات - معكوس من نموذج المشتريات"""
    uniqueId = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name=_("الرقم المسلسل"))
    slug = models.SlugField(max_length=225, unique=True, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث"))
    _last_invoice_number = models.IntegerField(default=0, editable=False)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='sales_created', verbose_name=_("تم الإنشاء بواسطة"))
    
    sale_customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='customer_sales', verbose_name=_("العميل"))
    
    sale_date = models.DateField(blank=True, null=True, verbose_name=_("تاريخ فاتورة البيع"))
    sale_customer_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("هاتف العميل"))
    sale_address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("عنوان العميل"))
    
    sale_invoice_number = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("رقم الفاتورة"))
    sale_payment_method = models.ForeignKey('Payment_method', on_delete=models.SET_NULL, null=True, blank=True, 
                                           verbose_name=_("طريقة الدفع"))
    sale_notes = models.TextField(max_length=200, blank=True, verbose_name=_("ملاحظات الفاتورة"))
    sale_currency = models.ForeignKey('Currency', on_delete=models.SET_NULL, null=True, blank=True, 
                                     verbose_name=_("العملة"))
    sale_status = models.ForeignKey('Status', on_delete=models.SET_NULL, null=True, blank=True, 
                                   verbose_name=_("حالة الفاتورة"))
    
    sale_shipping_company = models.ForeignKey('Shipping_com_m', on_delete=models.SET_NULL, null=True, blank=True, 
                                             verbose_name=_("شركة الشحن"))
    sale_shipping_num = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("رقم الشحنة"))
    
    sale_image = models.ImageField(upload_to='sale_invoice_images/%y/%m/%d/', blank=True, null=True, 
                                  verbose_name=_("صورة الفاتورة"))

    sale_tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), 
                                            verbose_name=_("نسبة الضريبة (%)"))
    sale_discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                       verbose_name=_("قيمة الخصم"))
    sale_addition = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                       verbose_name=_("قيمة الإضافة"))
    
    sale_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                         verbose_name=_("إجمالي البنود"))
    sale_tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                          verbose_name=_("قيمة الضريبة"))
    sale_final_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                           verbose_name=_("الإجمالي النهائي"))
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                     verbose_name=_("المبلغ المتبقي"))
    
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                     verbose_name=_("المبلغ المدفوع"))
    is_paid = models.BooleanField(default=False, verbose_name=_("تم الدفع بالكامل"))
    
    class Meta:
        verbose_name = _("فاتورة بيع")
        verbose_name_plural = _("فواتير البيع")
        ordering = ["-date_created"]
    
    def __str__(self):
        return f"فاتورة بيع {self.uniqueId}"
    
    def save(self, *args, **kwargs):
        if not self.sale_date:
            self.sale_date = timezone.now().date()
        
        if not self.uniqueId:
            last_invoice = Sale.objects.order_by('-_last_invoice_number').first()
            last_number = last_invoice._last_invoice_number if last_invoice else 0
            new_number = last_number + 1
            self._last_invoice_number = new_number
            self.uniqueId = f"S{new_number:04d}"
        
        if not self.slug:
            self.slug = slugify(f"sale-{self.uniqueId}")
        
        super().save(*args, **kwargs)

    def get_amount_parts(self):
        if not self.sale_final_total:
            return 0, 0
        
        amount = float(self.sale_final_total)
        currency_info = self.get_currency_info()
        decimals = currency_info.get('decimals', 2)
        
        integer_part = int(amount)
        fractional_part = int(round((amount - integer_part) * (10 ** decimals)))
        
        return integer_part, fractional_part
    
    @property
    def total_in_words(self):
        return self.get_total_in_words()
    
    def get_total_in_words(self):
        if not self.sale_final_total:
            return ""
        
        try:
            currency_info = self.get_currency_info()
            integer_part, fractional_part = self.get_amount_parts()
            
            integer_words = num2words(integer_part, lang='ar')
            
            def clean_arabic_words(words):
                words = re.sub(r'واحد ألف', 'ألف', words)
                words = re.sub(r'واحد مليون', 'مليون', words)
                words = re.sub(r'واحد مليار', 'مليار', words)
                words = re.sub(r'واحد ألف مليون', 'مليار', words)
                return words
            
            integer_words = clean_arabic_words(integer_words)
            
            if integer_part == 0:
                currency_word = currency_info['singular']
            elif integer_part == 1:
                currency_word = currency_info['singular']
            elif integer_part == 2:
                currency_word = currency_info['dual']
            elif integer_part <= 10:
                currency_word = currency_info['singular']
            else:
                currency_word = currency_info['plural']
            
            result = f"{integer_words} {currency_word}".strip()
            
            if fractional_part > 0:
                fraction_words = num2words(fractional_part, lang='ar')
                if fractional_part == 1:
                    fraction_currency = currency_info['fraction']
                elif fractional_part == 2:
                    fraction_currency = currency_info['fraction_dual']
                elif fractional_part <= 10:
                    fraction_currency = currency_info['fraction']
                else:
                    fraction_currency = currency_info['fraction_plural']
                
                if integer_part == 0:
                    result = f"{fraction_words} {fraction_currency}"
                else:
                    result += f" و{fraction_words} {fraction_currency}"
            
            result += " فقط لا غير"
            return result
            
        except Exception as e:
            logger.error(f"خطأ في تحويل المبلغ إلى كلمات: {e}", exc_info=True)
            currency_name = currency_info.get('singular', 'ليرة سورية') if 'currency_info' in locals() else 'ليرة سورية'
            return f"{self.sale_final_total} {currency_name} فقط لا غير"
    
    def get_currency_info(self):
        if not self.sale_currency:
            return {
                'name': 'ليرة سورية',
                'singular': 'ليرة سورية',
                'dual': 'ليرتان سوريتان',
                'plural': 'ليرات سورية',
                'fraction': 'قرش',
                'fraction_dual': 'قرشان',
                'fraction_plural': 'قروش',
                'decimals': 2
            }
        
        return {
            'name': self.sale_currency.name_ar,
            'singular': self.sale_currency.singular_ar,
            'dual': self.sale_currency.dual_ar,
            'plural': self.sale_currency.plural_ar,
            'fraction': self.sale_currency.fraction_name_ar,
            'fraction_dual': self.sale_currency.fraction_dual_ar,
            'fraction_plural': self.sale_currency.fraction_plural_ar,
            'decimals': self.sale_currency.decimals
        }
    
    def calculate_and_save_totals(self):
        try:
            self.sale_subtotal = self.saleitem_set.aggregate(total_sum=Sum('sale_total'))['total_sum'] or Decimal('0.00')
            self.sale_tax_amount = (self.sale_subtotal * (self.sale_tax_percentage / Decimal('100.00'))).quantize(Decimal('0.01'))
            self.sale_final_total = self.sale_subtotal + self.sale_tax_amount + self.sale_addition - self.sale_discount
            self.balance_due = max(self.sale_final_total - self.paid_amount, Decimal('0.00'))
            self.is_paid = self.paid_amount >= self.sale_final_total
            
            super().save(update_fields=[
                'sale_subtotal', 'sale_tax_amount', 'sale_final_total', 
                'balance_due', 'is_paid', 'sale_tax_percentage', 'sale_discount', 'sale_addition', 'paid_amount'
            ])
            
            logger.info(f"تم تحديث الإجماليات المالية لفاتورة البيع: الإجمالي {self.sale_final_total}")
            
        except Exception as e:
            logger.error(f"خطأ في حساب الإجماليات المالية لفاتورة البيع: {e}")
            raise
    
    def update_financial_fields(self, tax_percentage, discount, addition, paid_amount):
        try:
            self.sale_tax_percentage = Decimal(str(tax_percentage))
            self.sale_discount = Decimal(str(discount))
            self.sale_addition = Decimal(str(addition))
            self.paid_amount = Decimal(str(paid_amount))
            self.calculate_and_save_totals()
            
            logger.info(f"تم تحديث الحقول المالية لفاتورة البيع {self.uniqueId}")
            
        except Exception as e:
            logger.error(f"خطأ في تحديث الحقول المالية لفاتورة البيع: {e}")
            raise
    
    def create_cash_transaction(self):
        from .models import CashTransaction
        
        existing_transaction = CashTransaction.objects.filter(
            sale_invoice=self,
            transaction_type='sale_receipt'
        ).first()
        
        if not existing_transaction and self.paid_amount > 0:
            CashTransaction.objects.create(
                transaction_date=timezone.now(),
                amount_in=self.paid_amount,
                transaction_type='sale_receipt',
                payment_method=self.sale_payment_method,
                sale_invoice=self,
                notes=f"تحصيل مقابل فاتورة بيع {self.uniqueId}",
                created_by=self.created_by
            )
        elif existing_transaction and existing_transaction.amount_in != self.paid_amount:
            existing_transaction.amount_in = self.paid_amount
            existing_transaction.save()

    @property
    def total_items_count(self):
        if self.pk is None:
            return 0
        return self.saleitem_set.count()
    
    @property
    def total_quantity_sold(self):
        if self.pk is None:
            return Decimal('0.00')
        total_qty = self.saleitem_set.aggregate(total_qty=Sum('sold_quantity'))['total_qty']
        return total_qty or Decimal('0.00')

    @property
    def has_return(self):
        return self.sale_returns.exists()


class SaleItem(models.Model):
    """نموذج بنود فاتورة المبيعات - معكوس من PurchItem"""
    sale = models.ForeignKey('Sale', on_delete=models.CASCADE, verbose_name=_("فاتورة البيع"))
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='sale_items', verbose_name=_("المنتج المرتبط"))
    
    item_name = models.CharField(max_length=255, blank=True, verbose_name=_("اسم المادة"))
    sold_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'), 
                                           verbose_name=_("الكمية المباعة"))
    
    # === الحقول الجديدة للمعالجة المختلطة ===
    quantity_with_barcode = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_("الكمية المباعة بباركود")
    )
    
    quantity_without_barcode = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_("الكمية المباعة بدون باركود")
    )
    
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                   verbose_name=_("سعر الوحدة"))
    
    notes = models.CharField(max_length=255, blank=True, verbose_name=_("ملاحظات"))
    sale_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                    verbose_name=_("إجمالي البند"))
    
    sale_currency = models.ForeignKey("Currency", on_delete=models.PROTECT, 
                                     related_name='sale_items_by_currency', 
                                     verbose_name=_("عملة البيع لهذا البند"), null=True, blank=True)
    exchange_rate_at_sale = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('1.00'), 
                                                  verbose_name=_("سعر الصرف وقت البيع"))
    unit_price_base_currency = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                                 verbose_name=_("سعر الوحدة (بالعملة الأساسية)"))
    
    sale_item_image = models.ImageField(upload_to='sale_items_image/%y/%m/%d/', max_length=100, 
                                       blank=True, null=True, verbose_name=_("صورة المادة"))
    
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث"))

    class Meta:
        verbose_name = _("بند فاتورة البيع")
        verbose_name_plural = _("بنود فواتير البيع")
        ordering = ["id"]

    def __str__(self):
        if self.product:
            return f"{self.product.product_name} - {self.sold_quantity} × {self.unit_price} = {self.sale_total}"
        return f"{self.item_name} - {self.sold_quantity} × {self.unit_price} = {self.sale_total}"
    
    def save(self, *args, **kwargs):
        if not self.item_name and self.product:
            self.item_name = self.product.product_name
        elif not self.item_name:
            self.item_name = "مادة غير محددة"
        
        # التأكد من أن الكمية الإجمالية = كمية الباركود + كمية بدون باركود
        # فقط إذا لم تكن الكمية الإجمالية محددة يدوياً بشكل مختلف (للسلامة)
        total_q = self.quantity_with_barcode + self.quantity_without_barcode
        if total_q > 0:
            self.sold_quantity = total_q
        
        if self.sold_quantity and self.unit_price:
            subtotal = self.sold_quantity * self.unit_price
            self.sale_total = subtotal.quantize(Decimal('0.01'))
        
        try:
            self.unit_price_base_currency = self.unit_price
        except Exception:
            self.unit_price_base_currency = self.unit_price
        
        super().save(*args, **kwargs)

    def update_product_stock(self, old_quantity=None, old_product=None):
        try:
            if not self.product:
                logger.warning(f"⚠️ لا يوجد منتج مرتبط ببند البيع: {self.id}")
                return
            
            product = self.product
            
            print("="*50)
            print(f"🔍 تشخيص تحديث مخزون البيع للبند رقم: {self.id}")
            print(f"🔍 المنتج: {product.product_name}")
            product.refresh_from_db()
            print(f"📊 حالة المنتج قبل التحديث:")
            print(f"   - الكمية الحالية (current_stock_quantity): {product.current_stock_quantity}")
            print(f"📊 بيانات الفاتورة الجديدة:")
            print(f"   - الكمية المباعة (sold_quantity): {self.sold_quantity}")
            print(f"   - الكمية بباركود (quantity_with_barcode): {self.quantity_with_barcode}")
            print(f"   - الكمية بدون باركود (quantity_without_barcode): {self.quantity_without_barcode}")
            print("="*50)

            # منطق التعديل أو الإضافة الجديدة
            if old_quantity is not None and old_product is not None:
                logger.info(f"🔄 تعديل مخزون البيع: بند {self.id}, منتج {product.product_name}")
                
                if old_product and product.id == old_product.id:
                    # نفس المنتج - نطرح الفرق فقط
                    quantity_difference = self.sold_quantity - Decimal(str(old_quantity))
                    logger.info(f"📊 فرق الكمية لنفس المنتج: {quantity_difference}")
                    
                    product.current_stock_quantity -= quantity_difference
                    
                else:
                    # تغيير المنتج - إعادة كمية للقديم وخصم من الجديد
                    if old_product:
                        old_product.refresh_from_db()
                        old_product.current_stock_quantity += Decimal(str(old_quantity))
                        old_product.save()
                        logger.info(f"📈 إضافة كمية للمنتج القديم: {old_quantity}")
                    
                    product.current_stock_quantity -= self.sold_quantity
                    logger.info(f"📉 خصم كمية من المنتج الجديد: {self.sold_quantity}")
                        
            else:
                # عملية بيع جديدة - نطرح الكمية المباعة مباشرة
                logger.info(f"🆕 إنشاء بيع جديد: بند {self.id}, منتج {product.product_name}")
                product.current_stock_quantity -= self.sold_quantity
            
            # التحقق من السالبية
            if product.current_stock_quantity < Decimal('0.00'):
                logger.error(f"❌ خطأ: كمية المخزون سالبة للمنتج {product.product_name}!")

            product.last_operation_type = 'sale'
            product.save()
            
            print(f"✅ تم تحديث مخزون المنتج {product.product_name} إلى: {product.current_stock_quantity}")
            print("="*50)
            
            logger.info(f"✅ تم تحديث مخزون المنتج {product.product_name} إلى: {product.current_stock_quantity}")
                
        except Product.DoesNotExist:
            logger.error(f"❌ المنتج غير موجود: {self.product_id}")
        except Exception as e:
            print(f"❌❌❌ خطأ في تحديث مخزون البيع للبند {self.id}: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"❌ خطأ في تحديث مخزون البيع: {e}")
            logger.error(traceback.format_exc())

    def delete(self, *args, **kwargs):
        try:
            product = self.product
            sold_quantity = self.sold_quantity
            
            if product:
                product.current_stock_quantity += sold_quantity
                product.save()
                logger.info(f"↩️ تم إعادة كمية المنتج للمخزون بعد حذف بند البيع: {product.product_name}")
            
            super().delete(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"❌ خطأ في حذف بند البيع: {e}")
            raise


class SaleItemBarcode(models.Model):
    """نموذج لربط الباركودات ببنود فواتير البيع - نسخة معكوسة من PurchItemBarcode"""
    sale_item = models.ForeignKey('SaleItem', on_delete=models.CASCADE, 
                                 related_name='item_barcodes', verbose_name=_("بند البيع"))
    barcode = models.ForeignKey('Barcode', on_delete=models.CASCADE, 
                              related_name='sale_items', verbose_name=_("الباركود"))
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'),
                                      verbose_name=_("الكمية المرتبطة"))
    
    barcode_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'نشط'),
            ('returned', 'مرتجع'),
            ('damaged', 'تالف'),
        ],
        default='active',
        verbose_name=_("حالة الباركود في الفاتورة")
    )
    
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث"))

    class Meta:
        verbose_name = _("باركود بند البيع")
        verbose_name_plural = _("باركودات بنود البيع")
        unique_together = ('sale_item', 'barcode')
        ordering = ['-date_created']

    def __str__(self):
        return f"{self.sale_item.item_name} - {self.barcode.barcode_in}"

    def save(self, *args, **kwargs):
        if not self.barcode_status:
            self.barcode_status = 'active'
        
        if self.barcode_status == 'active':
            self.barcode.status = 'sold'
        elif self.barcode_status == 'returned':
            self.barcode.status = 'in_stock'
        elif self.barcode_status == 'damaged':
            self.barcode.status = 'damaged'
        
        self.barcode.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        barcode_to_check = self.barcode
        super().delete(*args, **kwargs)
        
        if not SaleItemBarcode.objects.filter(barcode=barcode_to_check).exists():
            if not hasattr(barcode_to_check, 'purch_items') or not barcode_to_check.purch_items.exists():
                if not hasattr(barcode_to_check, 'inventory_items') or not barcode_to_check.inventory_items.exists():
                    barcode_to_check.status = 'in_stock'
                    barcode_to_check.save()




class SaleReturn(models.Model):
    """نموذج مرتجع فاتورة المبيعات"""
    uniqueId = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="الرقم المسلسل")
    slug = models.SlugField(max_length=225, unique=True, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")
    _last_return_number = models.IntegerField(default=0, editable=False)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='sale_returns_created', verbose_name="تم الإنشاء بواسطة")
    
    original_sale = models.ForeignKey('Sale', on_delete=models.CASCADE, 
                                     related_name='sale_returns', verbose_name="الفاتورة الأصلية")
    
    return_date = models.DateField(blank=True, null=True, verbose_name="تاريخ المرتجع")
    return_reason = models.TextField(max_length=500, blank=True, verbose_name="سبب الإرجاع")
    
    return_invoice_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="رقم مرتجع البيع")
    return_payment_method = models.ForeignKey('Payment_method', on_delete=models.SET_NULL, null=True, blank=True, 
                                           verbose_name="طريقة الدفع للإرجاع")
    return_notes = models.TextField(max_length=200, blank=True, verbose_name="ملاحظات المرتجع")
    return_currency = models.ForeignKey('Currency', on_delete=models.SET_NULL, null=True, blank=True, 
                                     verbose_name="عملة المرتجع")
    return_status = models.ForeignKey('Status', on_delete=models.SET_NULL, null=True, blank=True, 
                                   verbose_name="حالة المرتجع")
    
    return_image = models.ImageField(upload_to='sale_return_images/%y/%m/%d/', blank=True, null=True, 
                                   verbose_name="صورة المرتجع")

    # الحقول المالية
    return_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                        verbose_name="إجمالي بنود المرتجع")
    return_tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                          verbose_name="قيمة الضريبة المستردة")
    return_final_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                           verbose_name="الإجمالي النهائي للمرتجع")
    
    # === [تعديل] تم تغيير الاسم من refund_amount إلى paid_amount ليكون أوضح ===
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                      verbose_name="المبلغ المصروف نقداً")
    
    is_refunded = models.BooleanField(default=False, verbose_name="تم الاسترداد بالكامل")

    class Meta:
        verbose_name = "مرتجع مبيعات"
        verbose_name_plural = "مرتجعات المبيعات"
        ordering = ["-date_created"]
    
    def __str__(self):
        return f"مرتجع بيع {self.uniqueId}"
    
    def save(self, *args, **kwargs):
        if not self.return_date:
            self.return_date = timezone.now().date()
        
        if not self.uniqueId:
            last_return = SaleReturn.objects.order_by('-_last_return_number').first()
            last_number = last_return._last_return_number if last_return else 0
            new_number = last_number + 1
            self._last_return_number = new_number
            self.uniqueId = f"SR{new_number:04d}"
        
        if not self.slug:
            self.slug = slugify(f"sale-return-{self.uniqueId}")
        
        super().save(*args, **kwargs)

    def calculate_and_save_totals(self):
        from django.db.models import Sum
        try:
            self.return_subtotal = self.salereturnitem_set.aggregate(total_sum=Sum('return_total'))['total_sum'] or Decimal('0.00')
            
            # التحقق من وجود نسبة ضريبة في الفاتورة الأصلية
            tax_percentage = getattr(self.original_sale, 'sale_tax_percentage', Decimal('0.00'))
            if tax_percentage:
                 self.return_tax_amount = (self.return_subtotal * (tax_percentage / Decimal('100.00'))).quantize(Decimal('0.01'))
            else:
                 self.return_tax_amount = Decimal('0.00')
            
            self.return_final_total = self.return_subtotal + self.return_tax_amount
            
            # تحديث حالة الاسترداد بناءً على المبلغ المصروف
            self.is_refunded = (self.paid_amount >= self.return_final_total)
            
            super().save(update_fields=[
                'return_subtotal', 'return_tax_amount', 'return_final_total', 
                'paid_amount', 'is_refunded'
            ])
            
            logger.info(f"تم تحديث إجماليات مرتجع البيع: الإجمالي {self.return_final_total}")
            
        except Exception as e:
            logger.error(f"خطأ في حساب إجماليات مرتجع البيع: {e}")
            raise
    
    @property
    def total_items_count(self):
        if self.pk is None:
            return 0
        return self.salereturnitem_set.count()
    
    @property
    def total_quantity_returned(self):
        from django.db.models import Sum
        if self.pk is None:
            return Decimal('0.00')
        total_qty = self.salereturnitem_set.aggregate(total_qty=Sum('returned_quantity'))['total_qty']
        return total_qty or Decimal('0.00')



class SaleReturnItem(models.Model):
    """نموذج بنود مرتجع فاتورة المبيعات"""
    sale_return = models.ForeignKey('SaleReturn', on_delete=models.CASCADE, verbose_name="مرتجع البيع")
    original_sale_item = models.ForeignKey('SaleItem', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='return_items', verbose_name="بند البيع الأصلي")
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='sale_return_items', verbose_name="المنتج المرتجع")
    
    item_name = models.CharField(max_length=255, blank=True, verbose_name="اسم المادة")
    returned_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'), 
                                          verbose_name="الكمية المرتجعة")
    
    # === الحقول للمعالجة المختلطة ===
    quantity_with_barcode = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        verbose_name="الكمية المرتجعة بباركود"
    )
    
    quantity_without_barcode = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        verbose_name="الكمية المرتجعة بدون باركود"
    )
    
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                   verbose_name="سعر الوحدة وقت البيع")
    
    notes = models.CharField(max_length=255, blank=True, verbose_name="ملاحظات")
    return_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                     verbose_name="إجمالي بند المرتجع")
    
    return_currency = models.ForeignKey("Currency", on_delete=models.PROTECT, 
                                      related_name='sale_return_items_by_currency', 
                                      verbose_name="عملة المرتجع", null=True, blank=True)
    exchange_rate_at_return = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('1.00'), 
                                                verbose_name="سعر الصرف وقت الإرجاع")
    unit_price_base_currency = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                                 verbose_name="سعر الوحدة (بالعملة الأساسية)")
    
    return_item_image = models.ImageField(upload_to='sale_return_items_image/%y/%m/%d/', max_length=100, 
                                        blank=True, null=True, verbose_name="صورة المادة المرتجعة")
    
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    class Meta:
        verbose_name = "بند مرتجع مبيعات"
        verbose_name_plural = "بنود مرتجعات المبيعات"
        ordering = ["id"]

    def __str__(self):
        if self.product:
            return f"{self.product.product_name} - {self.returned_quantity} × {self.unit_price} = {self.return_total}"
        return f"{self.item_name} - {self.returned_quantity} × {self.unit_price} = {self.return_total}"
    
    def save(self, *args, **kwargs):
        if not self.item_name and self.product:
            self.item_name = self.product.product_name
        elif not self.item_name:
            self.item_name = "مادة غير محددة"
        
        # حساب الإجمالي
        if self.returned_quantity and self.unit_price:
            total = self.returned_quantity * self.unit_price
            self.return_total = total.quantize(Decimal('0.01'))
        
        try:
            self.unit_price_base_currency = self.unit_price
        except Exception:
            self.unit_price_base_currency = self.unit_price
        
        super().save(*args, **kwargs)

    def get_available_image_url(self):
        if self.return_item_image and hasattr(self.return_item_image, 'url'):
            return self.return_item_image.url
        if self.product and self.product.product_image and hasattr(self.product.product_image, 'url'):
            return self.product.product_image.url
        return None

    def restore_product_stock(self):
        """إعادة الكمية المرتجعة إلى المخزون"""
        try:
            if not self.product:
                logger.warning(f"⚠️ لا يوجد منتج مرتبط ببند المرتجع: {self.id}")
                return
            
            product = self.product
            
            logger.info(f"🔄 إعادة مخزون للمنتج: {product.product_name}, الكمية: {self.returned_quantity}")
            
            product.current_stock_quantity += self.returned_quantity
            product.last_operation_type = 'sale_return'
            product.save()
            
            logger.info(f"✅ تم إعادة كمية {self.returned_quantity} إلى مخزون المنتج {product.product_name}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في إعادة المخزون: {e}")
            raise


class SaleReturnItemBarcode(models.Model):
    """نموذج لربط الباركودات ببنود مرتجع المبيعات"""
    sale_return_item = models.ForeignKey('SaleReturnItem', on_delete=models.CASCADE, 
                                       related_name='return_item_barcodes', verbose_name="بند المرتجع")
    barcode = models.ForeignKey('Barcode', on_delete=models.CASCADE, 
                              related_name='sale_return_items', verbose_name="الباركود")
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'),
                                      verbose_name="الكمية المرتجعة")
    
    barcode_status = models.CharField(
        max_length=20,
        choices=[
            ('returned', 'مرتجع'),
            ('damaged', 'تالف'),
        ],
        default='returned',
        verbose_name="حالة الباركود بعد الإرجاع"
    )
    
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    class Meta:
        verbose_name = "باركود مرتجع مبيعات"
        verbose_name_plural = "باركودات مرتجعات المبيعات"
        unique_together = ('sale_return_item', 'barcode')
        ordering = ['-date_created']

    def __str__(self):
        return f"{self.sale_return_item.item_name} - {self.barcode.barcode_in}"

    def save(self, *args, **kwargs):
        # عند إرجاع باركود، نعيد حالته إلى active
        if self.barcode_status == 'returned':
            self.barcode.status = 'active'  # <--- تم التعديل هنا
        elif self.barcode_status == 'damaged':
            self.barcode.status = 'damaged'
        
        self.barcode.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        barcode_to_check = self.barcode
        super().delete(*args, **kwargs)
        
        if not SaleReturnItemBarcode.objects.filter(barcode=barcode_to_check).exists():
            if not hasattr(barcode_to_check, 'sale_items') or not barcode_to_check.sale_items.exists():
                barcode_to_check.status = 'active'  # <--- تم التعديل هنا
                barcode_to_check.save()



#================================================
#       مرتجع المبيعات 
# ===============================================









#================================================
# اعدادات  من اجل البيانات المدخلة في قالاب التسعير 
# ===============================================



class PricingSetting(models.Model):
    """نموذج لحفظ إعدادات التسعير"""
    conversion_factor = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name=_("معامل التحويل"))
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name=_("نسبة الربح (%)"))
    offer_1_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name=_("نسبة العرض 1"))
    offer_2_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name=_("نسبة العرض 2"))
    offer_3_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name=_("نسبة العرض 3"))
    offer_4_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name=_("نسبة العرض 4"))
    offer_5_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name=_("نسبة العرض 5"))
    offer_6_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name=_("نسبة العرض 6"))
    
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث"))

    class Meta:
        verbose_name = _("إعدادات التسعير")
        verbose_name_plural = _("إعدادات التسعير")

    def save(self, *args, **kwargs):
        # ضمان وجود سجل واحد فقط
        if PricingSetting.objects.count() > 0 and not self.pk:
            existing = PricingSetting.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "إعدادات التسعير العامة"




#================================================
#  بداية المتجر 
# ===============================================



class ProductStoreSetting(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, primary_key=True, related_name='store_setting')
    
    #Choices for sections
    SECTION_CHOICES = [
        ('none', 'بدون قسم (لا يظهر تلقائياً)'),
        ('offers', 'أحدث العروض'),
        ('new', 'منتجات جديدة'),
        ('products', 'منتجاتنا'),
    ]

    badge_image = models.ImageField(
        upload_to='store_badges/', 
        blank=True, 
        null=True, 
        verbose_name="صورة الشعار"
    )
    
    is_visible = models.BooleanField(default=True, verbose_name="ظاهر في المتجر")
    
    store_section = models.CharField(
        max_length=20, 
        choices=SECTION_CHOICES, 
        default='products', 
        verbose_name="القسم في المتجر"
    )

    # === [الحقول الجديدة المضافة] ===
    show_old_price = models.BooleanField(
        default=True, 
        verbose_name="إظهار السعر القديم"
    )
    
    display_order = models.PositiveIntegerField(
        default=0, 
        verbose_name="ترتيب الظهور"
    )

    def __str__(self):
        return f"إعدادات: {self.product.product_name}"




class Cart(models.Model):
    """
    نموذج سلة التسوق:
    تستخدم لتخزين المنتجات المؤقتة قبل تحويلها لطلب فعلي.
    تدعم الزوار (عبر session_key) والمستخدمين المسجلين.
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, 
        null=True, blank=True, 
        verbose_name=_("المستخدم")
    )
    session_key = models.CharField(
        max_length=40, blank=True, null=True, 
        verbose_name=_("مفتاح الجلسة (للزوار)")
    )
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    
    class Meta:
        verbose_name = _("سلة تسوق")
        verbose_name_plural = _("سلات التسوق")
    
    def __str__(self):
        return f"سلة {self.user if self.user else 'زائر'} - {self.id}"

    @property
    def total_price(self):
        """حساب إجمالي السلة"""
        # نستخدم الدالة المساعدة التي فهمتها من كودك لجلب سعر العرض
        # ملاحظة: سأفترض وجود دالة get_price_for_user داخل Product لاحقاً
        return sum(item.total_item_price for item in self.items.all())


class CartItem(models.Model):
    """
    عناصر سلة التسوق
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name=_("السلة"))
    product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name=_("المنتج"))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("الكمية"))
    
    class Meta:
        verbose_name = _("عنصر سلة")
        verbose_name_plural = _("عناصر السلة")
        unique_together = ('cart', 'product') # منع تكرار نفس المنتج في السلة

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name}"

    @property
    def total_item_price(self):
        # هنا سنستخدم سعر العرض إذا كان موجوداً
        price = self.product.offer_1_price if self.product.offer_1_price > 0 else self.product.wholesale_price
        return price * self.quantity


class WebsiteOrder(models.Model):
    """
    نموذج طلب المتجر الإلكتروني:
    يمثل الطلب الذي يضعه الزبون. يتميز عن فاتورة البيع (Sale) بأنه يحتوي على
    حالات متابعة (جديد، قيد التجهيز) ويرتبط بفاتورة المحاسبة لاحقاً.
    """
    STATUS_CHOICES = (
        ('new', _('طلب جديد')),
        ('processing', _('قيد التجهيز')),
        ('shipped', _('تم الشحن')),
        ('delivered', _('تم التسليم')),
        ('cancelled', _('ملغي')),
    )
    
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='website_orders', 
        verbose_name=_("العميل")
    )
    
    # بيانات التواصل (نأخذها هنا حتى لو لم يكن مسجل دخول)
    full_name = models.CharField(max_length=100, verbose_name=_("الاسم الكامل"))
    phone = models.CharField(max_length=20, verbose_name=_("رقم الهاتف"))
    address = models.TextField(verbose_name=_("عنوان الشحن"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("ملاحظات العميل"))
    
    # معلومات الطلب
    order_date = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الطلب"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name=_("حالة الطلب"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name=_("الإجمالي"))
    
    # === الربط مع نظام المحاسبة (نقطة التكامل) ===
    related_sale = models.OneToOneField(
        Sale, on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='web_order',
        verbose_name=_("فاتورة البيع المرتبطة")
    )
    
    class Meta:
        verbose_name = _("طلب متجر")
        verbose_name_plural = _("طلبات المتجر")
        ordering = ['-order_date']

    def __str__(self):
        return f"طلب #{self.id} - {self.full_name}"


class WebsiteOrderItem(models.Model):
    """
    تفاصيل المنتجات داخل الطلب
    """
    order = models.ForeignKey(WebsiteOrder, on_delete=models.CASCADE, related_name='items', verbose_name=_("الطلب"))
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, verbose_name=_("المنتج"))
    product_name = models.CharField(max_length=255, verbose_name=_("اسم المنتج (وقت الطلب)")) # لحفظ الاسم حتى لو تغير لاحقاً
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("سعر الوحدة"))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("الكمية"))
    
    class Meta:
        verbose_name = _("بند طلب")
        verbose_name_plural = _("بنود الطلب")

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"





class StoreBanner(models.Model):
    """
    نموذج مستقل لإدارة بنرات المتجر (العلوي والجانبي)
    لا يؤثر على جدول المنتجات الأساسي.
    """
    POSITION_CHOICES = [
        ('top', 'بنر علوي (عرض كامل)'),
        ('side', 'بنر جانبي'),
    ]

    title = models.CharField(max_length=100, verbose_name="العنوان الترويجي", help_text="مثال: خصم 50%")
    image = models.ImageField(upload_to='store_banners/', verbose_name="صورة البنر")
    link_url = models.URLField(blank=True, null=True, verbose_name="رابط عند الضغط")
    position = models.CharField(max_length=10, choices=POSITION_CHOICES, default='top', verbose_name="موضع العرض")
    
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب", help_text="الأقل يظهر أولاً")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "بنر إعلاني"
        verbose_name_plural = "البنرات الإعلانية"
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_position_display()})"


#========التحديثات الجديدة




class StoreSection(models.Model):
    """
    يمثل قسماً في واجهة المتجر (مثل: الأكثر مبيعاً، إكسسوارات، عروض اليوم)
    يمكن إنشاء عدد غير محدود من هذه الأقسام من لوحة التحكم.
    """
    SECTION_STYLE_CHOICES = [
        ('grid', 'بطاقات شبكية (Grid)'),
        ('list', 'قائمة أفقية (List)'),
        ('offers', 'أسلوب العروض (Offers)'),
    ]

    name = models.CharField(max_length=100, verbose_name="اسم القسم", help_text="مثال: الأكثر مبيعاً")
    slug = models.SlugField(max_length=100, unique=True, blank=True, verbose_name="الرابط النصي")
    style_type = models.CharField(
        max_length=20, 
        choices=SECTION_STYLE_CHOICES, 
        default='grid', 
        verbose_name="شكل العرض"
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال (يظهر في المتجر)")
    display_order = models.PositiveIntegerField(default=0, verbose_name="ترتيب القسم", help_text="القسم ذو الرقم الأقل يظهر أولاً")
    
    class Meta:
        verbose_name = "قسم متجر"
        verbose_name_plural = "أقسام المتجر"
        ordering = ['display_order']


    def save(self, *args, **kwargs):
        if not self.slug:
            # معالجة الأسماء العربية (تُرجع فارغاً) بإضافة نص عشوائي
            base_slug = slugify(self.name)
            if not base_slug:
                self.slug = f"section-{uuid.uuid4().hex[:8]}"
            else:
                # التأكد من عدم تكرار الـ slug
                unique_slug = base_slug
                counter = 1
                while StoreSection.objects.filter(slug=unique_slug).exists():
                    unique_slug = f"{base_slug}-{counter}"
                    counter += 1
                self.slug = unique_slug
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name



class ProductSectionItem(models.Model):
    """
    الجدول الوسيط: يربط المنتج بالقسم.
    الميزة الأساسية: نفس المنتج يمكن إضافته لعدة أقسام بترتيب وشكل مختلف.
    """
    section = models.ForeignKey(StoreSection, on_delete=models.CASCADE, related_name='items', verbose_name="القسم")
    product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name="المنتج")
    
    # إعدادات خاصة بهذا المنتج داخل هذا القسم فقط
    display_order = models.PositiveIntegerField(default=0, verbose_name="ترتيب المنتج داخل القسم")
    show_old_price = models.BooleanField(default=False, verbose_name="إظهار السعر القديم كعرض")
    custom_badge = models.ImageField(
        upload_to='store_section_badges/', 
        blank=True, null=True, 
        verbose_name="شعار خاص (اختياري)", help_text="يظهر فوق صورة المنتج في هذا القسم فقط"
    )
    
    class Meta:
        verbose_name = "منتج داخل القسم"
        verbose_name_plural = "منتجات الأقسام"
        ordering = ['display_order']
        # منع تكرار نفس المنتج في نفس القسم مرتين
        unique_together = ('section', 'product')

    def __str__(self):
        return f"{self.product.product_name} في ({self.section.name})"






# ===============================================
#  نظام التسعير الديناميكي (الجديد)
# ===============================================

class PricingTier(models.Model):
    """
    يمثل مستوى تسعير أو خصم (مثل: أحدث العروض، منتجات جديدة، سعر الكرتون).
    المستخدم يمكنه إنشاء عدد غير محدود منها.
    """
    name = models.CharField(max_length=100, verbose_name="اسم المستوى (مثال: أحدث العروض)")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name="نسبة الخصم (%)")
    display_order = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "مستوى تسعير"
        verbose_name_plural = "مستويات التسعير"
        ordering = ['display_order']

    def __str__(self):
        return f"{self.name} ({self.discount_percent}%)"


class ProductPriceTier(models.Model):
    """
    الجدول الوسيط: يحفظ السعر النهائي لمنتج معين داخل مستوى تسعير معين.
    (هذا البديل الحديث لحقول offer_1_price, offer_2_price ...)
    """
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='tier_prices', verbose_name="المنتج")
    tier = models.ForeignKey(PricingTier, on_delete=models.CASCADE, related_name='product_prices', verbose_name="مستوى التسعير")
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="السعر المحسوب")

    class Meta:
        verbose_name = "سعر المنتج في مستوى"
        verbose_name_plural = "أسعار المستويات"
        unique_together = ('product', 'tier') # منع تكرار المستوى لنفس المنتج

    def __str__(self):
        return f"{self.product.product_name} - {self.tier.name}: {self.price}"


class Category(models.Model):
    """
    تصنيفات المنتجات (مثل: ألبسة، إلكترونيات، أدوات مطبخ)
    مرتبطة ديناميكياً بمستويات التسعير.
    """
    name = models.CharField(max_length=100, verbose_name="اسم التصنيف")
    slug = models.SlugField(max_length=100, unique=True, blank=True, verbose_name="الرابط النصي")
    
    # الربط المباشر مع مستوى التسعير الذي أنشأناه في الخطوة السابقة
    pricing_tier = models.ForeignKey(
        PricingTier, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="مستوى التسعير الافتراضي",
        help_text="إذا تم اختياره، سيتم استخدام سعر هذا المستوى للمنتجات التابعة لهذا التصنيف في المتجر"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="ظاهر في المتجر")
    display_order = models.PositiveIntegerField(default=0, verbose_name="ترتيب الظهور")
    
    # اختياري: صورة أيقونة للتصنيف
    icon = models.ImageField(
        upload_to='categories_icons/', 
        blank=True, null=True, 
        verbose_name="أيقونة التصنيف"
    )

    class Meta:
        verbose_name = "تصنيف"
        verbose_name_plural = "تصنيفات المتجر"
        ordering = ['display_order']

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.template.defaultfilters import slugify
            import uuid
            base_slug = slugify(self.name)
            self.slug = base_slug if base_slug else f"cat-{uuid.uuid4().hex[:8]}"
            
            # التأكد من عدم تكرار الـ slug
            unique_slug = self.slug
            counter = 1
            from .models import Category
            while Category.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{self.slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



# ===============================================
#  نظام تنبيهات توفر المواد
# ===============================================

from django.db import models
from .models import Product  # تأكد من استيراد المنتج


class StockNotification(models.Model):
    """
    يحفظ طلبات الزبائن لإعلامهم عند توفر منتج نفد من المخزون
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="المنتج")
    email = models.EmailField(verbose_name="البريد الإلكتروني")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")
    is_sent = models.BooleanField(default=False, verbose_name="تم الإرسال")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الإرسال")

    class Meta:
        verbose_name = "تنبيه مخزون"
        verbose_name_plural = "تنبيهات المخزون"
        # لمنع تكرار نفس الشخص لنفس المنتج (اختياري، لكنه يحافظ على النظافة)
        unique_together = ('product', 'email') 

    def __str__(self):
        return f"{self.email} ينتظر {self.product.product_name}"





# ═══════════════════════════════════════════════════════════
#  عرض الفلاش (Flash Deal)
# ═══════════════════════════════════════════════════════════

from django.utils import timezone

# ═══════════════════════════════════════════════════════════
#  عرض الفلاش (Flash Deal) - النسخة المُصححة
# ═══════════════════════════════════════════════════════════

from django.utils import timezone


class FlashDeal(models.Model):
    """
    عرض فلاش: منتج بسعر خاص وكمية محدودة ووقت انتهاء.
    يمكن تفعيل عدة عروض في نفس الوقت لعرضها مقسمة في الواجهة.
    """
    product = models.ForeignKey(
        'Product', 
        on_delete=models.CASCADE, 
        verbose_name="المنتج"
    )
    deal_price = models.DecimalField(
        max_digits=12, decimal_places=2, 
        verbose_name="سعر العرض"
    )
    max_quantity = models.PositiveIntegerField(
        default=1, 
        verbose_name="الكمية المخصصة للعرض",
        help_text="عدد الوحدات المتاحة بهذا السعر. عندما تنتهي يختفي العرض."
    )
    ends_at = models.DateTimeField(
        verbose_name="ينتهي في",
        help_text="الوقت الذي يختفي فيه العرض تلقائياً"
    )
    is_active = models.BooleanField(
        default=False, 
        verbose_name="فعال",
        help_text="يعرض العرض في الصفحة الرئيسية فقط إذا كان مفعّلاً ولم ينتهِ وقته"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "عرض فلاش"
        verbose_name_plural = "عروض الفلاش"
        ordering = ['-created_at']

    def __str__(self):
        return f"فلاش: {self.product.product_name} — {self.deal_price}"

    def is_currently_active(self):
        """هل العرض نشط الآن؟ (مفعّل + لم ينتهِ وقته)"""
        if not self.is_active:
            return False
        if self.ends_at and timezone.now() > self.ends_at:
            return False
        return True

    def remaining_quantity(self):
        """الكمية المتبقية من العرض"""
        try:
            sold = WebsiteOrderItem.objects.filter(
                product=self.product,
                order__order_date__gte=self.created_at,
                order__status__in=['new', 'processing', 'shipped', 'delivered']
            ).aggregate(total=models.Sum('quantity'))['total'] or 0
            return max(0, self.max_quantity - int(sold))
        except:
            return self.max_quantity

    def remaining_percentage(self):
        """نسبة المتبقي"""
        if self.max_quantity <= 0:
            return 0
        return int((self.remaining_quantity() / self.max_quantity) * 100)

    # =============================================
    # تم حذف دالة save() بالكامل
    # كانت تمنع تفعيل أكثر من عرض واحد
    # =============================================



# ===============================================
#  نماذج إعدادات الواجهة (للسماح بالتعديل من لوحة التحكم)
# ===============================================

class StoreAnnouncement(models.Model):
    """لإدارة نصوص الشريط العلوي المتحرك"""
    text = models.CharField(max_length=200, verbose_name="نص الإعلان")
    icon_class = models.CharField(max_length=50, default="fa-bullhorn", verbose_name="رمز الأيقونة (FontAwesome)")
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "إعلان شريط علوي"
        verbose_name_plural = "إعلانات الشريط العلوي"
        ordering = ['order']

    def __str__(self):
        return self.text


class StoreFeatureIcon(models.Model):
    """لإدارة الأيقونات المميزة أسفل الشريط"""
    title = models.CharField(max_length=100, verbose_name="العنوان")
    icon_class = models.CharField(max_length=50, verbose_name="رمز الأيقونة")
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "أيقونة مميزة"
        verbose_name_plural = "الأيقونات المميزة"
        ordering = ['order']

    def __str__(self):
        return self.title

#================================================
#  نهاية المتجر 
# ===============================================


