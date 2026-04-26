# ==================== مكتبات بايثون القياسية ====================
import csv
import json
import logging
import os
from decimal import Decimal
from types import SimpleNamespace
from tempfile import NamedTemporaryFile
from datetime import timedelta

# ==================== مكتبات خارجية ====================
import requests

# ==================== إطار عمل Django الأساسي ====================
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.temp import NamedTemporaryFile
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Q, Sum, Count, Func, Value, CharField, DecimalField, F, ExpressionWrapper
from django.db.models.functions import Concat, Now, Coalesce
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.forms import inlineformset_factory

# ==================== النماذج المحلية (Models) ====================
from .models import (
    Barcode,
    CashTransaction,
    Cart,
    CartItem,
    Currency,
    EmailSetting,
    Payment_method,
    PricingSetting,
    Product,
    ProductStoreSetting,
    Purch,
    PurchItem,
    PurchItemBarcode,
    PurchaseReturn,
    PurchaseReturnItem,
    PurchaseReturnItemBarcode,
    Sale,
    SaleItem,
    SaleItemBarcode,
    SaleReturn,
    SaleReturnItem,
    SaleReturnItemBarcode,
    Shipping_com_m,
    Status,
    PriceType,
    StoreBanner,
    User,
    WebsiteOrder,
    WebsiteOrderItem,
    Category,
    StoreAnnouncement, 
    StoreFeatureIcon
)

# ==================== النماذج المحلية (Forms) ====================
from .forms import (
    BarcodeForm,
    CashTransactionForm,
    CurrencyForm,
    EmailSettingForm,
    PaymentMethodForm,
    PriceTypeForm,
    PurchEditForm,
    PurchForm,
    PurchaseReturnForm,
    PurchaseReturnItemForm,
    PurchaseReturnItemFormSet,
    PurchItemEditFormSet,
    PurchItemFormSet,
    SaleForm,
    SaleItemForm,
    SaleItemBarcodeForm,
    SaleItemFormSet,
    SaleItemBarcodeFormSet,
    SaleReturnForm,
    SaleReturnItemForm,
    SaleReturnItemBarcodeForm,
    SaleReturnItemFormSet,
    SaleReturnItemBarcodeFormSet,
    ShippingCompanyForm,
    StatusForm,
)

# ==================== التطبيقات الأخرى ====================
from accounts.models import Profile

# ==================== الأدوات المساعدة المحلية ====================
from .utils import send_custom_email



from django.core.mail import EmailMessage
# ... باقي الاستيرادات

from invoice.utils import get_active_email_connection


from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count
from django.template.loader import render_to_string
from .models import StockNotification


from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
import json

from .models import (
    Product, PricingSetting, 
    PricingTier, ProductPriceTier
)




from django.core import serializers
# ... استيرادات أخرى ...
from django.core import serializers
# ...

from django.views.decorators.http import require_POST
import json  # تأكد من وجود هذا الاستيراد




from django.views.decorators.http import require_POST
import json  # تأكد من وجود هذا السطر
from django.http import Http404 # جيد للتعامل مع حالات عدم العثور

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone
import json
from decimal import Decimal
# ... بقية الاستيرادات الخاصة بك ...

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Q
from decimal import Decimal
import json

from .models import (
    Product, Sale, SaleItem, CashTransaction,
    ProductStoreSetting, Cart, CartItem,
    WebsiteOrder, WebsiteOrderItem,
    StoreBanner, StoreSection, ProductSectionItem
)










# ===============================================
#  المتجر الإلكتروني - Views (النسخة النهائية والمعتمدة)
# ===============================================

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal
import json

from .models import (
    Product, Sale, SaleItem, CashTransaction,
    ProductStoreSetting, StoreBanner,
    StoreSection, ProductSectionItem,
    Cart, CartItem, WebsiteOrder, WebsiteOrderItem
)

import json



from django.utils import timezone
from .models import FlashDeal





# ==================== إعدادات التسجيل ====================
logger = logging.getLogger(__name__)



#================================================
#               فواتير الشراء                  #
# ===============================================

@login_required
def purch_list(request):
    """عرض قائمة فواتير الشراء"""
    purchases = Purch.objects.all().order_by('-purch_date')
    return render(request, 'invoice/purchase/purch_list.html', {
        'purchases': purchases,
        'title': _('فواتير الشراء')
    })



@login_required
def purch_create(request):
    """
    إنشاء فاتورة شراء جديدة.
    تم تعديل الدالة لدعم:
    1. التحقق من تكرار الباركودات (داخل الفاتورة وفي قاعدة البيانات) قبل الحفظ.
    2. الحفاظ على البيانات المدخلة في حالة حدوث خطأ (عدم مسح الفورم).
    3. التعامل مع رفع الصور والربط التلقائي للمنتجات.
    """
    
    if request.method == 'POST':
        form = PurchForm(request.POST, request.FILES)
        formset = PurchItemFormSet(request.POST, request.FILES, prefix='items')
        
        # ============================================================
        # [1] التحقق من الباركودات قبل أي عملية حفظ
        # ============================================================
        barcode_errors = []
        invoice_barcodes_set = set() # لتخزين الباركودات للتأكد من عدم تكرارها داخل الفاتورة
        
        # نجمع البيانات المرسلة عبر POST والتي تبدأ بـ item_ وتنتهي بـ _barcodes
        # هذه البيانات يتم إرسالها بواسطة الـ JavaScript في القالب
        submitted_barcodes_data = {}
        for key, values in request.POST.lists():
            if key.startswith('item_') and key.endswith('_barcodes'):
                try:
                    # استخراج رقم البند (index) من اسم الحقل
                    # مثال: item_0_barcodes -> 0
                    parts = key.split('_')
                    idx = int(parts[1])
                    submitted_barcodes_data[idx] = values
                except (ValueError, IndexError):
                    continue
        
        # التحقق من كل باركود تم إرساله
        for idx, barcodes in submitted_barcodes_data.items():
            for bc in barcodes:
                bc = bc.strip()
                if not bc: continue # تجاهل الحقول الفارغة
                
                # أ. التحقق من التكرار داخل الفاتورة نفسها
                if bc in invoice_barcodes_set:
                    barcode_errors.append(f"الباركود '{bc}' مكرر أكثر من مرة في نفس الفاتورة.")
                else:
                    invoice_barcodes_set.add(bc)
                
                # ب. التحقق من وجود الباركود مسبقاً في قاعدة البيانات (في فواتير شراء سابقة)
                # نتحقق فقط إذا لم يكن مكرراً داخل الفاتورة لتجنب تكرار الرسائل
                if PurchItemBarcode.objects.filter(barcode__barcode_in=bc).exists():
                    barcode_errors.append(f"الباركود '{bc}' مستخدم سابقاً في فاتورة شراء أخرى ولا يمكن تكراره.")

        # ============================================================
        # [2] التحقق من صحة النموذج والبدء بالحفظ
        # ============================================================
        
        # نتحقق من صحة الفورم والفورمست وعدم وجود أخطاء باركود
        if form.is_valid() and formset.is_valid() and not barcode_errors:
            try:
                with transaction.atomic():
                    # --- حفظ الفاتورة الرئيسية ---
                    purchase = form.save(commit=False)
                    purchase.created_by = request.user
                    
                    # إنشاء رقم مسلسل للفاتورة إذا لم يكن موجوداً
                    if not purchase.uniqueId:
                        last_invoice = Purch.objects.order_by('-_last_invoice_number').first()
                        last_number = last_invoice._last_invoice_number if last_invoice else 0
                        new_number = last_number + 1
                        purchase._last_invoice_number = new_number
                        purchase.uniqueId = f"P{new_number:04d}"
                        
                    # إنشاء slug
                    if not purchase.slug:
                        purchase.slug = slugify(f"purch-{purchase.uniqueId}")
                    
                    purchase.save()

                    # --- حفظ بنود الفاتورة ---
                    instances = formset.save(commit=False)
                    
                    for i, instance in enumerate(instances):
                        instance.purch = purchase
                        
                        # التأكد من ربط المنتج من الحقول المخفية
                        product_id_from_form = request.POST.get(f'items-{i}-product')
                        product_search_value = request.POST.get(f'items-{i}-product_search', '')
                        
                        if not instance.product and product_id_from_form and product_id_from_form != '':
                            try:
                                product = Product.objects.get(id=product_id_from_form)
                                instance.product = product
                            except Product.DoesNotExist:
                                pass
                        
                        # إذا لم يتم الربط بعد، حاول البحث بالاسم
                        if not instance.product and product_search_value and product_search_value != "مادة غير محددة":
                            try:
                                product = Product.objects.get(product_name=product_search_value)
                                instance.product = product
                            except (Product.DoesNotExist, Product.MultipleObjectsReturned):
                                product = Product.objects.filter(product_name=product_search_value).first()
                                instance.product = product
                        
                        # التأكد من تعبئة اسم المادة
                        if not instance.item_name and instance.product:
                            instance.item_name = instance.product.product_name
                        elif not instance.item_name:
                            instance.item_name = product_search_value if product_search_value else "مادة غير محددة"
                        
                        # --- منطق حفظ الصور (تلقائي/يدوي) ---
                        image_field_name = f'items-{i}-purch_item_image'
                        image_url = request.POST.get(f'items-{i}-product_image_url', '')
                        is_auto_image = request.POST.get(f'items-{i}-is_auto_image') == 'true'
                        is_manual_upload = request.POST.get(f'items-{i}-manual_image_upload') == 'true'
                        
                        # الحالة 1: تم رفع صورة يدوياً (الملف موجود في request.FILES)
                        if image_field_name in request.FILES:
                            pass # سيتم حفظها تلقائياً بواسطة instance.save()
                            
                        # الحالة 2: صورة تلقائية من رابط URL
                        elif image_url and is_auto_image and not is_manual_upload:
                            try:
                                response = requests.get(image_url, timeout=10)
                                if response.status_code == 200:
                                    img_temp = NamedTemporaryFile(delete=True)
                                    img_temp.write(response.content)
                                    img_temp.flush()
                                    
                                    filename = os.path.basename(image_url)
                                    if not filename or '.' not in filename:
                                        filename = f"product_{instance.product_id if instance.product else 'auto'}.jpg"
                                    
                                    instance.purch_item_image.save(filename, File(img_temp), save=False)
                            except Exception as e:
                                logger.error(f"خطأ في تحميل الصورة التلقائية: {e}")
                        
                        # حفظ البند في قاعدة البيانات
                        instance.save()
                        
                        # تحديث المخزون
                        if instance.product:
                            instance.update_product_stock()
                        
                        # --- معالجة الباركودات ---
                        barcodes_key = f'item_{i}_barcodes'
                        barcodes = request.POST.getlist(barcodes_key)
                        
                        for barcode_value in barcodes:
                            barcode_value = barcode_value.strip()
                            if barcode_value:
                                try:
                                    # البحث عن الباركود أو إنشاؤه
                                    barcode_obj = None
                                    try:
                                        barcode_obj = Barcode.objects.get(barcode_in=barcode_value)
                                        # إذا كان الباركود موجوداً لمنتج مختلف، نتخطاه (أو نرفضه حسب السياسة)
                                        if instance.product and barcode_obj.product != instance.product:
                                            # هنا يمكنك إضافة منطق لتحديث المنتج المرتبط إذا أردت
                                            continue
                                    except Barcode.DoesNotExist:
                                        # إنشاء باركود جديد وربطه بالمنتج الحالي
                                        if instance.product:
                                            barcode_obj = Barcode.objects.create(
                                                barcode_in=barcode_value,
                                                product=instance.product,
                                                is_primary=False,
                                                status='active'
                                            )
                                        else:
                                            # إذا لم يكن هناك منتج، نحاول ربطه بالاسم
                                            item_name = instance.item_name
                                            if item_name and item_name != "مادة غير محددة":
                                                try:
                                                    product = Product.objects.get(product_name=item_name)
                                                    barcode_obj = Barcode.objects.create(
                                                        barcode_in=barcode_value,
                                                        product=product,
                                                        is_primary=False,
                                                        status='active'
                                                    )
                                                except Product.DoesNotExist:
                                                    continue
                                    
                                    # ربط الباركود ببند الفاتورة
                                    if barcode_obj:
                                        PurchItemBarcode.objects.get_or_create(
                                            purch_item=instance,
                                            barcode=barcode_obj,
                                            defaults={
                                                'quantity_used': Decimal('1.00'),
                                                'barcode_status': 'active'
                                            }
                                        )
                                    
                                except IntegrityError:
                                    continue
                                except Exception as e:
                                    logger.error(f"خطأ في ربط الباركود: {e}")
                    
                    # حذف البنود المحذوفة (التي اختار المستخدم حذفها في الواجهة)
                    for instance in formset.deleted_objects:
                        # حذف الباركودات المرتبطة بالبند أولاً
                        instance.item_barcodes.all().delete()
                        instance.delete()
                    
                    # حساب الإجماليات النهائية
                    purchase.calculate_and_save_totals()

                    # التحقق من المبلغ المدفوع
                    if purchase.paid_amount > purchase.purch_final_total:
                        raise ValidationError(_("المبلغ المدفوع لا يمكن أن يتجاوز الإجمالي النهائي للفاتورة"))

                    # إنشاء حركة الصندوق إذا كان الدفع نقدياً
                    if purchase.paid_amount > 0 and purchase.purch_payment_method and purchase.purch_payment_method.is_cash:
                        purchase.create_cash_transaction()
                    
                    messages.success(request, 'تم إنشاء فاتورة الشراء بنجاح وتحديث المخزون')
                    return redirect('invoice:purch_detail', slug=purchase.slug)
                    
            except ValidationError as e:
                messages.error(request, e.messages[0] if e.messages else str(e))
            except Exception as e:
                logger.error(f"خطأ في إنشاء فاتورة الشراء: {e}")
                messages.error(request, f'حدث خطأ غير متوقع: {str(e)}')
        
        # ============================================================
        # [3] التعامل مع حالات الخطأ (إعادة عرض الصفحة بالبيانات)
        # ============================================================
        
        # إذا وصلنا到这里، فهناك خطأ ما (فورم غير صالح أو أخطاء باركود)
        if not form.is_valid() or not formset.is_valid() or barcode_errors:
            # إضافة أخطاء الباركود إلى رسائل النظام
            for error in barcode_errors:
                messages.error(request, error)
            
            if not barcode_errors:
                messages.error(request, 'يرجى تصحيح الأخطاء في النموذج.')
            else:
                messages.error(request, 'لم يتم حفظ الفاتورة بسبب أخطاء في الباركودات أو البيانات.')
            
            # نقوم بتحضير السياق وإعادة عرض نفس الصفحة (render)
            # هذا هو التعديل الجوهري الذي يمنع فقدان البيانات
            products = Product.objects.all()
            return render(request, 'invoice/purchase/purch_form.html', {
                'form': form,         # الفورم يحتوي على البيانات المدخلة والأخطاء
                'formset': formset,   # الفورمست يحتوي على البنود المدخلة
                'products': products,
                'title': 'إنشاء فاتورة شراء جديدة'
            })

    # ============================================================
    # [4] طلب GET (إنشاء فاتورة جديدة فارغة)
    # ============================================================
    else:
        form = PurchForm(initial={
            'purch_date': timezone.now().date(),
            'paid_amount': 0,
            'purch_tax_percentage': 0,
            'purch_discount': 0,
            'purch_addition': 0
        })
        formset = PurchItemFormSet(prefix='items', queryset=PurchItem.objects.none())
    
    products = Product.objects.all()
    
    # ملاحظة: تم تعطيل عرض رصيد الصندوق هنا، وهو يعتمد أيضاً على عدم استدعاء fetchCashBalance في JS
    
    return render(request, 'invoice/purchase/purch_form.html', {
        'form': form,
        'formset': formset,
        'products': products,
        'title': 'إنشاء فاتورة شراء جديدة'
    })


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from types import SimpleNamespace
from decimal import Decimal
from .models import Purch

@login_required
def purch_detail(request, slug):
    """
    عرض تفاصيل فاتورة المشتريات
    مع تمييز الباركودات المرتجعة بلون خاص
    """
    purchase = get_object_or_404(Purch, slug=slug)
    
    reset_date = purchase.last_updated
    items_for_template = []
    
    purchase_items = purchase.purchitem_set.all().select_related('product')

    for item in purchase_items:
        # 1. حساب الكميات
        total_returned_after_edit = item.returned_items.filter(
            purchase_return__date_created__gte=reset_date
        ).aggregate(total=Sum('returned_quantity'))['total'] or Decimal('0.00')

        available_quantity = item.purchased_quantity - total_returned_after_edit

        # 2. تجميع الباركودات مع التمييز
        barcodes_list = []

        # أ. باركودات أصلية (Active)
        if hasattr(item, 'item_barcodes'):
            for b in item.item_barcodes.all():
                if b.barcode:
                    # نضيفه كما هو
                    barcodes_list.append(b.barcode)

        # ب. باركودات مرتجعة (Returned)
        for ret_item in item.returned_items.all():
            if ret_item.purchase_return.date_created >= reset_date:
                # نجلب الباركودات المرتجعة
                ret_barcodes = []
                
                if hasattr(ret_item, 'barcode') and ret_item.barcode:
                    ret_barcodes.append(ret_item.barcode)
                elif hasattr(ret_item, 'barcodes'):
                    try:
                        ret_barcodes.extend([b.barcode for b in ret_item.barcodes.all() if b.barcode])
                    except: pass
                elif hasattr(ret_item, 'returned_barcodes'):
                    try:
                        ret_barcodes.extend([b.barcode for b in ret_item.returned_barcodes.all() if b.barcode])
                    except: pass
                
                # نقوم بإضافتها للقائمة مع لاحقة خاصة لتمييزها في القالب
                for code in ret_barcodes:
                    barcodes_list.append(f"{code} (returned)")

        # إنشاء الكائن
        item_data = SimpleNamespace(
            product_name=item.product.product_name if item.product else item.item_name,
            original_quantity=item.purchased_quantity,
            returned_quantity=total_returned_after_edit,
            purchased_quantity=available_quantity, 
            unit_price=item.unit_price,
            purch_total=item.purch_total,
            purch_item_image=item.purch_item_image,
            barcodes=barcodes_list,
        )
        
        items_for_template.append(item_data)

    context = {
        'purchase': purchase,
        'items': items_for_template,
        'title': f'تفاصيل فاتورة الشراء {purchase.uniqueId}',
    }
    
    return render(request, 'invoice/purchase/purch_detail.html', context)




@login_required
def purch_edit(request, slug):
    """تعديل فاتورة شراء موجودة مع تحديث دقيق للمخزون والباركودات - النسخة المعدلة لتتوافق مع منطق المرتجعات الجديد"""
    from django.db.models import Q, Sum
    from decimal import Decimal
    
    purchase = get_object_or_404(Purch, slug=slug)
    
    print(f"🔍 بدء تعديل فاتورة: {purchase.uniqueId}")
    
    # ======== التغيير الرئيسي لمشكلة العرض ========
    # حساب الكميات المرتجعة بعد آخر تعديل للفاتورة
    # هذا يضمن عرض البيانات بشكل صحيح في صفحة التعديل
    reset_date = purchase.last_updated
    
    # حساب الكميات المرتجعة لكل بند بعد آخر تعديل للفاتورة
    returned_items_data = {}
    for item in purchase.purchitem_set.all():
        # استخدام نفس المنطق الجديد في حساب المرتجعات
        total_returned = item.returned_items.filter(
            purchase_return__date_created__gte=reset_date
        ).aggregate(total=Sum('returned_quantity'))['total']
        returned_items_data[item.id] = total_returned if total_returned else Decimal('0.00')
    
    if request.method == 'POST':
        print(f"📝 طلب POST - بدء معالجة البيانات")
        
        # ============================================
        # 🔧 نسخ البيانات أولاً وتعديلها
        # ============================================
        post_data = request.POST.copy()
        files_data = request.FILES
        
        print(f"📊 بيانات POST الأصلية للمورد: {post_data.get('purch_supplier', 'غير محدد')}")
        
        # ============================================
        # 🔧 معالجة حقل المورد إذا جاء من حقل البحث
        # ============================================
        supplier_search_value = post_data.get('supplier-search-input', '')
        if supplier_search_value and supplier_search_value != '':
            print(f"🔍 معالجة حقل البحث عن المورد: {supplier_search_value}")
            
            try:
                if supplier_search_value.isdigit():
                    from django.contrib.auth.models import User
                    supplier = User.objects.get(id=int(supplier_search_value))
                    post_data['purch_supplier'] = str(supplier.id)
                    print(f"✅ وجد المورد بالرقم: {supplier.get_full_name() or supplier.username}")
                else:
                    from django.contrib.auth.models import User
                    suppliers = User.objects.filter(
                        Q(first_name__icontains=supplier_search_value) |
                        Q(last_name__icontains=supplier_search_value) |
                        Q(username__icontains=supplier_search_value)
                    ).first()
                    
                    if suppliers:
                        post_data['purch_supplier'] = str(suppliers.id)
                        print(f"✅ وجد المورد بالاسم: {suppliers.get_full_name() or suppliers.username}")
            except Exception as e:
                print(f"❌ خطأ في البحث عن المورد: {e}")
        
        # ============================================
        # معالجة بيانات البنود
        # ============================================
        total_forms = int(post_data.get('items-TOTAL_FORMS', 0))
        print(f"📊 عدد البنود في POST: {total_forms}")
        
        for i in range(total_forms):
            product_search_key = f'items-{i}-product_search'
            if product_search_key in post_data:
                product_search = post_data[product_search_key]
                print(f"🔍 معالجة البند {i}: product_search = {product_search}")
                
                if product_search and product_search.strip():
                    try:
                        if product_search.isdigit():
                            product = Product.objects.get(id=int(product_search))
                            post_data[f'items-{i}-product'] = str(product.id)
                            post_data[f'items-{i}-item_name'] = product.product_name
                            print(f"✅ وجد المنتج بالرقم: {product.product_name}")
                        else:
                            product = Product.objects.filter(
                                Q(product_name__icontains=product_search) |
                                Q(barcodes__barcode_in__icontains=product_search)
                            ).first()
                            if product:
                                post_data[f'items-{i}-product'] = str(product.id)
                                post_data[f'items-{i}-item_name'] = product.product_name
                                print(f"✅ وجد المنتج بالاسم: {product.product_name}")
                            else:
                                post_data[f'items-{i}-item_name'] = product_search
                                print(f"⚠️ استخدام النص كاسم للبند: {product_search}")
                    except Product.DoesNotExist:
                        post_data[f'items-{i}-item_name'] = product_search
                        print(f"⚠️ استخدام النص كاسم للبند (لا يوجد منتج): {product_search}")
        
        print(f"📊 بيانات POST المعدلة للمورد: {post_data.get('purch_supplier', 'غير محدد')}")
        
        # ============================================
        # إنشاء النماذج مع البيانات المعدلة
        # ============================================
        form = PurchEditForm(post_data, files_data, instance=purchase)
        formset = PurchItemEditFormSet(post_data, files_data, instance=purchase, prefix='items', original_purchase=purchase)
        
        print(f"📋 صحة النموذج الرئيسي: {form.is_valid()}")
        print(f"📋 صحة formset: {formset.is_valid()}")
        
        if form.is_valid() and formset.is_valid():
            print(f"🎯 جميع النماذج صالحة - بدء الحفظ")
            
            try:
                with transaction.atomic():
                    print(f"🔄 بدء المعاملة الذرية")
                    
                    saved_purchase = form.save()
                    print(f"✅ تم حفظ فاتورة الشراء: {saved_purchase.uniqueId}")
                    
                    saved_items = formset.save(commit=False)
                    print(f"📊 عدد البنود المراد حفظها: {len(saved_items)}")
                    
                    # ============================================
                    # 🔧 تحديث المخزون بشكل صحيح - النسخة المعدلة
                    # ============================================
                    
                    for i, item_form in enumerate(formset):
                        item = item_form.instance
                        print(f"\n📝 معالجة البند [{i}]: {item.item_name}")
                        
                        original_item = None
                        if item.pk:
                            try:
                                original_item = PurchItem.objects.get(id=item.id)
                                print(f"📊 البند الأصلي موجود: {original_item.id}")
                                print(f"📊 بيانات البند الأصلي - الكمية: {original_item.purchased_quantity}, المنتج: {original_item.product}")
                            except PurchItem.DoesNotExist:
                                print(f"⚠️ البند الأصلي غير موجود، يعتبر جديداً")
                        
                        item.purch = saved_purchase
                        
                        if f'items-{i}-product_image_upload' in files_data:
                            print(f"🖼️ تم رفع صورة جديدة للبند {i}")
                            uploaded_file = files_data[f'items-{i}-product_image_upload']
                            if uploaded_file:
                                item.purch_item_image = uploaded_file
                        
                        if not item.item_name and item.product:
                            item.item_name = item.product.product_name
                        elif not item.item_name:
                            item_name_from_form = item_form.cleaned_data.get('item_name', '')
                            if item_name_from_form:
                                item.item_name = item_name_from_form
                        
                        if original_item:
                            print(f"🔄 تعديل بند موجود")
                            purchased_quantity_new = item_form.cleaned_data.get('purchased_quantity')
                            unit_price_new = item_form.cleaned_data.get('unit_price')
                            
                            if purchased_quantity_new is not None:
                                item.purchased_quantity = purchased_quantity_new
                            if unit_price_new is not None:
                                item.unit_price = unit_price_new
                            
                            if item.purchased_quantity and item.unit_price:
                                item.purch_total = item.purchased_quantity * item.unit_price
                            
                        else:
                            print(f"🆕 إنشاء بند جديد")
                            if not item.purchased_quantity or not item.unit_price:
                                purchased_quantity_new = item_form.cleaned_data.get('purchased_quantity', Decimal('0.00'))
                                unit_price_new = item_form.cleaned_data.get('unit_price', Decimal('0.00'))
                                
                                if purchased_quantity_new:
                                    item.purchased_quantity = purchased_quantity_new
                                if unit_price_new:
                                    item.unit_price = unit_price_new
                        
                        item.save()
                        print(f"✅ تم حفظ البند: {item.id}")
                        print(f"📊 الكمية المحفوظة: {item.purchased_quantity}, السعر: {item.unit_price}, الإجمالي: {item.purch_total}")
                        
                        # ============================================
                        # 🔧 تحديث المخزون يدوياً - المنطق المعدل
                        # ============================================
                        if original_item:
                            print(f"🔄 تحديث المخزون للتعديل")
                            
                            if item.product and original_item.product:
                                try:
                                    product = item.product
                                    old_product = original_item.product
                                    
                                    print(f"🔄 معالجة مخزون المنتج: {product.product_name}")
                                    
                                    if product.id == old_product.id:
                                        # ⭐⭐⭐ الحل الصحيح والآمن لنفس المنتج ⭐⭐⭐
                                        
                                        old_stock = product.current_stock_quantity
                                        
                                        # ======== تعديل طريقة حساب الكمية المرتجعة ========
                                        # استخدام نفس المنطق الجديد في حساب المرتجعات
                                        total_returned = PurchaseReturnItem.objects.filter(
                                            original_item=original_item,
                                            purchase_return__date_created__gte=reset_date
                                        ).aggregate(total=Sum('returned_quantity'))['total'] or Decimal('0.00')
                                        
                                        # احسب الكمية الفعالة قبل هذا التعديل
                                        effective_old_quantity = original_item.purchased_quantity - total_returned
                                        print(f"📊 الكمية الأصلية: {original_item.purchased_quantity}")
                                        print(f"📊 إجمالي المرتجع لهذا البند (بعد آخر تعديل): {total_returned}")
                                        print(f"📊 الكمية الفعالة القديمة (أصلية - مرتجع): {effective_old_quantity}")
                                        
                                        # احسب الفارق بناءً على الكمية الفعالة
                                        quantity_difference = item.purchased_quantity - effective_old_quantity
                                        product.current_stock_quantity += quantity_difference

                                        print(f"📊 المخزون قبل التعديل: {old_stock}")
                                        print(f"📊 الفارق في الكمية (جديد - فعال قديم): {item.purchased_quantity} - {effective_old_quantity} = {quantity_difference}")
                                        print(f"📊 المخزون بعد التعديل: {product.current_stock_quantity}")
                                        
                                        product.save()
                                        print(f"✅ تم تحديث مخزون المنتج بنجاح")
                                        
                                    else:
                                        # ⭐⭐⭐ الحل الصحيح والآمن لتغيير المنتج ⭐⭐⭐
                                        print(f"🔄 تغيير المنتج: من {old_product.product_name} إلى {product.product_name}")
                                        
                                        # ======== تعديل طريقة حساب الكمية المرتجعة ========
                                        # استخدام نفس المنطق الجديد في حساب المرتجعات
                                        total_returned_old = PurchaseReturnItem.objects.filter(
                                            original_item=original_item,
                                            purchase_return__date_created__gte=reset_date
                                        ).aggregate(total=Sum('returned_quantity'))['total'] or Decimal('0.00')
                                        effective_old_quantity_for_old_product = original_item.purchased_quantity - total_returned_old
                                        
                                        old_product.current_stock_quantity -= effective_old_quantity_for_old_product
                                        old_product.save()
                                        print(f"📉 خصم الكمية الفعالة من المنتج القديم: {effective_old_quantity_for_old_product}")
                                        print(f"📊 مخزون المنتج القديم الجديد: {old_product.current_stock_quantity}")
                                        
                                        # 2. إضافة الكمية الجديدة للمنتج الجديد
                                        old_stock_new = product.current_stock_quantity
                                        product.current_stock_quantity += item.purchased_quantity
                                        product.save()
                                        print(f"📈 إضافة الكمية الجديدة للمنتج الجديد: {item.purchased_quantity}")
                                        print(f"📊 مخزون المنتج الجديد: من {old_stock_new} إلى {product.current_stock_quantity}")
                                        
                                except Exception as e:
                                    print(f"❌ خطأ في تحديث المخزون: {e}")
                                    import traceback
                                    traceback.print_exc()
                            else:
                                print(f"⚠️ تحذير: أحد المنتجات غير موجود")
                        else:
                            # حالة الإنشاء الجديد للبند
                            print(f"🆕 تحديث المخزون للإنشاء الجديد")
                            if item.product:
                                try:
                                    product = item.product
                                    print(f"🆕 إضافة مخزون جديد: {item.purchased_quantity} من {product.product_name}")
                                    print(f"📊 المخزون الحالي قبل الإضافة: {product.current_stock_quantity}")
                                    
                                    old_stock = product.current_stock_quantity
                                    product.current_stock_quantity += item.purchased_quantity
                                    print(f"📊 المخزون الجديد: {product.current_stock_quantity}")
                                    
                                    product.save()
                                    print(f"✅ تم إضافة المخزون الجديد")
                                    
                                except Exception as e:
                                    print(f"❌ خطأ في إضافة المخزون الجديد: {e}")
                        
                        # ============================================
                        # معالجة الباركودات (بقيت كما هي)
                        # ============================================
                        print(f"📊 معالجة الباركودات للبند {item.id}")
                        barcode_keys = [k for k in post_data.keys() if k.startswith(f'item_{i}_barcodes[')]
                        new_barcodes = [post_data.get(k, '').strip() for k in barcode_keys if post_data.get(k, '').strip()]
                        
                        print(f"🔄 مقارنة الباركودات: قديم {item.item_barcodes.count()}، جديد {len(new_barcodes)}")
                        
                        for existing_barcode in item.item_barcodes.all():
                            if existing_barcode.barcode.barcode_in not in new_barcodes:
                                print(f"🗑️ حذف الباركود: {existing_barcode.barcode.barcode_in}")
                                existing_barcode.delete()
                        
                        for barcode_value in new_barcodes:
                            if not item.item_barcodes.filter(barcode__barcode_in=barcode_value).exists():
                                try:
                                    barcode_obj, created = Barcode.objects.get_or_create(
                                        barcode_in=barcode_value,
                                        defaults={'status': 'active', 'product': item.product if item.product else None}
                                    )
                                    PurchItemBarcode.objects.get_or_create(
                                        purch_item=item, barcode=barcode_obj,
                                        defaults={'quantity_used': Decimal('1.00'), 'barcode_status': 'active'}
                                    )
                                    print(f"✅ تم إضافة الباركود: {barcode_value}")
                                except Exception as e:
                                    print(f"❌ خطأ في معالجة الباركود: {e}")
                    
                    # ============================================
                    # 🔧 معالجة البنود المحذوفة
                    # ============================================
                    for item in formset.deleted_objects:
                        print(f"\n🗑️ حذف البند: {item.id} - {item.item_name}")
                        item.delete()
                        print(f"✅ تم حذف البند وتراجع عن مخزونه")
                    
                    # إعادة حساب الإجماليات
                    print(f"\n🧮 إعادة حساب الإجماليات")
                    saved_purchase.calculate_and_save_totals()
                    print(f"✅ تم حساب الإجماليات: {saved_purchase.purch_final_total}")
                    
                    if saved_purchase.paid_amount > 0:
                        print(f"💰 إنشاء حركة صندوق للمبلغ: {saved_purchase.paid_amount}")
                        saved_purchase.create_cash_transaction()
                        print(f"✅ تم إنشاء حركة الصندوق")
                    
                    messages.success(request, _('✅ تم تعديل فاتورة الشراء بنجاح وتحديث المخزون والباركودات'))
                    print(f"🎉 تم تعديل الفاتورة بنجاح: {saved_purchase.uniqueId}")
                    
                    return redirect('invoice:purch_detail', slug=saved_purchase.slug)

            except Exception as e:
                print(f"❌ خطأ في تعديل فاتورة الشراء: {e}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'❌ حدث خطأ: {str(e)}')
        else:
            print(f"❌ أخطاء في النماذج")
            for field, errors in form.errors.items():
                print(f"  {field}: {errors}")
            for form_in_formset in formset:
                if form_in_formset.errors:
                    print(f"  Form {form_in_formset.prefix}: {form_in_formset.errors}")
            messages.error(request, '❌ يرجى تصحيح الأخطاء في النموذج')
    else:
        print(f"📄 طلب GET - تحميل صفحة التعديل")
        form = PurchEditForm(instance=purchase)
        
        # ======== تعديل طريقة عرض البيانات في حالة GET ========
        # تمرير بيانات المرتجعات إلى formset لعرضها بشكل صحيح
        formset = PurchItemEditFormSet(
            instance=purchase, 
            prefix='items', 
            original_purchase=purchase,
            returned_items_data=returned_items_data  # تمرير بيانات المرتجعات كوسيط مسمى
        )
        print(f"✅ تم تحميل النماذج للعرض - عدد البنود: {len(formset)}")

    return render(request, 'invoice/purchase/purch_edit.html', {
        'form': form,
        'formset': formset,
        'purchase': purchase,
        'title': f'تعديل فاتورة الشراء {purchase.uniqueId}'
    })



@login_required
def purch_delete(request, slug):
    """حذف فاتورة شراء مع الباركودات المرتبطة"""
    purchase = get_object_or_404(Purch, slug=slug)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                barcodes_to_delete = []
                
                for purch_item in purchase.purchitem_set.all():
                    for purch_barcode in purch_item.item_barcodes.all():
                        barcodes_to_delete.append(purch_barcode.barcode)
                    
                    PurchItemBarcode.objects.filter(purch_item=purch_item).delete()
                
                purchase.delete()
                
                deleted_barcodes_count = 0
                for barcode in barcodes_to_delete:
                    if not PurchItemBarcode.objects.filter(barcode=barcode).exists():
                        barcode.delete()
                        deleted_barcodes_count += 1
                
                messages.success(request, 
                    _(f'تم حذف فاتورة الشراء بنجاح. تم حذف {deleted_barcodes_count} باركود.'))
                return redirect('invoice:purch_list')
                
        except Exception as e:
            logger.error(f"Error deleting purchase {purchase.uniqueId}: {str(e)}")
            messages.error(request, f'حدث خطأ أثناء حذف الفاتورة: {str(e)}')
    
    return render(request, 'invoice/purchase/purch_confirm_delete.html', {
        'purchase': purchase,
        'title': _('حذف فاتورة شراء')
    })




#================================================
#                 مرتجع المشتريات              #
# ===============================================




@login_required
def purch_return_create_view(request, slug):
    """إنشاء مرتجع فاتورة مشتريات - نسخة محسنة"""
    original_purchase = get_object_or_404(Purch, slug=slug)
    
    # التحقق من وجود بنود في الفاتورة
    if not original_purchase.purchitem_set.exists():
        messages.warning(request, 'لا توجد بنود في هذه الفاتورة للإرجاع')
        return redirect('invoice:purch_detail', slug=slug)
    
    # الحصول على بيانات الدفع من الفاتورة الأصلية
    original_payment_method = original_purchase.purch_payment_method
    payment_method_name = original_payment_method.name if original_payment_method else 'على الآجل'
    is_cash_payment = False
    
    if original_payment_method and hasattr(original_payment_method, 'is_cash'):
        is_cash_payment = original_payment_method.is_cash
    
    # حساب الكميات المرتجعة سابقاً
    reset_date = original_purchase.last_updated
    
    returned_items_data = {}
    for item in original_purchase.purchitem_set.all():
        total_returned = item.returned_items.filter(
            purchase_return__date_created__gte=reset_date
        ).aggregate(total=Sum('returned_quantity'))['total']
        returned_items_data[item.id] = total_returned if total_returned else Decimal('0.00')
    
    # حساب الإجمالي المتوقع للمرتجع (لتعيينه في المبلغ المستلم)
    expected_return_total = Decimal('0.00')
    for item in original_purchase.purchitem_set.all():
        returned_quantity = returned_items_data.get(item.id, Decimal('0.00'))
        available_quantity = item.purchased_quantity - returned_quantity
        if available_quantity > 0:
            expected_return_total += available_quantity * item.unit_price
    
    if request.method == 'POST':
        form = PurchaseReturnForm(request.POST)
        
        items_data = []
        form_valid = True
        has_any_returned_items = False
        actual_return_total = Decimal('0.00')
        
        original_items = original_purchase.purchitem_set.all().select_related('product')
        
        for item in original_items:
            # حساب الكمية المتاحة
            returned_quantity = returned_items_data.get(item.id, Decimal('0.00'))
            available_quantity = item.purchased_quantity - returned_quantity
            
            prefix = f"item-{item.id}"
            
            # الحصول على الباركودات المتاحة
            available_barcodes = PurchItemBarcode.objects.filter(
                purch_item=item, 
                barcode_status='active'
            ).select_related('barcode')
            
            barcode_queryset = Barcode.objects.filter(
                id__in=available_barcodes.values_list('barcode_id', flat=True)
            )
            
            # إنشاء النموذج
            item_form = PurchaseReturnItemForm(
                request.POST, 
                prefix=prefix,
                original_item=item
            )
            
            item_form.fields['original_barcodes'].queryset = barcode_queryset
            
            # التحقق إذا كان هناك باركودات متاحة
            has_barcodes = available_barcodes.exists()
            
            if has_barcodes and item_form.is_valid():
                selected_barcodes = item_form.cleaned_data.get('original_barcodes', [])
                if selected_barcodes:
                    item_form.cleaned_data['returned_quantity'] = Decimal(str(len(selected_barcodes)))
                    item_form.data = item_form.data.copy()
                    item_form.data[f"{prefix}-returned_quantity"] = str(len(selected_barcodes))
            
            if not item_form.is_valid():
                form_valid = False
                logger.error(f"خطأ في نموذج البند {item.id}: {item_form.errors}")
            
            if item_form.is_valid():
                returned_quantity_value = item_form.cleaned_data.get('returned_quantity', Decimal('0.00'))
                if returned_quantity_value and returned_quantity_value > 0:
                    has_any_returned_items = True
                    # حساب الإجمالي الفعلي للبند
                    unit_price = item_form.cleaned_data.get('return_unit_price', Decimal('0.00'))
                    actual_return_total += returned_quantity_value * unit_price
            
            items_data.append({
                'form': item_form,
                'original_item': item,
                'product': item.product if hasattr(item, 'product') else None,
                'available_quantity': available_quantity,
                'previously_returned': returned_quantity,
                'available_barcodes': available_barcodes,
                'available_barcodes_count': available_barcodes.count(),
                'has_barcodes': has_barcodes
            })
        
        if form.is_valid() and form_valid:
            if not has_any_returned_items:
                messages.error(request, 'يجب إدخال كمية مرتجعة لبند واحد على الأقل')
                context = {
                    'form': form,
                    'items_data': items_data,
                    'original_purchase': original_purchase,
                    'payment_method_name': payment_method_name,
                    'is_cash_payment': is_cash_payment,
                    'expected_return_total': expected_return_total,
                    'title': f'إنشاء مرتجع لفاتورة شراء {original_purchase.uniqueId}'
                }
                return render(request, 'invoice/purchase/purch_return_form.html', context)
            
            try:
                with transaction.atomic():
                    # حفظ فاتورة المرتجع
                    purchase_return = form.save(commit=False)
                    purchase_return.original_purchase = original_purchase
                    purchase_return.created_by = request.user
                    purchase_return.purch_supplier = original_purchase.purch_supplier
                    
                    if hasattr(original_purchase, 'purch_currency'):
                        purchase_return.purch_currency = original_purchase.purch_currency
                    
                    # تعيين المبلغ المستلم
                    paid_amount = form.cleaned_data.get('paid_amount', Decimal('0.00'))
                    purchase_return.paid_amount = paid_amount
                    purchase_return.remaining_amount = Decimal('0.00')
                    purchase_return.settlement_status = 'pending'
                    purchase_return.return_final_total = actual_return_total
                    purchase_return.save()
                    
                    saved_items = False
                    
                    # حفظ بنود المرتجع
                    for item_data in items_data:
                        item_form = item_data['form']
                        
                        if item_form.is_valid():
                            returned_quantity = item_form.cleaned_data.get('returned_quantity', Decimal('0.00'))
                            
                            if returned_quantity and returned_quantity > 0:
                                item_instance = item_form.save(commit=False)
                                item_instance.purchase_return = purchase_return
                                item_instance.return_total = returned_quantity * item_form.cleaned_data.get('return_unit_price', Decimal('0.00'))
                                
                                if not item_instance.product and item_data['original_item'].product:
                                    item_instance.product = item_data['original_item'].product
                                
                                item_instance.save()
                                
                                # حفظ الباركودات المرتجعة
                                returned_barcodes = item_form.cleaned_data.get('original_barcodes')
                                if returned_barcodes:
                                    for barcode in returned_barcodes:
                                        PurchaseReturnItemBarcode.objects.create(
                                            purchase_return_item=item_instance,
                                            barcode=barcode
                                        )
                                
                                saved_items = True
                    
                    if not saved_items:
                        purchase_return.delete()
                        messages.warning(request, 'لم يتم تحديد أي كميات للاسترجاع')
                        return redirect('invoice:purch_detail', slug=slug)
                    
                    # تحديث الإجماليات
                    purchase_return.refresh_from_db()
                    purchase_return.return_subtotal = actual_return_total
                    purchase_return.return_final_total = actual_return_total
                    purchase_return.remaining_amount = actual_return_total - paid_amount
                    purchase_return.update_settlement_status()
                    purchase_return.save(update_fields=['return_subtotal', 'return_final_total', 'remaining_amount', 'settlement_status'])
                    
                    # للفواتير النقدية: التحقق من المبلغ المستلم
                    if is_cash_payment:
                        paid_amount_modified = request.POST.get('paid_amount_modified') == 'true'
                        
                        # إذا لم يعدل المستخدم المبلغ، نعيّن الإجمالي كاملاً
                        if not paid_amount_modified:
                            purchase_return.paid_amount = actual_return_total
                            purchase_return.remaining_amount = Decimal('0.00')
                            purchase_return.settlement_status = 'settled'
                            purchase_return.save(update_fields=['paid_amount', 'remaining_amount', 'settlement_status'])
                            paid_amount = actual_return_total
                        
                        # تسجيل حركة الصندوق
                        if paid_amount > 0:
                            try:
                                CashTransaction.objects.create(
                                    transaction_date=timezone.now(),
                                    amount_in=paid_amount,
                                    transaction_type='purchase_return',
                                    notes=f"استلام {paid_amount} مقابل مرتجع فاتورة {original_purchase.uniqueId}",
                                    created_by=request.user,
                                    purchase_invoice=original_purchase,
                                    payment_method=original_payment_method
                                )
                                
                                if paid_amount >= actual_return_total:
                                    messages.success(request, 
                                        f'✅ تم إنشاء فاتورة المرتجع {purchase_return.uniqueId} واستلام كامل المبلغ ({paid_amount})')
                                else:
                                    messages.success(request, 
                                        f'✅ تم إنشاء فاتورة المرتجع {purchase_return.uniqueId} واستلام {paid_amount} من أصل {actual_return_total}')
                                    
                            except Exception as e:
                                logger.error(f"خطأ في تسجيل حركة الصندوق: {e}")
                                messages.warning(request, f'تم إنشاء المرتجع ولكن حدث خطأ في تسجيل حركة الصندوق')
                        else:
                            messages.info(request, 
                                f'ℹ️ تم إنشاء فاتورة المرتجع {purchase_return.uniqueId} بدون استلام نقدية')
                    else:
                        messages.success(request, 
                            f'✅ تم إنشاء فاتورة المرتجع {purchase_return.uniqueId} بنجاح')
                    
                    return redirect('invoice:purch_detail', slug=original_purchase.slug)
                    
            except Exception as e:
                logger.error(f"خطأ في إنشاء المرتجع: {str(e)}", exc_info=True)
                messages.error(request, f'حدث خطأ أثناء إنشاء المرتجع: {str(e)}')
        else:
            # عرض الأخطاء
            error_messages = []
            
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        error_messages.append(f"{form.fields[field].label if field in form.fields else field}: {error}")
            
            for item_data in items_data:
                if item_data['form'].errors:
                    item_name = item_data['product'].product_name if item_data['product'] else f"بند {item_data['original_item'].id}"
                    for field, errors in item_data['form'].errors.items():
                        for error in errors:
                            error_messages.append(f"{item_name} - {error}")
            
            if error_messages:
                messages.error(request, 'يرجى تصحيح الأخطاء التالية:')
                for error_msg in error_messages[:5]:
                    messages.error(request, f"• {error_msg}")
            
            context = {
                'form': form,
                'items_data': items_data,
                'original_purchase': original_purchase,
                'payment_method_name': payment_method_name,
                'is_cash_payment': is_cash_payment,
                'expected_return_total': expected_return_total,
                'title': f'إنشاء مرتجع لفاتورة شراء {original_purchase.uniqueId}'
            }
            return render(request, 'invoice/purchase/purch_return_form.html', context)
    
    else:
        # حالة GET
        form = PurchaseReturnForm(
            initial={
                'return_date': timezone.now().date(),
                'paid_amount': expected_return_total if is_cash_payment else Decimal('0.00')
            }
        )
        
        items_data = []
        original_items = original_purchase.purchitem_set.all().select_related('product')
        
        for item in original_items:
            total_returned = returned_items_data.get(item.id, Decimal('0.00'))
            available_quantity = item.purchased_quantity - total_returned
            
            prefix = f"item-{item.id}"
            
            available_barcodes = PurchItemBarcode.objects.filter(
                purch_item=item, 
                barcode_status='active'
            ).select_related('barcode')
            
            initial_data = {
                'original_item': item,
                'product': item.product,
                'purchased_quantity': item.purchased_quantity,
                'return_unit_price': item.unit_price,
                'return_total': Decimal('0.00'),
                'returned_quantity': '',
            }
            
            item_form = PurchaseReturnItemForm(
                prefix=prefix,
                initial=initial_data,
                original_item=item
            )
            
            item_form.fields['original_barcodes'].queryset = Barcode.objects.filter(
                id__in=available_barcodes.values_list('barcode_id', flat=True)
            )
            
            has_barcodes = available_barcodes.exists()
            
            # تعيين خصائص حقل الكمية
            if available_quantity > 0:
                if has_barcodes:
                    item_form.fields['returned_quantity'].widget.attrs.update({
                        'readonly': True,
                        'placeholder': 'اختر الباركودات',
                        'class': 'quantity-with-barcode form-control text-center'
                    })
                else:
                    item_form.fields['returned_quantity'].widget.attrs.update({
                        'max': available_quantity,
                        'readonly': False,
                        'placeholder': 'أدخل الكمية',
                        'class': 'quantity-without-barcode form-control text-center'
                    })
            else:
                item_form.fields['returned_quantity'].widget.attrs.update({
                    'readonly': True,
                    'placeholder': 'غير متاح',
                    'value': '0',
                    'class': 'form-control text-center bg-light'
                })
            
            items_data.append({
                'form': item_form,
                'original_item': item,
                'product': item.product,
                'available_quantity': available_quantity,
                'previously_returned': total_returned,
                'available_barcodes': available_barcodes,
                'available_barcodes_count': available_barcodes.count(),
                'has_barcodes': has_barcodes,
                'item_image': item.purch_item_image or (item.product.product_image if item.product else None)
            })
    
    context = {
        'form': form,
        'items_data': items_data,
        'original_purchase': original_purchase,
        'payment_method_name': payment_method_name,
        'is_cash_payment': is_cash_payment,
        'title': f'إنشاء مرتجع لفاتورة شراء {original_purchase.uniqueId}',
        'supplier': original_purchase.purch_supplier,
        'total_invoice_amount': original_purchase.purch_final_total,
        'expected_return_total': expected_return_total,
    }
    return render(request, 'invoice/purchase/purch_return_form.html', context)


@login_required
def purchase_return_list_view(request):
    """قائمة مرتجعات المشتريات"""
    # فلترة البحث
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    supplier_filter = request.GET.get('supplier', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # قاعدة الاستعلام - استخدام purch_supplier
    purchase_returns = PurchaseReturn.objects.all().select_related(
        'original_purchase', 'created_by', 'purch_supplier'
    ).order_by('-return_date', '-date_created')
    
    # تطبيق الفلاتر
    if search_query:
        purchase_returns = purchase_returns.filter(
            Q(uniqueId__icontains=search_query) |
            Q(purch_supplier__username__icontains=search_query) |
            Q(purch_supplier__first_name__icontains=search_query) |
            Q(purch_supplier__last_name__icontains=search_query) |
            Q(original_purchase__uniqueId__icontains=search_query)
        )
    
    if status_filter:
        if status_filter == 'completed':
            purchase_returns = purchase_returns.filter(settlement_status='settled')
        elif status_filter == 'partial':
            purchase_returns = purchase_returns.filter(settlement_status='partial')
        elif status_filter == 'pending':
            purchase_returns = purchase_returns.filter(settlement_status='pending')
    
    if supplier_filter and supplier_filter.isdigit():
        purchase_returns = purchase_returns.filter(purch_supplier_id=supplier_filter)
    
    if date_from:
        purchase_returns = purchase_returns.filter(return_date__gte=date_from)
    
    if date_to:
        purchase_returns = purchase_returns.filter(return_date__lte=date_to)
    
    # ترقيم الصفحات
    paginator = Paginator(purchase_returns, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # قائمة الموردين للفلترة
    suppliers = User.objects.filter(is_active=True).order_by('username')
    
    context = {
        'purchase_returns': page_obj,
        'page_obj': page_obj,
        'suppliers': suppliers,
        'title': 'قائمة مرتجعات المشتريات',
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'invoice/purchase/purchase_return_list.html', context)


@login_required
def purchase_return_detail_view(request, slug):
    """عرض تفاصيل مرتجع المشتريات"""
    purchase_return = get_object_or_404(
        PurchaseReturn.objects.select_related(
            'original_purchase', 'created_by', 'purch_supplier'
        ).prefetch_related(
            'return_items__product',  # المفتاح: return_items هو الاسم الصحيح
        ),
        slug=slug
    )
    
    # حساب الإحصائيات - استخدام return_items
    items = purchase_return.return_items.all()
    items_count = items.count()
    total_quantity = items.aggregate(total=Sum('returned_quantity'))['total'] or 0
    
    context = {
        'return': purchase_return,
        'purchase_return': purchase_return,
        'items': items,
        'items_count': items_count,
        'total_quantity': total_quantity,
        'title': f'تفاصيل مرتجع المشتريات {purchase_return.uniqueId}'
    }
    
    return render(request, 'invoice/purchase/purch_return_detail.html', context)


@login_required
def purchase_return_delete_view(request, slug):
    """حذف مرتجع المشتريات"""
    purchase_return = get_object_or_404(PurchaseReturn, slug=slug)
    
    if request.method == 'POST':
        try:
            # حفظ معلومات للتوجيه بعد الحذف
            original_purch_slug = purchase_return.original_purchase.slug if purchase_return.original_purchase else None
            return_uniqueId = purchase_return.uniqueId
            
            # حذف المرتجع
            purchase_return.delete()
            
            messages.success(request, f'تم حذف مرتجع المشتريات {return_uniqueId} بنجاح')
            
            # التوجيه إلى قائمة المرتجعات أو فاتورة الشراء الأصلية
            if original_purch_slug:
                return redirect('invoice:purch_detail', slug=original_purch_slug)
            else:
                return redirect('invoice:purchase_return_list')
                
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف المرتجع: {str(e)}')
            return redirect('invoice:purchase_return_detail', slug=slug)
    
    context = {
        'purchase_return': purchase_return,
        'title': f'حذف مرتجع المشتريات {purchase_return.uniqueId}'
    }
    
    return render(request, 'invoice/purchase/purchase_return_confirm_delete.html', context)





#================================================
#               المواد  و الباركود            #
# ===============================================


@login_required
def product_list(request):
    """عرض قائمة المنتجات مع فلترة الباركودات النشطة فقط"""
    # تعديل السطر التالي: استبدال is_active=True بـ status='active'
    products = Product.objects.all().prefetch_related(
        Prefetch('barcodes', queryset=Barcode.objects.filter(status='active'), to_attr='active_barcodes')
    ).order_by('-date_created')
    
    return render(request, 'invoice/products/product_list.html', {
        'products': products,
        'title': _('إدارة المنتجات')
    })


@login_required
def product_create(request):
    """إنشاء مادة جديدة - معلومات فقط"""
    print("✅ تم الدخول إلى product_create")
    
    if request.method == 'POST':
        print("✅ الطريقة POST")
        product_name = request.POST.get('product_name')
        product_description = request.POST.get('product_description', '')
        product_image = request.FILES.get('product_image')
        
        print(f"✅ اسم المادة: {product_name}")
        
        if not product_name:
            messages.error(request, _('اسم المادة مطلوب'))
            return render(request, 'invoice/products/product_form.html', {
                'title': _('إنشاء مادة جديدة')
            })
        
        try:
            with transaction.atomic():
                # إنشاء المادة بالقيم الافتراضية
                product = Product(
                    product_name=product_name,
                    product_description=product_description,
                    # قيم افتراضية للحقول المالية
                    purch_price=Decimal('0.00'),
                    sale_price=Decimal('0.00'),
                    current_stock_quantity=Decimal('0.00'),
                    average_purchase_cost=Decimal('0.00'),
                    retail_profit_margin=Decimal('25.00'),
                    semi_wholesale_profit_margin=Decimal('20.00'),
                    wholesale_profit_margin=Decimal('15.00'),
                    price_adjustment=Decimal('0.00'),
                    retail_price=Decimal('0.00'),
                    semi_wholesale_price=Decimal('0.00'),
                    wholesale_price=Decimal('0.00')
                )
                
                # إضافة الصورة إذا وجدت
                if product_image:
                    product.product_image = product_image
                
                # حفظ المادة
                product.save()
                print(f"✅ تم حفظ المادة: {product.product_name} - ID: {product.id} - Slug: {product.slug}")
                
                messages.success(request, _('تم إنشاء المادة بنجاح'))
                # تأكد من استخدام invoice: في redirect
                return redirect('invoice:product_list')
                
        except Exception as e:
            print(f"❌ خطأ في الحفظ: {str(e)}")
            messages.error(request, f'حدث خطأ أثناء إنشاء المادة: {str(e)}')
    
    # GET request - عرض النموذج
    return render(request, 'invoice/products/product_form.html', {
        'title': _('إنشاء مادة جديدة')
    })



@login_required
def product_detail(request, slug):
    """عرض تفاصيل المنتج"""
    product = get_object_or_404(Product, slug=slug)
    barcodes = product.barcodes.all()
    
    return render(request, 'invoice/products/product_detail.html', {
        'product': product,
        'barcodes': barcodes,
        'title': _('تفاصيل المنتج')
    })


@login_required
def product_delete(request, slug):
    """حذف منتج"""
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        product_name = product.product_name
        product.delete()
        messages.success(request, f'تم حذف المنتج "{product_name}" بنجاح')
        return redirect('invoice:product_list')
    
    return render(request, 'invoice/products/product_confirm_delete.html', {
        'product': product,
        'title': _('تأكيد حذف المنتج')
    })

#--------------

@login_required
def product_edit(request, slug):
    """تعديل مادة موجودة - معلومات فقط"""
    product = get_object_or_404(Product, slug=slug)
    print(f"✅ تعديل المادة: {product.product_name} - Slug: {slug}")
    
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        product_description = request.POST.get('product_description', '')
        product_image = request.FILES.get('product_image')
        remove_image = request.POST.get('remove_image')  # للتحقق من إزالة الصورة
        
        if not product_name:
            messages.error(request, _('اسم المادة مطلوب'))
            return render(request, 'invoice/products/product_edit.html', {
                'product': product,
                'title': _('تعديل المادة')
            })
        
        try:
            with transaction.atomic():
                # تحديث المعلومات الأساسية فقط
                product.product_name = product_name
                product.product_description = product_description
                
                # معالجة الصورة
                if remove_image == 'true':
                    # حذف الصورة القديمة إذا وجدت
                    if product.product_image:
                        product.product_image.delete()
                    product.product_image = None
                elif product_image:
                    # حذف الصورة القديمة إذا وجدت
                    if product.product_image:
                        product.product_image.delete()
                    product.product_image = product_image
                
                # حفظ التغييرات
                product.save()
                print(f"✅ تم تحديث المادة: {product.product_name}")
                
                messages.success(request, _('تم تحديث المادة بنجاح'))
                return redirect('invoice:product_detail', slug=product.slug)
                
        except Exception as e:
            print(f"❌ خطأ في تحديث المادة: {str(e)}")
            messages.error(request, f'حدث خطأ أثناء تحديث المادة: {str(e)}')
    
    # في حالة طلب GET، اعرض النموذج مع البيانات الحالية للمنتج
    return render(request, 'invoice/products/product_edit.html', {
        'product': product,
        'title': _('تعديل المادة')
    })

#--------------


# نظام التسعير 



@login_required
def product_bulk_update(request):
    """تحديث جماعي أو فردي للأسعار مع نظام مستويات ديناميكي غير محدود"""
    
    PRICING_PASSWORD = "1234" 

    if request.method == 'POST':
        try:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'خطأ في تنسيق البيانات'}, status=400)

            if 'bulk_updates' in data or 'save_tiers_settings' in data or 'reset_data' in data:
                provided_password = data.get('password', '')
                if provided_password != PRICING_PASSWORD:
                    return JsonResponse({'success': False, 'message': 'كلمة المرور غير صحيحة!'}, status=403)

            def to_decimal(val):
                try:
                    return Decimal(str(val).strip())
                except:
                    return Decimal('0.00')

            # === سيناريو 1: إضافة مستوى تسعير جديد ===
            if 'add_tier' in data:
                name = data.get('tier_name', '').strip()
                if not name:
                    return JsonResponse({'success': False, 'message': 'اسم المستوى مطلوب'}, status=400)
                
                order = PricingTier.objects.count()
                tier = PricingTier.objects.create(name=name, display_order=order)
                
                return JsonResponse({
                    'success': True, 
                    'message': 'تم إضافة المستوى بنجاح',
                    'tier_id': tier.id,
                    'tier_name': tier.name
                })

            # === سيناريو 2: حذف مستوى تسعير ===
            if 'delete_tier' in data:
                tier_id = data.get('tier_id')
                PricingTier.objects.filter(id=tier_id).delete()
                return JsonResponse({'success': True, 'message': 'تم حذف المستوى'})

            # === سيناريو 3: حفظ النسب الجديدة وتحديث أسعار المنتجات ===
            if 'save_tiers_settings' in data or 'bulk_updates' in data:
                tiers_data = data.get('tiers', [])
                bulk_updates = data.get('bulk_updates', {})
                
                with transaction.atomic():
                    for t in tiers_data:
                        PricingTier.objects.filter(id=t['id']).update(
                            name=t['name'],
                            discount_percent=to_decimal(t.get('percent', 0))
                        )
                    
                    if bulk_updates:
                        for product_id, prices in bulk_updates.items():
                            try:
                                product = Product.objects.get(id=product_id)
                                
                                if 'wholesale_price' in prices:
                                    product.wholesale_price = to_decimal(prices['wholesale_price'])
                                    product.save()
                                
                                for field_name, tier_price in prices.items():
                                    if field_name.startswith('tier_'):
                                        tier_id = field_name.replace('tier_', '')
                                        ProductPriceTier.objects.update_or_create(
                                            product=product,
                                            tier_id=tier_id,
                                            defaults={'price': to_decimal(tier_price)}
                                        )
                            except Product.DoesNotExist:
                                continue
                
                return JsonResponse({'success': True, 'message': 'تم التحديث بنجاح'})

            # === سيناريو 4: إعادة ضبط النظام ===
            if 'reset_data' in data:
                settings_obj = PricingSetting.get_settings()
                settings_obj.profit_margin = Decimal('0.00')
                settings_obj.conversion_factor = Decimal('0.00')
                settings_obj.save()
                
                with transaction.atomic():
                    products = Product.objects.all()
                    products.update(wholesale_price=F('average_purchase_cost'))
                    ProductPriceTier.objects.all().delete()
                    PricingTier.objects.update(discount_percent=Decimal('0.00'))
                
                return JsonResponse({'success': True, 'message': 'تم إعادة ضبط النظام بنجاح'})

            # === سيناريو 5: تحديث فردي ===
            elif 'manual_update' in data:
                product_id = data.get('product_id')
                updates = data.get('updates', {})
                
                try:
                    product = Product.objects.get(id=product_id)
                    field = updates.get('field')
                    value = updates.get('value')
                    
                    if field == 'wholesale_price':
                        product.wholesale_price = to_decimal(value)
                        product.save()
                    elif field and field.startswith('tier_'):
                        tier_id = field.replace('tier_', '')
                        ProductPriceTier.objects.update_or_create(
                            product=product,
                            tier_id=tier_id,
                            defaults={'price': to_decimal(value)}
                        )
                        
                    return JsonResponse({'success': True, 'message': 'تم الحفظ'})
                except Product.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'المنتج غير موجود'}, status=404)

            return JsonResponse({'success': False, 'message': 'طلب غير معروف'}, status=400)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': f'خطأ: {str(e)}'}, status=500)

    # ==========================================
    # عرض الصفحة (GET) - الجزء المسبب للمشكلة إذا لم يكن صحيحاً
    # ==========================================
    products_qs = Product.objects.all().order_by('-date_created').prefetch_related('tier_prices__tier')
    settings = PricingSetting.get_settings()
    tiers_qs = PricingTier.objects.all().order_by('display_order')
    
    # 1. تحويل المستويات إلى قائمة (لحل مشكلة JSON)
    tiers_list = [
        {
            'id': t.id,
            'name': t.name,
            'percent': float(t.discount_percent or 0)
        }
        for t in tiers_qs
    ]
    
    # 2. تحويل المنتجات إلى قائمة (لحل مشكلة JSON)
    products_list = [
        {
            'id': p.id,
            'name': p.product_name,
            'stock': p.current_stock_quantity,
            'cost': str(p.average_purchase_cost or 0),
            'wholesale': str(p.wholesale_price or 0),
            'tier_prices': {str(tp.tier_id): str(tp.price) for tp in p.tier_prices.all()}
        }
        for p in products_qs
    ]
    
    # 3. إرسال القوائم (وليس الـ QuerySet) إلى القالب
    return render(request, 'invoice/products/product_bulk_update.html', {
        'products': products_list, 
        'tiers': tiers_list,        # لاحظ أننا أرسلنا tiers_list وليس tiers_qs
        'settings': settings,
        'title': 'تحديث جماعي للمواد'
    })


# ===============================================
#  API: إدارة التصنيفات (الفئات)
# ===============================================

@login_required
def manage_categories(request):
    """صفحة إدارة تصنيفات المتجر"""
    categories = Category.objects.all().select_related('pricing_tier').order_by('display_order')
    tiers = PricingTier.objects.all()
    return render(request, 'invoice/store/manage_categories.html', {
        'categories': categories,
        'tiers': tiers,
        'title': 'إدارة تصنيفات المتجر'
    })


@login_required
@require_POST
def api_add_category(request):
    """إنشاء تصنيف جديد"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'message': 'اسم التصنيف مطلوب'}, status=400)
        
        category = Category.objects.create(
            name=name,
            pricing_tier_id=data.get('tier_id') or None,
            display_order=Category.objects.count()
        )
        return JsonResponse({'success': True, 'message': 'تم إنشاء التصنيف'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_POST
def api_update_category(request, cat_id):
    """تحديث بيانات التصنيف"""
    try:
        data = json.loads(request.body)
        category = get_object_or_404(Category, id=cat_id)
        category.name = data.get('name', category.name)
        category.pricing_tier_id = data.get('tier_id') or None
        category.is_active = data.get('is_active', category.is_active)
        category.save()
        return JsonResponse({'success': True, 'message': 'تم التحديث'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_POST
def api_delete_category(request, cat_id):
    """حذف تصنيف"""
    try:
        get_object_or_404(Category, id=cat_id).delete()
        return JsonResponse({'success': True, 'message': 'تم الحذف'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)



@login_required
def get_product_details(request, product_id):
    """الحصول على تفاصيل المنتج"""
    try:
        product = Product.objects.get(id=product_id)
        data = {
            'product_name': product.product_name,
            'purch_price': str(product.purch_price),
            'sale_price': str(product.sale_price),
            'current_stock': str(product.current_stock_quantity),
        }
        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({'error': _('المنتج غير موجود')}, status=404)




#================================================
#                  الباركود                    #
# ===============================================


@login_required
def barcode_create(request, product_slug):
    """إضافة باركود لمنتج"""
    product = get_object_or_404(Product, slug=product_slug)
    
    if request.method == 'POST':
        form = BarcodeForm(request.POST)
        if form.is_valid():
            try:
                barcode = form.save(commit=False)
                barcode.product = product
                
                if barcode.is_primary:
                    Barcode.objects.filter(product=product, is_primary=True).update(is_primary=False)
                
                barcode.save()
                messages.success(request, _('تم إضافة الباركود بنجاح'))
                return redirect('invoice:product_detail', slug=product.slug)
                
            except IntegrityError:
                messages.error(request, _('هذا الباركود موجود مسبقاً'))
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء إضافة الباركود: {str(e)}')
        else:
            messages.error(request, _('بيانات غير صحيحة. يرجى التصحيح والمحاولة مرة أخرى.'))
    else:
        form = BarcodeForm(initial={'product': product, 'status': 'active'})
    
    return render(request, 'invoice/barcode_form.html', {
        'form': form,
        'product': product,
        'title': _('إضافة باركود للمنتج')
    })


@login_required
def barcode_manage(request, product_slug):
    """إدارة باركودات منتج"""
    product = get_object_or_404(Product, slug=product_slug)
    barcodes = product.barcodes.all()
    
    return render(request, 'invoice/barcode_manage.html', {
        'product': product,
        'barcodes': barcodes,
        'title': _('إدارة باركودات المنتج')
    })


@login_required
def barcode_delete(request, barcode_id):
    """حذف باركود"""
    barcode = get_object_or_404(Barcode, id=barcode_id)
    product_slug = barcode.product.slug
    
    if request.method == 'POST':
        try:
            barcode.delete()
            messages.success(request, _('تم حذف الباركود بنجاح'))
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف الباركود: {str(e)}')
    
    return redirect('invoice:product_detail', slug=product_slug)


#--------------

@login_required
def api_barcode_search(request, barcode):
    """API للبحث بالباركود"""
    try:
        barcode_obj = Barcode.objects.get(barcode_in=barcode)
        product = barcode_obj.product
        return JsonResponse({
            'product_id': product.id,
            'product_name': product.product_name,
            'purch_price': str(product.purch_price),
            'sale_price': str(product.sale_price),
            'current_stock': str(product.current_stock_quantity),
        })
    except Barcode.DoesNotExist:
        return JsonResponse({'error': 'الباركود غير موجود'}, status=404)






# ================ إدارة الصندوق ================

@login_required
def cash_dashboard(request):
    """عرض لوحة تحكم الصندوق"""
    total_in = CashTransaction.objects.aggregate(total=Sum('amount_in'))['total'] or Decimal('0.00')
    total_out = CashTransaction.objects.aggregate(total=Sum('amount_out'))['total'] or Decimal('0.00')
    current_balance = total_in - total_out

    recent_transactions = CashTransaction.objects.all().order_by('-transaction_date')[:10]

    today = timezone.now().date()
    today_in = CashTransaction.objects.filter(
        transaction_date__date=today
    ).aggregate(total=Sum('amount_in'))['total'] or Decimal('0.00')
    today_out = CashTransaction.objects.filter(
        transaction_date__date=today
    ).aggregate(total=Sum('amount_out'))['total'] or Decimal('0.00')

    context = {
        'title': 'لوحة تحكم الصندوق',
        'total_in': total_in,
        'total_out': total_out,
        'current_balance': current_balance,
        'today_in': today_in,
        'today_out': today_out,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'invoice/cashbox/cash_dashboard.html', context)


@login_required
def cash_transaction_list(request):
    """عرض قائمة حركات الصندوق"""
    
    transaction_type = request.GET.get('type', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    search_query = request.GET.get('q', '')

    if not start_date and not end_date:
        today = timezone.now().date()
        start_date = today.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')

    transactions_qs = CashTransaction.objects.all().order_by('-transaction_date')
    
    if transaction_type:
        transactions_qs = transactions_qs.filter(transaction_type=transaction_type)
    
    if start_date:
        transactions_qs = transactions_qs.filter(transaction_date__date__gte=start_date)
    
    if end_date:
        transactions_qs = transactions_qs.filter(transaction_date__date__lte=end_date)

    if search_query:
        transactions_qs = transactions_qs.filter(
            Q(notes__icontains=search_query) | Q(transaction_type__icontains=search_query)
        )

    if 'export' in request.GET and request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="cash_transactions.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'التاريخ', 'النوع', 'المبلغ الداخل', 
            'المبلغ الخارج', 'البيان', 'بواسطة'
        ])

        for trans in transactions_qs:
            writer.writerow([
                trans.transaction_date.strftime('%Y-%m-%d %H:%M:%S'),
                trans.get_transaction_type_display(),
                trans.amount_in,
                trans.amount_out,
                trans.notes,
                trans.created_by.username if trans.created_by else '-'
            ])
        return response

    paginator = Paginator(transactions_qs, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    total_in = transactions_qs.aggregate(total=Sum('amount_in'))['total'] or Decimal('0.00')
    total_out = transactions_qs.aggregate(total=Sum('amount_out'))['total'] or Decimal('0.00')
    net_total = total_in - total_out

    page_total_in = sum(item.amount_in for item in page_obj)
    page_total_out = sum(item.amount_out for item in page_obj)
    page_total_net = page_total_in - page_total_out

    overall_balance = CashTransaction.get_cash_balance()
    is_balance_negative = overall_balance < 0

    today = timezone.now().date()
    today_transactions = CashTransaction.objects.filter(transaction_date__date=today)
    today_in = today_transactions.aggregate(total=Sum('amount_in'))['total'] or Decimal('0.00')
    today_out = today_transactions.aggregate(total=Sum('amount_out'))['total'] or Decimal('0.00')
    today_net = today_in - today_out
    
    context = {
        'title': 'حركات الصندوق',
        'page_obj': page_obj,
        'total_in': total_in,
        'total_out': total_out,
        'net_total': net_total,
        'page_total_in': page_total_in,
        'page_total_out': page_total_out,
        'page_total_net': page_total_net,
        'overall_balance': overall_balance,
        'is_balance_negative': is_balance_negative,
        'today_in': today_in,
        'today_out': today_out,
        'today_net': today_net,
        'current_filter': {
            'type': transaction_type,
            'start_date': start_date,
            'end_date': end_date,
            'q': search_query,
        }
    }
    return render(request, 'invoice/cashbox/cash_transaction_list.html', context)


@login_required
def cash_transaction_create(request):
    """إنشاء حركة صندوق جديدة"""
    total_in = CashTransaction.objects.aggregate(total=Sum('amount_in'))['total'] or Decimal('0.00')
    total_out = CashTransaction.objects.aggregate(total=Sum('amount_out'))['total'] or Decimal('0.00')
    current_balance = total_in - total_out

    if request.method == 'POST':
        form = CashTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            transaction.transaction_date = timezone.now()
            if transaction.transaction_type in ['withdrawal', 'expense']:
                try:
                    cash_payment_method = Payment_method.objects.get(name='نقداً')
                    transaction.payment_method = cash_payment_method
                except Payment_method.DoesNotExist:
                    pass
            transaction.save()
            return redirect('invoice:cash_transaction_list')
    else:
        form = CashTransactionForm()
    
    context = {
        'title': 'إضافة حركة صندوق جديدة',
        'form': form,
        'current_balance': current_balance,
    }
    return render(request, 'invoice/cashbox/cash_transaction_create.html', context)


@login_required
def cash_transaction_detail(request, pk):
    """عرض تفاصيل حركة صندوق"""
    transaction = get_object_or_404(CashTransaction, pk=pk)
    
    context = {
        'title': 'تفاصيل حركة الصندوق',
        'transaction': transaction,
    }
    return render(request, 'invoice/cashbox/cash_transaction_detail.html', context)





@require_GET
def get_cash_balance(request):
    """جلب رصيد الصندوق الحالي"""
    try:
        balance = CashTransaction.get_cash_balance()
        return JsonResponse({'balance': str(balance)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




@csrf_exempt
@require_POST
def update_payment_method_cash(request, pk):
    """تحديث حالة is_cash في طريقة الدفع"""
    try:
        payment_method = get_object_or_404(Payment_method, pk=pk)
        data = json.loads(request.body)
        is_cash = data.get('is_cash', False)
        
        payment_method.is_cash = is_cash
        payment_method.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



@require_GET
def get_payment_method(request, pk):
    """جلب بيانات طريقة الدفع"""
    try:
        payment_method = get_object_or_404(Payment_method, pk=pk)
        return JsonResponse({
            'id': payment_method.id,
            'name': payment_method.name,
            'is_cash': payment_method.is_cash
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)


#================================================
#             دول مساعدة عامة                  #
# ===============================================

@require_GET
def convert_amount_to_words_api(request):
    """API لتحويل المبلغ إلى كلمات"""
    from num2words import num2words
    amount = request.GET.get('amount', '0')
    currency_id = request.GET.get('currency_id', '')
    
    try:
        amount_decimal = Decimal(amount)
        if amount_decimal <= Decimal('0'):
            return JsonResponse({
                'success': False,
                'error': 'المبلغ يجب أن يكون أكبر من صفر'
            })
        
        currency_data = {
            'code': 'SYP',
            'symbol': 'ل.س',
            'name_ar': 'ليرة سورية',
            'singular': 'ليرة سورية',
            'dual': 'ليرتان سوريتان',
            'plural': 'ليرات سورية',
            'fraction': 'قرش',
            'fraction_dual': 'قرشان',
            'fraction_plural': 'قروش',
            'decimals': 2
        }
        
        if currency_id:
            try:
                currency = Currency.objects.get(id=currency_id)
                currency_data = {
                    'code': currency.code,
                    'symbol': currency.symbol,
                    'name_ar': currency.name_ar,
                    'singular': currency.singular_ar,
                    'dual': currency.dual_ar,
                    'plural': currency.plural_ar,
                    'fraction': currency.fraction_name_ar,
                    'fraction_dual': currency.fraction_dual_ar,
                    'fraction_plural': currency.fraction_plural_ar,
                    'decimals': currency.decimals
                }
            except Currency.DoesNotExist:
                logger.warning(f"العملة غير موجودة: {currency_id}")
        
        amount_float = float(amount_decimal)
        integer_part = int(amount_float)
        fractional_part = int(round((amount_float - integer_part) * (10 ** currency_data['decimals'])))
        
        integer_words = num2words(integer_part, lang='ar')
        fraction_words = num2words(fractional_part, lang='ar') if fractional_part > 0 else ''
        
        def clean_arabic_text(text):
            corrections = {
                'مئة': 'مائة',
                'مئتان': 'مئتان',
                'مئتين': 'مئتين',
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
                'عشرة': 'عشرة'
            }
            
            for wrong, correct in corrections.items():
                text = text.replace(wrong, correct)
            
            return text
        
        integer_words = clean_arabic_text(integer_words)
        
        if integer_part == 0:
            currency_word = ""
        elif integer_part == 1:
            currency_word = currency_data['singular']
        elif integer_part == 2:
            currency_word = currency_data['dual']
        elif integer_part <= 10:
            currency_word = currency_data['singular']
        else:
            currency_word = currency_data['plural']
        
        result_parts = []
        if integer_words and currency_word:
            result_parts.append(f"{integer_words} {currency_word}")
        elif integer_words:
            result_parts.append(integer_words)
        
        if fractional_part > 0 and fraction_words:
            fraction_words = clean_arabic_text(fraction_words)
            
            if fractional_part == 1:
                fraction_currency = currency_data['fraction']
            elif fractional_part == 2:
                fraction_currency = currency_data['fraction_dual']
            elif fractional_part <= 10:
                fraction_currency = currency_data['fraction']
            else:
                fraction_currency = currency_data['fraction_plural']
            
            if fraction_words and fraction_currency:
                result_parts.append(f"{fraction_words} {fraction_currency}")
        
        if not result_parts:
            result = "صفر"
        else:
            result = " و".join(result_parts)
        
        result += " فقط لا غير"
        
        return JsonResponse({
            'success': True,
            'amount_in_words': result,
            'amount_numeric': f"{amount_float:,.2f}",
            'currency': currency_data,
            'parts': {
                'integer': integer_part,
                'fraction': fractional_part,
                'integer_words': integer_words,
                'fraction_words': fraction_words
            }
        })
        
    except Exception as e:
        logger.error(f"خطأ في تحويل المبلغ إلى كلمات: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f"حدث خطأ في التحويل: {str(e)}"
        })

#== FOR WHAT ==
@require_GET
def get_current_amount_in_words(request):
    """API للحصول على المبلغ الحالي للفاتورة مكتوباً"""
    from num2words import num2words
    
    purchase_id = request.GET.get('purchase_id')
    amount = request.GET.get('amount')
    currency_id = request.GET.get('currency_id')
    
    try:
        if purchase_id:
            purchase = Purch.objects.get(id=purchase_id)
            amount_in_words = purchase.get_total_in_words()
            amount_numeric = purchase.purch_final_total
            currency_data = purchase.get_currency_info() if purchase.purch_currency else {
                'code': 'SYP',
                'symbol': 'ل.س',
                'name_ar': 'ليرة سورية'
            }
        elif amount:
            amount_decimal = Decimal(amount)
            currency_info = {}
            
            if currency_id:
                try:
                    currency = Currency.objects.get(id=currency_id)
                    currency_info = {
                        'code': currency.code,
                        'symbol': currency.symbol,
                        'name_ar': currency.name_ar
                    }
                except Currency.DoesNotExist:
                    currency_info = {
                        'code': 'SYP',
                        'symbol': 'ل.س',
                        'name_ar': 'ليرة سورية'
                    }
            
            try:
                if currency_id:
                    currency = Currency.objects.get(id=currency_id)
                    currency_info = {
                        'singular': currency.singular_ar,
                        'dual': currency.dual_ar,
                        'plural': currency.plural_ar,
                        'fraction': currency.fraction_name_ar,
                        'fraction_dual': currency.fraction_dual_ar,
                        'fraction_plural': currency.fraction_plural_ar,
                        'decimals': currency.decimals
                    }
                else:
                    currency_info = {
                        'singular': 'ليرة سورية',
                        'dual': 'ليرتان سوريتان',
                        'plural': 'ليرات سورية',
                        'fraction': 'قرش',
                        'fraction_dual': 'قرشان',
                        'fraction_plural': 'قروش',
                        'decimals': 2
                    }
                
                amount_float = float(amount_decimal)
                integer_part = int(amount_float)
                fractional_part = int(round((amount_float - integer_part) * (10 ** currency_info['decimals'])))
                
                integer_words = num2words(integer_part, lang='ar')
                integer_words = integer_words.replace('مئة', 'مائة')
                
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
                    fraction_words = fraction_words.replace('مئة', 'مائة')
                    
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
                amount_in_words = result
                
            except Exception as e:
                logger.error(f"خطأ في التحويل المباشر: {e}")
                amount_in_words = f"{amount} فقط لا غير"
            
            amount_numeric = amount_decimal
            currency_data = currency_info
        else:
            return JsonResponse({
                'success': False,
                'error': 'يجب تقديم purchase_id أو amount'
            })
        
        return JsonResponse({
            'success': True,
            'amount_in_words': amount_in_words,
            'amount_numeric': f"{amount_numeric:,.2f}",
            'currency': currency_data
        })
        
    except Purch.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'الفاتورة غير موجودة'
        })
    except Exception as e:
        logger.error(f"خطأ في جلب المبلغ المكتوب: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })




#================================================
#               دوال البحث (APIs)              #
# ===============================================


@require_GET
@login_required
def search_suppliers(request):
    """بحث عن الموردين للإكمال التلقائي (مُحسَّن لجلب بيانات Profile)"""
    query = request.GET.get('q', '')
    suppliers = []
    
    if query:
        # --- التعديل الرئيسي هنا ---
        # 1. نستخدم select_related لجلب بيانات المرتبطة (Profile) بكفاءة في استعلام واحد.
        # 2. هذا يمنع حدوث مشكلة N+1 queries ويحسن الأداء بشكل كبير.
        supplier_users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).select_related('profile').distinct()[:10]
        
        for user in supplier_users:
            # --- التعديل الثاني هنا ---
            # نحاول الوصول إلى بيانات الملف الشخصي (Profile) بأمان.
            # hasattr() تتحقق مما إذا كان الكائن 'user' يحتوي على علاقة 'profile'.
            # هذا يمنع حدوث خطأ DoesNotExist إذا كان مستخدم بدون ملف شخصي.
            if hasattr(user, 'profile'):
                profile = user.profile
                phone = profile.phone_number or ''
                address = profile.address or ''
            else:
                # إذا لم يكن هناك ملف شخصي، نستخدم قيم فارغة.
                phone = ''
                address = ''
            
            suppliers.append({
                'id': user.id,
                'text': f"{user.get_full_name() or user.username}",
                # نستخدم القيم التي حصلنا عليها من Profile
                'phone': phone,
                'address': address,
            })
    
    # لم نتغير في شيء هنا، الـ JSON يبقى بنفس الشكل
    return JsonResponse({'results': suppliers})



@require_GET
@login_required
def search_products(request):
    """بحث عن المنتجات للإكمال التلقائي"""
    query = request.GET.get('q', '')
    products = []
    
    if query:
        try:
            product_results = Product.objects.filter(
                Q(product_name__icontains=query) |
                Q(product_description__icontains=query)
            ).distinct()[:10]
            
            for product in product_results:
                purchase_price = getattr(product, 'purch_price', '0.00')
                price = getattr(product, 'retail_price', '0.00')
                final_price = purchase_price or price or '0.00'
                
                image_url = None
                if product.product_image:
                    image_url = product.product_image.url
                
                products.append({
                    'id': product.id,
                    'text': product.product_name,
                    'price': str(final_price),
                    'image_url': image_url
                })
                
        except Exception as e:
            logger.error(f"Error in product search: {e}")
            try:
                product_results = Product.objects.filter(
                    Q(product_name__icontains=query)
                )[:10]
                
                for product in product_results:
                    purchase_price = getattr(product, 'purch_price', '0.00')
                    price = getattr(product, 'retail_price', '0.00')
                    final_price = purchase_price or price or '0.00'
                    
                    image_url = None
                    if product.product_image:
                        image_url = product.product_image.url
                    
                    products.append({
                        'id': product.id,
                        'text': product.product_name,
                        'price': str(final_price),
                        'image_url': image_url
                    })
            except Exception as e2:
                logger.error(f"Error in fallback search: {e2}")
                products = []
    
    return JsonResponse({'results': products})



#================================================
#        المبيعات 
# ===============================================


@login_required
def sale_create(request):
    """إنشاء فاتورة بيع جديدة مع منطق التحقق المحسّن."""
    
    if request.method == 'POST':
        form = SaleForm(request.POST, request.FILES)
        formset = SaleItemFormSet(request.POST, request.FILES, prefix='items')
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # حفظ الفاتورة الرئيسية
                    sale = form.save(commit=False)
                    sale.created_by = request.user
                    
                    if not sale.uniqueId:
                        last_invoice = Sale.objects.order_by('-_last_invoice_number').first()
                        last_number = last_invoice._last_invoice_number if last_invoice else 0
                        new_number = last_number + 1
                        
                        sale._last_invoice_number = new_number
                        sale.uniqueId = f"S{new_number:04d}"
                        
                    if not sale.slug:
                        sale.slug = slugify(f"sale-{sale.uniqueId}")
                    
                    sale.save()

                    # حفظ بنود الفاتورة
                    instances = formset.save(commit=False)
                    
                    for i, instance in enumerate(instances):
                        instance.sale = sale
                        
                        # التأكد من ربط المنتج
                        product_id_from_form = request.POST.get(f'items-{i}-product')
                        product_search_value = request.POST.get(f'items-{i}-product_search', '')
                        
                        if not instance.product and product_id_from_form and product_id_from_form != '':
                            try:
                                product = Product.objects.get(id=product_id_from_form)
                                instance.product = product
                            except Product.DoesNotExist:
                                pass
                        
                        if not instance.product and product_search_value and product_search_value != "مادة غير محددة":
                            try:
                                product = Product.objects.get(product_name=product_search_value)
                                instance.product = product
                            except (Product.DoesNotExist, Product.MultipleObjectsReturned):
                                product = Product.objects.filter(product_name=product_search_value).first()
                                instance.product = product
                        
                        if not instance.item_name and instance.product:
                            instance.item_name = instance.product.product_name
                        elif not instance.item_name:
                            instance.item_name = product_search_value if product_search_value else "مادة غير محددة"
                        
                        # منطق الصور
                        image_field_name = f'items-{i}-sale_item_image'
                        image_url = request.POST.get(f'items-{i}-product_image_url', '')
                        is_auto_image = request.POST.get(f'items-{i}-is_auto_image') == 'true'
                        is_manual_upload = request.POST.get(f'items-{i}-manual_image_upload') == 'true'
                        
                        if image_field_name in request.FILES:
                            pass
                        elif image_url and is_auto_image and not is_manual_upload:
                            try:
                                response = requests.get(image_url, timeout=10)
                                if response.status_code == 200:
                                    img_temp = NamedTemporaryFile(delete=True)
                                    img_temp.write(response.content)
                                    img_temp.flush()
                                    
                                    filename = os.path.basename(image_url)
                                    if not filename or '.' not in filename:
                                        filename = f"product_{instance.product_id if instance.product else 'auto'}.jpg"
                                    
                                    instance.sale_item_image.save(filename, File(img_temp), save=False)
                            except Exception as e:
                                logger.error(f"خطأ في تحميل الصورة التلقائية: {e}")
                        
                        # === منطق الكميات والباركودات ===
                        qty_sold_with_barcode = Decimal('0.00')
                        qty_sold_without_barcode = Decimal('0.00')
                        
                        if instance.product:
                            product = instance.product
                            sale_type = request.POST.get(f'items-{i}-sale_type', 'barcode')
                            
                            # قراءة الباركودات المرسلة
                            barcodes_key = f'item_{i}_barcodes'
                            submitted_barcodes = request.POST.getlist(barcodes_key)
                            valid_submitted_barcodes = [b.strip() for b in submitted_barcodes if b.strip()]
                            
                            # حساب الكميات
                            qty_sold_with_barcode = Decimal(str(len(valid_submitted_barcodes)))
                            
                            # قراءة الكمية المدخلة يدوياً (إن وجدت)
                            qty_input_value = request.POST.get(f'items-{i}-sold_quantity', '0')
                            try:
                                manual_qty = Decimal(qty_input_value)
                            except:
                                manual_qty = Decimal('0.00')
                            
                            # تحديد الكمية بدون باركود
                            # إذا كانت الكمية اليدوية أكبر من عدد الباركودات، فإن الفرق هو كمية بدون باركود
                            if manual_qty > qty_sold_with_barcode:
                                qty_sold_without_barcode = manual_qty - qty_sold_with_barcode
                            else:
                                # إذا لم يدخل كمية يدوياً أو كانت أقل، نعتبره يبيع بالباركود فقط
                                # أو نأخذ الكمية اليدوية كقيمة أساسية إذا لم يكن هناك باركودات
                                if qty_sold_with_barcode == 0:
                                     qty_sold_without_barcode = manual_qty
                            
                            # تحديث حقول البند
                            instance.quantity_with_barcode = qty_sold_with_barcode
                            instance.quantity_without_barcode = qty_sold_without_barcode
                            instance.sold_quantity = qty_sold_with_barcode + qty_sold_without_barcode
                            
                            # التحقق من المخزون
                            total_stock = product.current_stock_quantity
                            available_barcodes_count = Barcode.objects.filter(product=product, status='active').count()
                            non_barcoded_stock = max(Decimal('0.00'), total_stock - Decimal(str(available_barcodes_count)))
                            
                            errors = []
                            if instance.sold_quantity > total_stock:
                                errors.append(f"الكمية المطلوبة ({instance.sold_quantity}) تتجاوز المخزون ({total_stock})")
                            
                            if qty_sold_with_barcode > available_barcodes_count:
                                errors.append(f"عدد الباركودات ({qty_sold_with_barcode}) يتجاوز المتاح ({available_barcodes_count})")
                            
                            if qty_sold_without_barcode > non_barcoded_stock:
                                errors.append(f"الكمية بدون باركود ({qty_sold_without_barcode}) تتجاوز المخزون غير المباركود ({non_barcoded_stock})")
                            
                            for barcode_value in valid_submitted_barcodes:
                                if not Barcode.objects.filter(barcode_in=barcode_value, product=product, status='active').exists():
                                    errors.append(f"الباركود '{barcode_value}' غير متاح")
                            
                            if errors:
                                raise ValidationError(f"خطأ في بند '{product.product_name}': " + " | ".join(errors))
                        
                        instance.save()
                        
                        # تحديث المخزون (باستخدام الكمية النهائية المحسوبة)
                        if instance.product:
                            instance.update_product_stock()
                        
                        # ربط الباركودات
                        for barcode_value in valid_submitted_barcodes:
                            barcode_value = barcode_value.strip()
                            if barcode_value:
                                try:
                                    barcode_obj = Barcode.objects.get(
                                        barcode_in=barcode_value, 
                                        product=instance.product, 
                                        status='active'
                                    )
                                    
                                    SaleItemBarcode.objects.create(
                                        sale_item=instance,
                                        barcode=barcode_obj,
                                        quantity_used=Decimal('1.00'),
                                        barcode_status='active'
                                    )
                                    # تحديث حالة الباركود
                                    barcode_obj.status = 'sold'
                                    barcode_obj.save()
                                    
                                except Barcode.DoesNotExist:
                                    # تم التحقق مسبقاً، هذا مجرد احتياط
                                    pass
                                except Exception as e:
                                    logger.error(f"خطأ في ربط الباركود {barcode_value}: {e}")
                    
                    # حذف البنود المحذوفة
                    for instance in formset.deleted_objects:
                        instance.item_barcodes.all().delete()
                        instance.delete()
                    
                    # حساب الإجماليات
                    sale.calculate_and_save_totals()

                    # التحقق من المبلغ المدفوع (باستخدام Decimal بشكل صحيح)
                    paid_amt = Decimal(str(request.POST.get('paid_amount', '0')))
                    if paid_amt > sale.sale_final_total:
                        raise ValidationError("المبلغ المدفوع لا يمكن أن يتجاوز الإجمالي النهائي للفاتورة")

                    # تحديث المبلغ المدفوع في الفاتورة
                    sale.paid_amount = paid_amt
                    sale.balance_due = sale.sale_final_total - sale.paid_amount
                    sale.is_paid = sale.balance_due <= 0
                    sale.save(update_fields=['paid_amount', 'balance_due', 'is_paid'])

                    # إنشاء حركة صندوق
                    if sale.paid_amount > 0 and sale.sale_payment_method and sale.sale_payment_method.is_cash:
                        sale.create_cash_transaction()
                    
                    messages.success(request, 'تم إنشاء فاتورة البيع بنجاح وتحديث المخزون')
                    return redirect('invoice:sale_detail', slug=sale.slug)
                    
            except ValidationError as e:
                messages.error(request, e.messages[0] if hasattr(e, 'messages') and e.messages else str(e))
            except Exception as e:
                logger.error(f"خطأ في إنشاء فاتورة البيع: {e}", exc_info=True)
                messages.error(request, f'حدث خطأ غير متوقع: {str(e)}')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء في النموذج.')
                
    else:
        form = SaleForm(initial={
            'sale_date': timezone.now().date(),
            'paid_amount': 0,
            'sale_tax_percentage': 0,
            'sale_discount': 0,
            'sale_addition': 0
        })
        formset = SaleItemFormSet(prefix='items', queryset=SaleItem.objects.none())
    
    products = Product.objects.all()
    
    return render(request, 'invoice/sale/sale_form.html', {
        'form': form,
        'formset': formset,
        'products': products,
        'title': 'إنشاء فاتورة بيع جديدة'
    })



#----------------

def handle_sale_cash_transaction(sale):
    from .models import CashTransaction
    existing = CashTransaction.objects.filter(sale_invoice=sale, transaction_type='sale_receipt').first()
    is_cash = sale.sale_payment_method and sale.sale_payment_method.is_cash
    if sale.paid_amount > 0 and is_cash:
        if existing:
            existing.amount_in = sale.paid_amount
            existing.save()
        else:
            CashTransaction.objects.create(
                transaction_date=timezone.now(),
                amount_in=sale.paid_amount,
                transaction_type='sale_receipt',
                payment_method=sale.sale_payment_method,
                sale_invoice=sale,
                notes=f"تحصيل فاتورة {sale.uniqueId}",
                created_by=sale.created_by
            )
    else:
        if existing:
            existing.delete()



#------------------



@login_required
def sale_detail(request, slug):
    """
    عرض تفاصيل فاتورة بيع محددة مع جميع البنود والباركودات المرتبطة
    """
    # جلب الفاتورة مع العلاقات المرتبطة لتقليل الاستعلامات
    sale = get_object_or_404(
        Sale.objects.select_related(
            'sale_customer',
            'sale_payment_method',
            'sale_currency',
            'sale_status',
            'sale_shipping_company',
            'created_by'
        ),
        slug=slug
    )
    
    # جلب جميع بنود الفاتورة مرتبة
    items = sale.saleitem_set.all().order_by('id')
    
    # تجهيز قائمة تحتوي على كل بند مع باركوداته
    items_with_barcodes = []
    for item in items:
        # جلب روابط الباركودات النشطة لهذا البند مع الباركود المرتبط
        barcode_links = item.item_barcodes.filter(
            barcode_status='active'
        ).select_related('barcode')
        
        # تحويلها إلى قائمة من القواميس البسيطة
        barcodes = [
            {
                'code': link.barcode.barcode_in,
                'status': link.barcode_status
            }
            for link in barcode_links
        ]
        
        items_with_barcodes.append({
            'item': item,
            'barcodes': barcodes
        })
    
    # إحصائيات سريعة (اختياري)
    total_items = items.count()
    total_quantity = sum(item.sold_quantity for item in items)
    
    context = {
        'sale': sale,
        'items_with_barcodes': items_with_barcodes,
        'total_items': total_items,
        'total_quantity': total_quantity,
        'title': f'تفاصيل فاتورة البيع {sale.uniqueId}'
    }
    
    return render(request, 'invoice/sale/sale_detail.html', context)


@login_required
def sale_edit(request, slug):
    """
    تعديل فاتورة بيع موجودة.
    تم تصحيح المنطق للسماح بتعديل الفاتورة التي تحتوي على باركودات مباعة (sold)
    باعتبارها "ممتلكة" بالفعل ولا تحتاج لفحص توفر جديد.
    """
    sale = get_object_or_404(Sale, slug=slug)
    
    # تعريف FormSet مخصص للتعديل (extra=0 لمنع ظهور صفوف فارغة غير مرغوبة)
    SaleItemEditFormSet = inlineformset_factory(
        Sale, 
        SaleItem, 
        form=SaleItemForm,
        extra=0,
        can_delete=True,
        can_order=False
    )
    
    if request.method == 'POST':
        form = SaleForm(request.POST, request.FILES, instance=sale)
        formset = SaleItemEditFormSet(request.POST, request.FILES, instance=sale, prefix='items')
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # 1. حفظ بيانات الفاتورة الرئيسية
                    updated_sale = form.save(commit=False)
                    updated_sale.save()
                    
                    # 2. معالجة البنود المحذوفة (من خلال checkbox الحذف في الفورم)
                    #注意: formset.deleted_forms يحتوي على البنود المحددة للحذف فقط
                    for form_del in formset.deleted_forms:
                        instance = form_del.instance
                        if instance.pk:
                            # إعادة الباركودات المرتبطة بهذا البند إلى حالة نشط (active)
                            for barcode_item in instance.item_barcodes.all():
                                barcode_obj = barcode_item.barcode
                                barcode_obj.status = 'active'
                                barcode_obj.save()
                                barcode_item.delete()
                            
                            # حذف البند (سيتم تحديث المخزون تلقائياً في signal أو delete method إذا كان مدعوماً)
                            # هنا نستدعي delete لتفعيل المنطق الموجود في модели SaleItem
                            instance.delete()
                    
                    # 3. حفظ البنود الجديدة والمعدلة
                    instances = formset.save(commit=False)
                    
                    for i, instance in enumerate(instances):
                        # ربط الفاتورة
                        instance.sale = updated_sale
                        
                        # --- الخطوة أ: جلب البيانات القديمة (لحساب فرق المخزون) ---
                        old_instance = None
                        old_quantity = Decimal('0.00')
                        old_product = None
                        
                        if instance.pk:
                            try:
                                old_instance = SaleItem.objects.get(pk=instance.pk)
                                old_quantity = old_instance.sold_quantity
                                old_product = old_instance.product
                            except SaleItem.DoesNotExist:
                                pass
                        
                        # --- الخطوة ب: معالجة المنتج والاسم ---
                        product_id_from_form = request.POST.get(f'items-{i}-product')
                        product_search_value = request.POST.get(f'items-{i}-product_search', '')
                        
                        # محاولة ربط المنتج إذا لم يكن مرتبطاً
                        if not instance.product and product_id_from_form:
                            try:
                                instance.product = Product.objects.get(id=product_id_from_form)
                            except Product.DoesNotExist:
                                pass
                        
                        if not instance.product and product_search_value and product_search_value != "مادة غير محددة":
                            instance.product = Product.objects.filter(product_name=product_search_value).first()
                        
                        # تعيين اسم المادة
                        if not instance.item_name:
                            if instance.product:
                                instance.item_name = instance.product.product_name
                            else:
                                instance.item_name = product_search_value if product_search_value else "مادة غير محددة"

                        # --- الخطوة ج: معالجة الكميات والباركودات ---
                        barcodes_key = f'item_{i}_barcodes'
                        submitted_barcodes = request.POST.getlist(barcodes_key)
                        # تنظيف القائمة (إزالة الفراغات)
                        valid_submitted_barcodes = [b.strip() for b in submitted_barcodes if b.strip()]
                        
                        # تحديد الباركودات الحالية للبند (من قاعدة البيانات)
                        current_item_barcodes_set = set()
                        if instance.pk:
                            current_item_barcodes_set = set(
                                SaleItemBarcode.objects.filter(sale_item_id=instance.pk)
                                .values_list('barcode__barcode_in', flat=True)
                            )
                        
                        # حساب الكميات
                        qty_with_barcode = Decimal(str(len(valid_submitted_barcodes)))
                        manual_qty = Decimal(request.POST.get(f'items-{i}-sold_quantity', '0') or '0')
                        
                        # منطق حساب الكمية بدون باركود
                        qty_without_barcode = Decimal('0.00')
                        if manual_qty > qty_with_barcode:
                            qty_without_barcode = manual_qty - qty_with_barcode
                        else:
                            # إذا كانت الكمية اليدوية أقل أو تساوي عدد الباركودات
                            # فالكمية الإجمالية هي عدد الباركودات
                            qty_without_barcode = Decimal('0.00')
                            if qty_with_barcode == 0 and manual_qty > 0:
                                # حالة خاصة: لا يوجد باركودات ولكن هناك كمية يدوية
                                qty_without_barcode = manual_qty
                        
                        instance.quantity_with_barcode = qty_with_barcode
                        instance.quantity_without_barcode = qty_without_barcode
                        instance.sold_quantity = qty_with_barcode + qty_without_barcode
                        
                        # --- الخطوة د: التحقق من المخزون والباركودات (المنطق المصحح) ---
                        if instance.product:
                            product = instance.product
                            submitted_set = set(valid_submitted_barcodes)
                            
                            # 1. الباركودات المطلوب إضافتها (جديدة)
                            barcodes_to_add = submitted_set - current_item_barcodes_set
                            
                            # 2. الباركودات المطلوب إزالتها (كانت موجودة وتم حذفها)
                            barcodes_to_remove = current_item_barcodes_set - submitted_set
                            
                            errors = []
                            
                            # التحقق من الباركودات الجديدة: يجب أن تكون نشطة (active) وتابعة لنفس المنتج
                            if barcodes_to_add:
                                # جلب الباركودات النشطة المطلوبة
                                available_new_barcodes = Barcode.objects.filter(
                                    barcode_in__in=barcodes_to_add,
                                    product=product,
                                    status='active'
                                )
                                
                                # التحقق: هل كل الباركودات الجديدة موجودة ونشطة؟
                                found_barcodes = set(available_new_barcodes.values_list('barcode_in', flat=True))
                                missing_or_invalid = barcodes_to_add - found_barcodes
                                
                                if missing_or_invalid:
                                    errors.append(
                                        f"الباركودات التالية غير متاحة أو لا تنتمي للمنتج: {', '.join(list(missing_or_invalid)[:5])}"
                                    )
                            
                            # التحقق من الكمية الإجمالية (للتأكد من عدم تجاوز المخزون الكلي)
                            # المخزون المتاح للحساب = المخزون الحالي + ما سنسترجعه من الباركودات المحذوفة
                            # (ببساطة: Logic يعتمد على فرق الكمية، ولكن للتحقق نستخدم المنطق التالي)
                            
                            # الكمية المطلوبة صافي = (الكمية الجديدة) - (الكمية القديمة)
                            # هذا معقد قليلاً مع الباركود، نعتمد على تحقق الباركودات أولاً
                            
                            if errors:
                                raise ValidationError(f"خطأ في بند '{product.product_name}': " + " | ".join(errors))
                        
                        # حفظ البند (SaleItem)
                        instance.save()
                        
                        # --- الخطوة هـ: تحديث المخزون ---
                        # نستخدم الدالة الموجودة في الموديل لتحديث المخزون بناءً على الفرق
                        if instance.product:
                            if old_instance and old_instance.product:
                                # تعديل: نمرر الكمية القديمة والمنتج القديم
                                instance.update_product_stock(old_quantity=old_quantity, old_product=old_instance.product)
                            else:
                                # إضافة جديدة
                                instance.update_product_stock()
                        
                        # --- الخطوة و: تحديث ربط الباركودات في قاعدة البيانات ---
                        
                        # 1. إزالة الباركودات التي لم تعد موجودة في القائمة المرسلة
                        if barcodes_to_remove:
                            for b_val in barcodes_to_remove:
                                try:
                                    barcode_obj = Barcode.objects.get(barcode_in=b_val, product=instance.product)
                                    # إعادة الحالة إلى نشط
                                    barcode_obj.status = 'active'
                                    barcode_obj.save()
                                    
                                    # حذف الربط
                                    SaleItemBarcode.objects.filter(sale_item=instance, barcode=barcode_obj).delete()
                                except Barcode.DoesNotExist:
                                    pass
                        
                        # 2. إضافة الباركودات الجديدة
                        if barcodes_to_add:
                            for b_val in barcodes_to_add:
                                try:
                                    barcode_obj = Barcode.objects.get(barcode_in=b_val, product=instance.product)
                                    SaleItemBarcode.objects.create(
                                        sale_item=instance,
                                        barcode=barcode_obj,
                                        quantity_used=Decimal('1.00'),
                                        barcode_status='active'
                                    )
                                    # تحديث حالة الباركود إلى مباع
                                    barcode_obj.status = 'sold'
                                    barcode_obj.save()
                                except Barcode.DoesNotExist:
                                    # تم التحقق منها سابقاً، لكن للتأكد
                                    logger.warning(f"Barcode {b_val} disappeared during save.")
                        
                        # تحديث صورة المنتج (اختياري - كما في الكود القديم)
                        # ... (يمكن إضافة كود تحميل الصورة هنا إذا لزم الأمر) ...
                    
                    # 4. تحديث الإجماليات المالية للفاتورة
                    updated_sale.calculate_and_save_totals()
                    
                    # 5. معالجة المبلغ المدفوع
                    paid_amt = Decimal(str(request.POST.get('paid_amount', '0')))
                    if paid_amt > updated_sale.sale_final_total:
                        raise ValidationError("المبلغ المدفوع لا يمكن أن يتجاوز الإجمالي النهائي للفاتورة")
                    
                    updated_sale.paid_amount = paid_amt
                    updated_sale.balance_due = updated_sale.sale_final_total - updated_sale.paid_amount
                    updated_sale.is_paid = updated_sale.balance_due <= 0
                    updated_sale.save(update_fields=['paid_amount', 'balance_due', 'is_paid'])
                    
                    # 6. إنشاء/تحديث حركة الصندوق
                    if updated_sale.paid_amount > 0 and updated_sale.sale_payment_method and updated_sale.sale_payment_method.is_cash:
                        updated_sale.create_cash_transaction()
                    else:
                        CashTransaction.objects.filter(sale_invoice=updated_sale, transaction_type='sale_receipt').delete()
                    
                    messages.success(request, 'تم تعديل فاتورة البيع بنجاح')
                    return redirect('invoice:sale_detail', slug=updated_sale.slug)
                    
            except ValidationError as e:
                msg = e.messages[0] if hasattr(e, 'messages') and e.messages else str(e)
                messages.error(request, msg)
            except Exception as e:
                logger.error(f"خطأ في تعديل فاتورة البيع: {e}", exc_info=True)
                messages.error(request, f'حدث خطأ غير متوقع: {str(e)}')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء في النموذج.')
    
    else:  # GET request
        form = SaleForm(instance=sale)
        formset = SaleItemEditFormSet(instance=sale, prefix='items')
    
    # تجهيز بيانات الباركودات للبنود الحالية (للاستخدام في JavaScript)
    barcodes_data = {}
    for item in sale.saleitem_set.all():
        barcodes_data[str(item.id)] = list(item.item_barcodes.values_list('barcode__barcode_in', flat=True))
    
    context = {
        'form': form,
        'formset': formset,
        'sale': sale,
        'barcodes_data': barcodes_data,
        'products': Product.objects.all(),
        'title': f'تعديل فاتورة بيع: {sale.uniqueId}',
    }
    return render(request, 'invoice/sale/sale_form_edit.html', context)




@login_required
def sale_list(request):
    """عرض قائمة فواتير البيع"""
    sales = Sale.objects.all().select_related('sale_customer', 'sale_status').prefetch_related('saleitem_set')
    
    # البحث والفلترة
    query = request.GET.get('q', '')
    status_id = request.GET.get('status', '')
    
    if query:
        sales = sales.filter(uniqueId__icontains=query) | sales.filter(sale_invoice_number__icontains=query)
    
    if status_id:
        sales = sales.filter(sale_status_id=status_id)
        
    context = {
        'sales': sales,
        'title': 'قائمة فواتير البيع',
    }
    return render(request, 'invoice/sale/sale_list.html', context)


#--seale return---






@login_required
def sale_return_create(request, sale_slug):
    original_sale = get_object_or_404(Sale, slug=sale_slug)
    
    # التحقق مما إذا كانت الفاتورة الأصلية مدفوعة نقداً (للعرض فقط)
    is_cash_payment = False
    payment_method_name = ""
    if original_sale.sale_payment_method:
        payment_method_name = original_sale.sale_payment_method.name
        if payment_method_name == 'نقداً' or payment_method_name == 'نقدا':
            is_cash_payment = True

    # 1. حساب الكميات المرتجعة سابقاً وجلب البيانات
    returned_items_data = {}
    for item in original_sale.saleitem_set.all():
        returned_qty = SaleReturnItem.objects.filter(
            original_sale_item=item,
            sale_return__isnull=False
        ).aggregate(total=Sum('returned_quantity'))['total'] or Decimal('0.00')
        
        returned_items_data[item.id] = {
            'returned': returned_qty,
            'sold': item.sold_quantity
        }
    
    SaleReturnItemFormSet = inlineformset_factory(
        SaleReturn, SaleReturnItem, form=SaleReturnItemForm,
        extra=original_sale.saleitem_set.count(), can_delete=True
    )

    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data['original_sale'] = original_sale.id
        
        form = SaleReturnForm(post_data, request.FILES)
        formset = SaleReturnItemFormSet(request.POST, request.FILES, prefix='items')
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    sale_return = form.save(commit=False)
                    sale_return.original_sale = original_sale
                    sale_return.created_by = request.user
                    
                    # تعيين العملة
                    if not sale_return.return_currency:
                        sale_return.return_currency = getattr(original_sale, 'sale_currency', None)
                    
                    # تعيين طريقة الدفع (افتراضياً نقداً إذا لم يتم اختيارها)
                    if not sale_return.return_payment_method:
                        try:
                            # نحاول الجلب بأي طريقة كتابة
                            cash_method = Payment_method.objects.filter(name__in=['نقداً', 'نقدا']).first()
                            if not cash_method:
                                cash_method = Payment_method.objects.create(name='نقداً')
                            sale_return.return_payment_method = cash_method
                        except Exception:
                            pass
                    
                    sale_return.save()
                    
                    saved_items_count = 0
                    
                    for item_form in formset:
                        if item_form.cleaned_data.get('DELETE') or not item_form.cleaned_data.get('original_sale_item'):
                            continue
                            
                        item_instance = item_form.save(commit=False)
                        item_instance.sale_return = sale_return
                        original_item = item_form.cleaned_data.get('original_sale_item')
                        
                        data = returned_items_data.get(original_item.id, {'returned': 0, 'sold': 0})
                        available = data['sold'] - data['returned']
                        
                        if item_instance.returned_quantity > available:
                            raise ValueError(f"الكمية المرتجعة لـ {original_item.item_name} تتجاوز المتاح ({available}).")
                        
                        item_instance.product = original_item.product
                        item_instance.item_name = original_item.item_name
                        item_instance.unit_price = original_item.unit_price
                        item_instance.save()
                        saved_items_count += 1
                        
                        item_instance.restore_product_stock()
                        
                        # حفظ الباركودات وتغيير حالتها إلى active
                        form_index = item_form.prefix.split('-')[1] if '-' in item_form.prefix else None
                        if form_index:
                            barcode_key = f'barcodes_{form_index}'
                            raw_ids = request.POST.getlist(barcode_key)
                            ids_list = []
                            for val in raw_ids:
                                ids_list.extend(val.split(','))
                            
                            for b_id in ids_list:
                                b_id = b_id.strip()
                                if b_id:
                                    try:
                                        barcode_link = SaleItemBarcode.objects.get(
                                            barcode_id=int(b_id), 
                                            sale_item=original_item
                                        )
                                        SaleReturnItemBarcode.objects.create(
                                            sale_return_item=item_instance, 
                                            barcode=barcode_link.barcode,
                                            quantity_used=Decimal('1.00'), 
                                            barcode_status='returned'
                                        )
                                    except Exception as e:
                                        logger.warning(f"Barcode save error: {e}")

                    if saved_items_count == 0:
                        sale_return.delete()
                        messages.warning(request, 'لم يتم تحديد أي كميات للاسترجاع.')
                        return redirect('invoice:sale_detail', slug=original_sale.slug)
                    
                    # حساب الإجماليات
                    sale_return.calculate_and_save_totals()
                    
                    # التأكد من أن المبلغ لا يتجاوز الإجمالي
                    if sale_return.paid_amount > sale_return.return_final_total:
                         raise ValueError(f"المبلغ المصروف ({sale_return.paid_amount}) أكبر من إجمالي المرتجع ({sale_return.return_final_total})")
                    
                    sale_return.save()
                    
                    # === [منطق تسجيل الصندوق المعدل] ===
                    # نستخدم طريقة دفع المرتجع وليس الفاتورة الأصلية
                    is_cash_method = False
                    if sale_return.return_payment_method:
                        # نقارن بإزالة المسافات والهمزات لتجنب مشاكل الكتابة
                        method_name = sale_return.return_payment_method.name.strip()
                        if method_name in ['نقداً', 'نقدا', 'Cash']:
                            is_cash_method = True
                    
                    # تسجيل أو تحديث حركة الصندوق
                    if sale_return.paid_amount > 0 and is_cash_method:
                        CashTransaction.objects.update_or_create(
                            sale_return=sale_return,
                            defaults={
                                'transaction_date': timezone.now(),
                                'transaction_type': 'sale_return',
                                'amount_out': sale_return.paid_amount,
                                'amount_in': Decimal('0.00'),
                                'payment_method': sale_return.return_payment_method,
                                'notes': f"صرف نقدي للعميل - مرتجع رقم {sale_return.uniqueId}",
                                'created_by': request.user,
                                'sale_invoice': sale_return.original_sale
                            }
                        )
                        logger.info(f"✅ تم تسجيل حركة صندوق لمرتجع المبيعات: {sale_return.paid_amount}")
                    else:
                        # إذا لم يكن نقدياً أو المبلغ صفر، نحذف أي حركة سابقة
                        CashTransaction.objects.filter(sale_return=sale_return).delete()
                    
                    messages.success(request, f'تم إنشاء مرتجع البيع {sale_return.uniqueId} بنجاح')
                    return redirect('invoice:sale_detail', slug=original_sale.slug)
                    
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
                messages.error(request, f"حدث خطأ: {str(e)}")
            
    else: # GET
        form = SaleReturnForm(initial={
            'return_date': timezone.now().date(),
            'return_currency': getattr(original_sale, 'sale_currency', None),
            'original_sale': original_sale.id,
        })
        
        initial_data = []
        for item in original_sale.saleitem_set.all():
            initial_data.append({
                'original_sale_item': item, 'product': item.product,
                'item_name': item.item_name, 'unit_price': item.unit_price,
                'returned_quantity': 0,
            })
        formset = SaleReturnItemFormSet(prefix='items', initial=initial_data)

    # تجهيز JSON للواجهة الأمامية
    items_json = []
    for sale_item in original_sale.saleitem_set.all().select_related('product'):
        data = returned_items_data.get(sale_item.id, {'returned': 0, 'sold': 0})
        available = data['sold'] - data['returned']
        
        barcodes_list = []
        if sale_item.product:
            item_barcodes = sale_item.item_barcodes.filter(barcode_status='active')
            for ib in item_barcodes:
                barcodes_list.append({
                    'id': ib.barcode.id, 
                    'barcode_in': ib.barcode.barcode_in
                })

        image_url = None
        if sale_item.product and sale_item.product.product_image:
            image_url = sale_item.product.product_image.url

        items_json.append({
            'id': sale_item.id,
            'product_id': sale_item.product.id if sale_item.product else None,
            'product_name': sale_item.item_name,
            'unit_price': float(sale_item.unit_price),
            'sold_quantity': float(data['sold']),
            'returned_quantity': float(data['returned']),
            'available_to_return': float(available),
            'item_image': image_url,
            'barcodes': barcodes_list
        })

    context = {
        'form': form, 
        'formset': formset, 
        'original_sale': original_sale,
        'title': f'إنشاء مرتجع لفاتورة بيع {original_sale.uniqueId}',
        'items_json': json.dumps(items_json),
        'is_cash_payment': is_cash_payment,
        'payment_method_name': payment_method_name,
    }
    return render(request, 'invoice/sale/sale_return_form.html', context)


@login_required
def sale_return_detail(request, slug):
    """عرض تفاصيل مرتجع المبيعات"""
    try:
        sale_return = SaleReturn.objects.prefetch_related(
            'salereturnitem_set__product',
            'salereturnitem_set__return_item_barcodes__barcode'
        ).get(slug=slug)
    except SaleReturn.DoesNotExist:
        messages.error(request, 'مرتجع المبيعات غير موجود')
        return redirect('invoice:sale_return_list')
    
    return render(request, 'invoice/sale_return/sale_return_detail.html', {
        'sale_return': sale_return,
        'original_sale': sale_return.original_sale,
    })


@login_required
def sale_return_update(request, slug):
    """تعديل مرتجع المبيعات"""
    try:
        sale_return = SaleReturn.objects.get(slug=slug)
    except SaleReturn.DoesNotExist:
        messages.error(request, 'مرتجع المبيعات غير موجود')
        return redirect('invoice:sale_return_list')
    
    if request.method == 'POST':
        form = SaleReturnForm(request.POST, request.FILES, instance=sale_return)
        formset = SaleReturnItemFormSet(request.POST, request.FILES, prefix='items', instance=sale_return)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    sale_return = form.save()
                    formset.save()
                    
                    # إعادة حساب الإجماليات
                    sale_return.calculate_and_save_totals()
                    
                    messages.success(request, f'تم تحديث مرتجع المبيعات {sale_return.uniqueId} بنجاح')
                    return redirect('invoice:sale_return_detail', slug=sale_return.slug)
                    
            except Exception as e:
                logger.error(f"خطأ في تحديث مرتجع المبيعات: {e}", exc_info=True)
                messages.error(request, f'حدث خطأ: {str(e)}')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء في النموذج')
    else:
        form = SaleReturnForm(instance=sale_return)
        formset = SaleReturnItemFormSet(prefix='items', instance=sale_return)
    
    return render(request, 'invoice/sale/sale_return_form.html', {
        'form': form,
        'formset': formset,
        'original_sale': sale_return.original_sale,
        'sale_return': sale_return,
        'title': f'تعديل مرتجع {sale_return.uniqueId}'
    })


@login_required
def sale_return_delete(request, slug):
    """حذف مرتجع المبيعات"""
    try:
        sale_return = SaleReturn.objects.get(slug=slug)
    except SaleReturn.DoesNotExist:
        messages.error(request, 'مرتجع المبيعات غير موجود')
        return redirect('invoice:sale_return_list')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # إعادة الباركودات إلى حالتها السابقة (اختياري حسب المنطق)
                for item in sale_return.salereturnitem_set.all():
                    for barcode_item in item.return_item_barcodes.all():
                        barcode = barcode_item.barcode
                        # إعادة الباركود إلى حالة البيع (لأننا نحذف المرتجع)
                        barcode.status = 'sold'
                        barcode.save()
                    
                    # سحب الكمية من المخزون مرة أخرى (عكس عملية الإرجاع)
                    if item.product:
                        item.product.current_stock_quantity -= item.returned_quantity
                        item.product.save()
                
                sale_return.delete()
                messages.success(request, f'تم حذف مرتجع المبيعات {sale_return.uniqueId} بنجاح')
                
        except Exception as e:
            logger.error(f"خطأ في حذف مرتجع المبيعات: {e}", exc_info=True)
            messages.error(request, f'حدث خطأ أثناء الحذف: {str(e)}')
            
        return redirect('invoice:sale_return_list')
    
    return render(request, 'invoice/sale_return/sale_return_confirm_delete.html', {
        'sale_return': sale_return
    })


@login_required
def sale_return_list(request):
    """عرض قائمة مرتجعات المبيعات"""
    sale_returns = SaleReturn.objects.select_related(
        'original_sale', 'created_by'
    ).prefetch_related('salereturnitem_set').all()
    
    # فلترة حسب التاريخ إذا وجد
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        sale_returns = sale_returns.filter(return_date__gte=start_date)
    if end_date:
        sale_returns = sale_returns.filter(return_date__lte=end_date)
    
    # بحث
    search_query = request.GET.get('q')
    if search_query:
        sale_returns = sale_returns.filter(
            Q(uniqueId__icontains=search_query) |
            Q(original_sale__uniqueId__icontains=search_query) |
            Q(original_sale__sale_customer__username__icontains=search_query)
        )
    
    paginator = Paginator(sale_returns, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'invoice/sale/sale_return_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
    })



@login_required
def get_sale_items_for_return(request, sale_id):
    """API لجلب بنود الفاتورة الأصلية مع إمكانية تحديد الكميات القابلة للإرجاع"""
    try:
        sale = Sale.objects.get(id=sale_id)
        
        # جلب جميع بنود الفاتورة مع معلومات الإرجاع السابقة
        items = []
        for item in sale.saleitem_set.all():
            # حساب الكمية التي تم إرجاعها سابقاً لهذا البند
            returned_qty = SaleReturnItem.objects.filter(
                original_sale_item=item,
                sale_return__isnull=False
            ).aggregate(total=Sum('returned_quantity'))['total'] or Decimal('0.00')
            
            # الكمية القابلة للإرجاع = الكمية المباعة - الكمية المرتجعة سابقاً
            available_to_return = max(Decimal('0.00'), item.sold_quantity - returned_qty)
            
            # جلب الباركودات الخاصة بهذا البند
            barcodes = []
            if item.product:
                for ib in item.item_barcodes.filter(barcode_status='active'):
                    barcodes.append({
                        'id': ib.barcode.id,
                        'barcode_in': ib.barcode.barcode_in,
                        'status': ib.barcode.status
                    })
            
            items.append({
                'id': item.id,
                'product_id': item.product.id if item.product else None,
                'product_name': item.item_name,
                'sold_quantity': float(item.sold_quantity),
                'returned_quantity': float(returned_qty),
                'available_to_return': float(available_to_return),
                'unit_price': float(item.unit_price),
                'has_barcode': len(barcodes) > 0,
                'barcodes': barcodes
            })
        
        return JsonResponse({
            'success': True,
            'sale_number': sale.uniqueId,
            'items': items,
            'currency': {
                'id': sale.sale_currency.id if sale.sale_currency else None,
                'name': sale.sale_currency.name_ar if sale.sale_currency else 'ليرة سورية'
            }
        })
        
    except Sale.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'الفاتورة غير موجودة'}, status=404)
    except Exception as e:
        logger.error(f"خطأ في جلب بنود الفاتورة للإرجاع: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def check_barcode_for_return(request, product_id):
    """API للتحقق من صحة الباركود للإرجاع"""
    try:
        product = Product.objects.get(id=product_id)
        barcode_value = request.GET.get('barcode')
        sale_item_id = request.GET.get('sale_item_id')
        
        if not barcode_value:
            return JsonResponse({'success': False, 'error': 'لم يتم إرسال قيمة الباركود'})
        
        # البحث عن الباركود
        try:
            barcode_obj = Barcode.objects.get(barcode_in=barcode_value, product=product)
        except Barcode.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': 'الباركود غير موجود لهذا المنتج'
            })
        
        # التحقق من أن هذا الباركود كان مباعاً في هذه الفاتورة
        if barcode_obj.status != 'sold':
            return JsonResponse({
                'success': False,
                'error': f'هذا الباركود غير مباع (حالته: {barcode_obj.get_status_display()})'
            })
        
        # التحقق من أن الباركود تابع لهذا البند (إذا تم تحديد البند)
        if sale_item_id:
            is_in_sale_item = SaleItemBarcode.objects.filter(
                sale_item_id=sale_item_id,
                barcode=barcode_obj,
                barcode_status='active'
            ).exists()
            
            if not is_in_sale_item:
                return JsonResponse({
                    'success': False,
                    'error': 'هذا الباركود ليس من ضمن بنود هذه الفاتورة'
                })
        
        # التحقق من أن الباركود لم يُرجع سابقاً
        already_returned = SaleReturnItemBarcode.objects.filter(
            barcode=barcode_obj,
            barcode_status='returned'
        ).exists()
        
        if already_returned:
            return JsonResponse({
                'success': False,
                'error': 'تم إرجاع هذا الباركود سابقاً'
            })
        
        return JsonResponse({
            'success': True,
            'message': 'باركود صالح للإرجاع',
            'barcode_id': barcode_obj.id,
            'barcode_value': barcode_obj.barcode_in
        })
        
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'المنتج غير موجود'}, status=404)
    except Exception as e:
        logger.error(f"خطأ في التحقق من الباركود للإرجاع: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)









#================================================
#  الجداول المساعدة 
# ===============================================


# ================ عملات ================
class CurrencyListView(LoginRequiredMixin, ListView):
    model = Currency
    template_name = 'invoice/Currency/currency_list.html'
    context_object_name = 'currencies'
    paginate_by = 10

    def get_queryset(self):
        return Currency.objects.all().order_by('code')

class CurrencyDetailView(LoginRequiredMixin, DetailView):
    model = Currency
    template_name = 'invoice/Currency/currency_detail.html'
    context_object_name = 'currency'

class CurrencyCreateView(LoginRequiredMixin, CreateView):
    model = Currency
    form_class = CurrencyForm
    template_name = 'invoice/Currency/currency_form.html'
    success_url = reverse_lazy('invoice:currency_list')

    def form_valid(self, form):
        messages.success(self.request, _('تمت إضافة العملة بنجاح'))
        return super().form_valid(form)

class CurrencyUpdateView(LoginRequiredMixin, UpdateView):
    model = Currency
    form_class = CurrencyForm
    template_name = 'invoice/Currency/currency_form.html'
    success_url = reverse_lazy('invoice:currency_list')

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث العملة بنجاح'))
        return super().form_valid(form)

class CurrencyDeleteView(LoginRequiredMixin, DeleteView):
    model = Currency
    template_name = 'invoice/Currency/currency_confirm_delete.html'
    success_url = reverse_lazy('invoice:currency_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _('تم حذف العملة بنجاح'))
        return super().delete(request, *args, **kwargs)

# ================ طرق الدفع ================
class PaymentMethodListView(LoginRequiredMixin, ListView):
    model = Payment_method
    template_name = 'invoice/Payment_method/payment_method_list.html'
    context_object_name = 'payment_methods'
    paginate_by = 10

    def get_queryset(self):
        return Payment_method.objects.all().order_by('name')

class PaymentMethodDetailView(LoginRequiredMixin, DetailView):
    model = Payment_method
    template_name = 'invoice/Payment_method/payment_method_detail.html'
    context_object_name = 'payment_method'

class PaymentMethodCreateView(LoginRequiredMixin, CreateView):
    model = Payment_method
    form_class = PaymentMethodForm
    template_name = 'invoice/Payment_method/payment_method_form.html'
    success_url = reverse_lazy('invoice:payment_method_list')

    def form_valid(self, form):
        messages.success(self.request, _('تمت إضافة طريقة الدفع بنجاح'))
        return super().form_valid(form)

class PaymentMethodUpdateView(LoginRequiredMixin, UpdateView):
    model = Payment_method
    form_class = PaymentMethodForm
    template_name = 'invoice/Payment_method/payment_method_form.html'
    success_url = reverse_lazy('invoice:payment_method_list')

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث طريقة الدفع بنجاح'))
        return super().form_valid(form)

class PaymentMethodDeleteView(LoginRequiredMixin, DeleteView):
    model = Payment_method
    template_name = 'invoice/Payment_method/payment_method_confirm_delete.html'
    success_url = reverse_lazy('invoice:payment_method_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _('تم حذف طريقة الدفع بنجاح'))
        return super().delete(request, *args, **kwargs)

# ================ شركات الشحن ================
class ShippingCompanyListView(LoginRequiredMixin, ListView):
    model = Shipping_com_m
    template_name = 'invoice/Shipping_com_m/shipping_company_list.html'
    context_object_name = 'shipping_companies'
    paginate_by = 10

    def get_queryset(self):
        return Shipping_com_m.objects.all().order_by('name')

class ShippingCompanyDetailView(LoginRequiredMixin, DetailView):
    model = Shipping_com_m
    template_name = 'invoice/Shipping_com_m/shipping_company_detail.html'
    context_object_name = 'shipping_company'

class ShippingCompanyCreateView(LoginRequiredMixin, CreateView):
    model = Shipping_com_m
    form_class = ShippingCompanyForm
    template_name = 'invoice/Shipping_com_m/shipping_company_form.html'
    success_url = reverse_lazy('invoice:shipping_company_list')

    def form_valid(self, form):
        messages.success(self.request, _('تمت إضافة شركة الشحن بنجاح'))
        return super().form_valid(form)

class ShippingCompanyUpdateView(LoginRequiredMixin, UpdateView):
    model = Shipping_com_m
    form_class = ShippingCompanyForm
    template_name = 'invoice/Shipping_com_m/shipping_company_form.html'
    success_url = reverse_lazy('invoice:shipping_company_list')

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث شركة الشحن بنجاح'))
        return super().form_valid(form)

class ShippingCompanyDeleteView(LoginRequiredMixin, DeleteView):
    model = Shipping_com_m
    template_name = 'invoice/Shipping_com_m/shipping_company_confirm_delete.html'
    success_url = reverse_lazy('invoice:shipping_company_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _('تم حذف شركة الشحن بنجاح'))
        return super().delete(request, *args, **kwargs)

# ================ الحالات ================
class StatusListView(LoginRequiredMixin, ListView):
    model = Status
    template_name = 'invoice/Status/status_list.html'
    context_object_name = 'statuses'
    paginate_by = 10

    def get_queryset(self):
        return Status.objects.all().order_by('name')

class StatusDetailView(LoginRequiredMixin, DetailView):
    model = Status
    template_name = 'invoice/Status/status_detail.html'
    context_object_name = 'status'

class StatusCreateView(LoginRequiredMixin, CreateView):
    model = Status
    form_class = StatusForm
    template_name = 'invoice/Status/status_form.html'
    success_url = reverse_lazy('invoice:status_list')

    def form_valid(self, form):
        messages.success(self.request, _('تمت إضافة الحالة بنجاح'))
        return super().form_valid(form)

class StatusUpdateView(LoginRequiredMixin, UpdateView):
    model = Status
    form_class = StatusForm
    template_name = 'invoice/Status/status_form.html'
    success_url = reverse_lazy('invoice:status_list')

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث الحالة بنجاح'))
        return super().form_valid(form)

class StatusDeleteView(LoginRequiredMixin, DeleteView):
    model = Status
    template_name = 'invoice/Status/status_confirm_delete.html'
    success_url = reverse_lazy('invoice:status_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _('تم حذف الحالة بنجاح'))
        return super().delete(request, *args, **kwargs)

# ================ أنواع الأسعار ================
class PriceTypeListView(LoginRequiredMixin, ListView):
    model = PriceType
    template_name = 'invoice/PriceType/price_type_list.html'
    context_object_name = 'price_types'
    paginate_by = 10

    def get_queryset(self):
        return PriceType.objects.all().order_by('name')

class PriceTypeDetailView(LoginRequiredMixin, DetailView):
    model = PriceType
    template_name = 'invoice/PriceType/price_type_detail.html'
    context_object_name = 'price_type'

class PriceTypeCreateView(LoginRequiredMixin, CreateView):
    model = PriceType
    form_class = PriceTypeForm
    template_name = 'invoice/PriceType/price_type_form.html'
    success_url = reverse_lazy('invoice:price_type_list')

    def form_valid(self, form):
        messages.success(self.request, _('تمت إضافة نوع السعر بنجاح'))
        return super().form_valid(form)

class PriceTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = PriceType
    form_class = PriceTypeForm
    template_name = 'invoice/PriceType/price_type_form.html'
    success_url = reverse_lazy('invoice:price_type_list')

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث نوع السعر بنجاح'))
        return super().form_valid(form)

class PriceTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = PriceType
    template_name = 'invoice/PriceType/price_type_confirm_delete.html'
    success_url = reverse_lazy('invoice:price_type_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _('تم حذف نوع السعر بنجاح'))
        return super().delete(request, *args, **kwargs)


@login_required
def get_product_barcodes(request, product_id):
    """
    API ذكي لجلب الباركودات المتاحة للبيع.
    يعيد قائمة الباركودات النشطة فقط (غير المباعة)
    """
    try:
        product = Product.objects.get(id=product_id)
        
        # معامل اختياري للتحقق من باركود معين (للتعديل)
        check_barcode = request.GET.get('check_barcode')
        sale_item_id = request.GET.get('sale_item_id')
        
        # سيناريو 1: التحقق من باركود محدد
        if check_barcode:
            try:
                barcode_obj = Barcode.objects.get(barcode_in=check_barcode, product=product)
                
                # باركود نشط -> متاح للبيع
                if barcode_obj.status == 'active':
                    return JsonResponse({'is_valid': True, 'message': 'متاح'})
                
                # باركود مباع -> نتحقق إن كان ملكاً لهذا البند (في حالة التعديل)
                elif barcode_obj.status == 'sold':
                    is_owner = SaleItemBarcode.objects.filter(
                        barcode=barcode_obj, 
                        sale_item_id=sale_item_id
                    ).exists()
                    
                    if is_owner:
                        return JsonResponse({'is_valid': True, 'message': 'موجود في الفاتورة'})
                    else:
                        return JsonResponse({'is_valid': False, 'message': 'هذا الباركود مباع مسبقاً'})
                
                # حالات أخرى
                else:
                    return JsonResponse({'is_valid': False, 'message': f'حالة الباركود: {barcode_obj.get_status_display()}'})
                    
            except Barcode.DoesNotExist:
                return JsonResponse({'is_valid': False, 'message': 'الباركود غير موجود'})
        
        # سيناريو 2: جلب قائمة الباركودات المتاحة للبيع
        else:
            # جلب الباركودات النشطة فقط (غير المباعة)
            barcodes_qs = Barcode.objects.filter(
                product=product, 
                status='active'
            ).order_by('barcode_in')
            
            barcodes_list = list(barcodes_qs.values('id', 'barcode_in', 'barcode_out'))
            
            # في حالة التعديل، نضيف الباركودات المرتبطة بالبند الحالي
            if sale_item_id:
                from .models import SaleItemBarcode
                item_barcodes = SaleItemBarcode.objects.filter(
                    sale_item_id=sale_item_id
                ).select_related('barcode')
                
                barcode_ids = set(b['id'] for b in barcodes_list)
                
                for ib in item_barcodes:
                    if ib.barcode_id not in barcode_ids:
                        barcodes_list.append({
                            'id': ib.barcode_id,
                            'barcode_in': ib.barcode.barcode_in,
                            'barcode_out': ib.barcode.barcode_out,
                            'is_current_item': True
                        })
            
            return JsonResponse({
                'success': True,
                'product_name': product.product_name,
                'barcodes': barcodes_list,
                'count': len(barcodes_list),
                'has_barcodes': len(barcodes_list) > 0
            })
            
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'المنتج غير موجود'}, status=404)
    except Exception as e:
        logger.error(f"خطأ في جلب باركودات المنتج: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)





#================================================
#  التقارير 
# ===============================================







class Date(Func):
    function = 'DATE'
    output_field = CharField()



@login_required
def statement_report_view(request):
    context = {}
    statement_data = []
    total_debit = Decimal('0.00')  
    total_credit = Decimal('0.00') 
    running_balance = Decimal('0.00')
    total_remaining = Decimal('0.00')
    
    selected_user = None
    user_type = None

    customer_ids = Sale.objects.values_list('sale_customer_id', flat=True).distinct()
    supplier_ids = Purch.objects.values_list('purch_supplier_id', flat=True).distinct()
    
    context['customers'] = User.objects.filter(id__in=customer_ids)
    context['suppliers'] = User.objects.filter(id__in=supplier_ids)

    if request.method == 'GET' and 'user_id' in request.GET:
        user_id = request.GET.get('user_id')
        
        try:
            selected_user = User.objects.get(id=user_id)
            raw_transactions = []

            is_customer = Sale.objects.filter(sale_customer=selected_user).exists()
            is_supplier = Purch.objects.filter(purch_supplier=selected_user).exists()
            
            if is_customer: 
                user_type = 'customer'
            elif is_supplier: 
                user_type = 'supplier'

            # ============================================
            # 1. فواتير المبيعات (للعملاء)
            # ============================================
            if is_customer:
                sales = Sale.objects.filter(sale_customer=selected_user).order_by('sale_date')
                for sale in sales:
                    # جلب المدفوعات لهذه الفاتورة
                    paid_amount = CashTransaction.objects.filter(
                        sale_invoice=sale,
                        transaction_type='sale_receipt'
                    ).aggregate(total=Sum('amount_in'))['total'] or Decimal('0.00')
                    
                    remaining = sale.sale_final_total - paid_amount
                    
                    raw_transactions.append({
                        'trans_date': sale.sale_date,
                        'trans_type': 'invoice_sale',
                        'ref_number': sale.uniqueId,
                        'slug': sale.slug,
                        'debit_amount': sale.sale_final_total,
                        'credit_amount': paid_amount,
                        'remaining_amount': remaining,
                        'note': f"فاتورة مبيعات - المدفوع: {paid_amount}" if paid_amount > 0 else "فاتورة مبيعات"
                    })
                    total_remaining += remaining

            # ============================================
            # 2. فواتير المشتريات (للموردين)
            # ============================================
            if is_supplier:
                purchases = Purch.objects.filter(purch_supplier=selected_user).order_by('purch_date')
                for purch in purchases:
                    # جلب المدفوعات لهذه الفاتورة
                    paid_amount = CashTransaction.objects.filter(
                        purchase_invoice=purch,
                        transaction_type='purchase_payment'
                    ).aggregate(total=Sum('amount_out'))['total'] or Decimal('0.00')
                    
                    remaining = purch.purch_final_total - paid_amount
                    
                    raw_transactions.append({
                        'trans_date': purch.purch_date,
                        'trans_type': 'invoice_purch',
                        'ref_number': purch.uniqueId,
                        'slug': purch.slug,
                        'debit_amount': paid_amount,
                        'credit_amount': purch.purch_final_total,
                        'remaining_amount': remaining,
                        'note': f"فاتورة مشتريات - المدفوع: {paid_amount}" if paid_amount > 0 else "فاتورة مشتريات"
                    })
                    total_remaining += remaining

            # ============================================
            # 3. مرتجعات المبيعات
            # ============================================
            if is_customer:
                sale_returns = SaleReturn.objects.filter(
                    original_sale__sale_customer=selected_user
                ).select_related('original_sale')
                
                for ret in sale_returns:
                    return_amount = ret.paid_amount if ret.paid_amount > 0 else ret.return_final_total
                    remaining = ret.return_final_total - return_amount
                    
                    raw_transactions.append({
                        'trans_date': ret.return_date,
                        'trans_type': 'return_sale',
                        'ref_number': ret.uniqueId,
                        'slug': ret.slug,
                        'original_ref': ret.original_sale.uniqueId,
                        'original_slug': ret.original_sale.slug,
                        'debit_amount': Decimal('0.00'),
                        'credit_amount': return_amount,
                        'remaining_amount': remaining,
                        'note': f"مرتجع مبيعات - عن فاتورة {ret.original_sale.uniqueId} - المبلغ المردود: {return_amount}"
                    })

            # ============================================
            # 4. مرتجعات المشتريات
            # ============================================
            if is_supplier:
                purchase_returns = PurchaseReturn.objects.filter(
                    original_purchase__purch_supplier=selected_user
                ).select_related('original_purchase')
                
                for ret in purchase_returns:
                    return_amount = ret.paid_amount if ret.paid_amount > 0 else ret.return_final_total
                    remaining = ret.return_final_total - return_amount
                    
                    raw_transactions.append({
                        'trans_date': ret.return_date,
                        'trans_type': 'return_purch',
                        'ref_number': ret.uniqueId,
                        'slug': ret.slug,
                        'original_ref': ret.original_purchase.uniqueId,
                        'original_slug': ret.original_purchase.slug,
                        'debit_amount': return_amount,
                        'credit_amount': Decimal('0.00'),
                        'remaining_amount': remaining,
                        'note': f"مرتجع مشتريات - عن فاتورة {ret.original_purchase.uniqueId} - المبلغ المستلم: {return_amount}"
                    })

            # ============================================
            # 5. الترتيب والحساب النهائي
            # ============================================
            def get_sort_date(x):
                d = x.get('trans_date')
                if d is None:
                    return datetime.datetime.min
                if isinstance(d, datetime.date) and not isinstance(d, datetime.datetime):
                    return datetime.datetime.combine(d, datetime.time.min)
                return d

            raw_transactions.sort(key=get_sort_date)

            total_debit = Decimal('0.00')
            total_credit = Decimal('0.00')
            running_balance = Decimal('0.00')
            statement_data = []

            for trans in raw_transactions:
                debit = trans['debit_amount'] if trans['debit_amount'] else Decimal('0.00')
                credit = trans['credit_amount'] if trans['credit_amount'] else Decimal('0.00')
                
                total_debit += debit
                total_credit += credit
                
                # حساب الرصيد التراكمي حسب نوع المستخدم
                if user_type == 'customer':
                    running_balance = total_debit - total_credit
                elif user_type == 'supplier':
                    running_balance = total_credit - total_debit
                else:
                    running_balance = total_debit - total_credit
                
                trans['balance'] = running_balance
                statement_data.append(trans)

            context['statement_data'] = statement_data
            context['total_debit'] = total_debit
            context['total_credit'] = total_credit
            context['total_remaining'] = total_remaining
            context['final_balance'] = running_balance
            
        except User.DoesNotExist:
            messages.error(request, "المستخدم غير موجود")
        except Exception as e:
            messages.error(request, f"حدث خطأ: {str(e)}")
            import traceback
            traceback.print_exc()

    context['selected_user'] = selected_user
    context['user_type'] = user_type
    return render(request, 'invoice/reports/statement_report.html', context)



#  تقرير كشف حساب الباركودات 
import datetime

@login_required
def barcode_statement_view(request):
    context = {}
    movements = []
    barcode_obj = None
    search_query = request.GET.get('q', '').strip()

    if search_query:
        try:
            # 1. جلب الباركود
            barcode_obj = Barcode.objects.get(barcode_in=search_query)
            
            # 2. جلب حركات الشراء
            purchase_items = PurchItemBarcode.objects.filter(
                barcode=barcode_obj
            ).select_related('purch_item__purch', 'purch_item__product')

            for item in purchase_items:
                movements.append({
                    'date': item.purch_item.purch.purch_date,
                    'type': 'purchase',
                    'type_display': 'فاتورة شراء',
                    'reference': item.purch_item.purch.uniqueId,
                    'detail': f"شراء - {item.purch_item.product.product_name if item.purch_item.product else item.purch_item.item_name}",
                    'quantity': item.quantity_used,
                    # الحالة عند الشراء: دخول للمخزون -> نشط
                    'status_display': 'نشط (Active)',
                    'status_class': 'status-active',
                })

            # 3. جلب حركات مرتجع الشراء
            return_items = PurchaseReturnItemBarcode.objects.filter(
                barcode=barcode_obj
            ).select_related('purchase_return_item__purchase_return', 'purchase_return_item__product')

            for item in return_items:
                movements.append({
                    'date': item.purchase_return_item.purchase_return.return_date,
                    'type': 'purchase_return',
                    'type_display': 'مرتجع شراء',
                    'reference': item.purchase_return_item.purchase_return.uniqueId,
                    'detail': f"إرجاع للمورد - {item.purchase_return_item.product.product_name if item.purchase_return_item.product else item.purchase_return_item.item_name}",
                    'quantity': item.quantity_used,
                    # الحالة: خروج من المخزون -> مرتجع
                    'status_display': 'مرتجع للمورد',
                    'status_class': 'status-returned',
                })

            # 4. جلب حركات البيع
            sale_items = SaleItemBarcode.objects.filter(
                barcode=barcode_obj
            ).select_related('sale_item__sale', 'sale_item__product')

            for item in sale_items:
                movements.append({
                    'date': item.sale_item.sale.sale_date,
                    'type': 'sale',
                    'type_display': 'فاتورة بيع',
                    'reference': item.sale_item.sale.uniqueId,
                    'detail': f"بيع - {item.sale_item.product.product_name if item.sale_item.product else item.sale_item.item_name}",
                    'quantity': item.quantity_used,
                    # الحالة عند البيع: خروج للعميل -> مباع
                    'status_display': 'مباع (Sold)',
                    'status_class': 'status-sold',
                })

            # 5. جلب حركات مرتجع البيع
            sale_return_items = SaleReturnItemBarcode.objects.filter(
                barcode=barcode_obj
            ).select_related('sale_return_item__sale_return', 'sale_return_item__product')

            for item in sale_return_items:
                movements.append({
                    'date': item.sale_return_item.sale_return.return_date,
                    'type': 'sale_return',
                    'type_display': 'مرتجع بيع',
                    'reference': item.sale_return_item.sale_return.uniqueId,
                    'detail': f"إرجاع من العميل - {item.sale_return_item.product.product_name if item.sale_return_item.product else item.sale_return_item.item_name}",
                    'quantity': item.quantity_used,
                    # الحالة: عودة للمخزون -> نشط (عادة)
                    'status_display': 'مرتجع (Returned)',
                    'status_class': 'status-returned',
                })

            # ترتيب الحركات حسب التاريخ
            movements.sort(key=lambda x: x['date'] or datetime.date.min)

        except Barcode.DoesNotExist:
            messages.error(request, "الباركود غير موجود في النظام")
        except Exception as e:
            messages.error(request, f"حدث خطأ: {str(e)}")

    context['movements'] = movements
    context['barcode_obj'] = barcode_obj
    context['search_query'] = search_query
    return render(request, 'invoice/reports/barcode_statement.html', context)


# فواتير لم تسدد او لها رصيد 




@login_required
def unpaid_sales_report(request):
    """
    تقرير فواتير المبيعات غير المدفوعة بالكامل (متابعة الديون)
    مع تصنيف فترات التأخير (Aging Report)
    """
    # جلب الفواتير التي لم تُسدد بالكامل
    invoices = Sale.objects.filter(
        Q(balance_due__gt=0) | Q(is_paid=False)
    ).select_related(
        'sale_customer'
    ).order_by('-sale_date')

    # تحديد فترات التأخير (بالأيام)
    # 0-30، 31-60، 61-90، أكثر من 90
    period_ranges = [
        (0, 30, 'حديث'),
        (31, 60, 'متأخر'),
        (61, 90, 'متأخر جداً'),
        (91, 9999, 'متعثر'),
    ]

    report_data = []
    grand_total_balance = 0

    today = timezone.now().date()

    for invoice in invoices:
        # حساب عدد أيام التأخير
        days_overdue = (today - invoice.sale_date).days
        
        # تحديد الفئة العمرية للدين
        category = "غير محدد"
        for start, end, label in period_ranges:
            if start <= days_overdue <= end:
                category = label
                break
        
        report_data.append({
            'invoice': invoice,
            'customer': invoice.sale_customer,
            'date': invoice.sale_date,
            'total': invoice.sale_final_total,
            'paid': invoice.paid_amount,
            'balance': invoice.balance_due,
            'days_overdue': days_overdue,
            'category': category,
        })
        
        grand_total_balance += invoice.balance_due

    context = {
        'title': 'تقرير الفواتير الغير مدفوعة ',
        'report_data': report_data,
        'grand_total_balance': grand_total_balance,
    }
    
    return render(request, 'invoice/reports/unpaid_sales_report.html', context)


# تقرير تقرير المنتجات الراكدة





@login_required
def dead_stock_report(request):
    """
    تقرير المنتجات الراكدة (موجودة ولم يتم بيعها منذ فترة)
    """
    # تحديد فترة الراكد (مثلاً 60 يوماً)
    days_threshold = int(request.GET.get('days', 60))
    date_threshold = timezone.now().date() - timedelta(days=days_threshold)

    # جلب المنتجات التي لها مخزون
    # تم إزالة 'category' من select_related لأنها غير موجودة في الموديل
    products = Product.objects.filter(
        current_stock_quantity__gt=0
    ).order_by('product_name')

    dead_items = []

    for product in products:
        # البحث عن آخر عملية بيع لهذا المنتج
        # ملاحظة: تأكد من أن SaleItem لديه حقل اسمه 'sale' يشير لفاتورة البيع
        # وأن الفاتورة لديها حقل 'sale_date'
        last_sale_item = SaleItem.objects.filter(
            product=product
        ).order_by('-sale__sale_date').first()
        
        # تحديد آخر تاريخ بيع
        last_sale_date = None
        if last_sale_item and last_sale_item.sale:
            last_sale_date = last_sale_item.sale.sale_date
        
        # التحقق: هل يوجد مبيعات بعد تاريخ الحد (date_threshold)؟
        # نستخدم filter().exists() لأنه أسرع
        has_recent_sales = SaleItem.objects.filter(
            product=product,
            sale__sale_date__gte=date_threshold
        ).exists()

        if not has_recent_sales:
            # حساب قيمة المخزون الراكد
            cost_price = product.average_purchase_cost or product.purch_price or Decimal('0.00')
            stock_value = product.current_stock_quantity * cost_price
            
            dead_items.append({
                'product': product,
                'stock': product.current_stock_quantity,
                'last_sale_date': last_sale_date,
                'value': stock_value,
            })

    total_dead_value = sum(item['value'] for item in dead_items)

    context = {
        'title': f'تقرير المواد الراكدة (أكثر من {days_threshold} يوم)',
        'dead_items': dead_items,
        'days_threshold': days_threshold,
        'total_dead_value': total_dead_value,
    }
    
    return render(request, 'invoice/reports/dead_stock_report.html', context)



def get_email_settings():
    obj, created = EmailSetting.objects.get_or_create(pk=1)
    return obj

@login_required
def email_settings_view(request):
    """عرض وتعديل إعدادات البريد الإلكتروني"""
    # جلب الإعدادات أو إنشائها إذا لم تكن موجودة
    setting = get_email_settings()

    if request.method == 'POST':
        form = EmailSettingForm(request.POST, instance=setting)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم حفظ إعدادات البريد الإلكتروني بنجاح.')
            return redirect('invoice:email_settings')
    else:
        form = EmailSettingForm(instance=setting)

    context = {
        'title': 'إعدادات البريد الإلكتروني',
        'form': form,
        'setting': setting,
    }
    return render(request, 'invoice/settings/email_settings.html', context)

# مثال على دالة إرسال بريد باستخدام الإعدادات الجديدة
def send_custom_email(subject, message, recipient_list):
    config = get_email_settings()
    
    try:
        send_mail(
            subject,
            message,
            config.default_from_email,
            recipient_list,
            fail_silently=False,
            auth_user=config.email_host_user,
            auth_password=config.email_host_password,
            connection=None # سيستخدم إعدادات settings.py الخلفية، أو يمكن تخصيصها هنا
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False



#  تقرير الأرباح (Profit Report)




@login_required
def profit_report_view(request):
    """
    تقرير الأرباح: يحسب صافي الربح خلال فترة محددة
    المعادلة: (المبيعات - تكلفة المشتريات) - المصاريف
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'show_results': False,
    }

    if start_date and end_date:
        # 1. جلب فواتير المبيعات في الفترة
        sales_qs = Sale.objects.filter(sale_date__range=[start_date, end_date])
        
        # إجمالي المبيعات
        total_sales = sales_qs.aggregate(total=Sum('sale_final_total'))['total'] or Decimal('0.00')
        
        # 2. حساب تكلفة البضائع المباعة (COGS)
        # نجلب بنود البيع ونضرب الكمية في متوسط سعر شراء المنتج
        sold_items = SaleItem.objects.filter(sale__in=sales_qs).select_related('product')
        
        total_cost = Decimal('0.00')
        for item in sold_items:
            # نستخدم average_purchase_cost إذا كان موجوداً، وإلا نستخدم purch_price
            cost_price = item.product.average_purchase_cost if item.product and item.product.average_purchase_cost else (item.product.purch_price if item.product else Decimal('0.00'))
            total_cost += (item.sold_quantity * cost_price)
        
        # 3. حساب إجمالي الخصومات الممنوحة في المبيعات
        total_sales_discount = sales_qs.aggregate(total=Sum('sale_discount'))['total'] or Decimal('0.00')

        # 4. المصاريف والسحوبات (من الصندوق)
        # نفترض أن أنواع المصاريف هي 'expense' أو 'withdrawal'
        expenses_qs = CashTransaction.objects.filter(
            transaction_date__date__range=[start_date, end_date],
            transaction_type__in=['expense', 'withdrawal']
        )
        total_expenses = expenses_qs.aggregate(total=Sum('amount_out'))['total'] or Decimal('0.00')

        # 5. حساب صافي الربح
        # الربح الإجمالي = المبيعات - التكلفة
        gross_profit = total_sales - total_cost
        # صافي الربح = الربح الإجمالي - المصاريف
        net_profit = gross_profit - total_expenses

        # ملء السياق للقالب
        context.update({
            'total_sales': total_sales,
            'total_cost': total_cost,
            'gross_profit': gross_profit,
            'total_sales_discount': total_sales_discount,
            'total_expenses': total_expenses,
            'net_profit': net_profit,
            'show_results': True,
        })

    return render(request, 'invoice/reports/profit_report.html', context)



# تقرير المبيعات حسب العميل (Sales by Customer Report)




@login_required
def sales_by_customer_report(request):
    """
    تقرير يوضح إجمالي مبيعات كل عميل وعدد الفواتير
    """
    # البحث حسب اسم العميل (اختياري)
    search_query = request.GET.get('q', '')

    # تجميع المبيعات لكل عميل
    # نقوم بتصفية المبيعات أولاً ثم التجميع لتحسين الأداء
    queryset = Sale.objects.values(
        'sale_customer__id',
        'sale_customer__username',
        'sale_customer__first_name',
        'sale_customer__last_name'
    ).annotate(
        total_amount=Sum('sale_final_total'),
        paid_amount=Sum('paid_amount'),
        invoice_count=Count('id')
    ).order_by('-total_amount') # ترتيب تنازلي حسب المبلغ

    # تطبيق فلتر البحث إذا وجد
    if search_query:
        # بحث في اسم المستخدم أو الاسم الأول أو الأخير
        queryset = queryset.filter(
            Q(sale_customer__username__icontains=search_query) |
            Q(sale_customer__first_name__icontains=search_query) |
            Q(sale_customer__last_name__icontains=search_query)
        )

    # حساب الإجماليات الكلية للصفحة
    grand_total = sum(item['total_amount'] or 0 for item in queryset)
    total_invoices = sum(item['invoice_count'] or 0 for item in queryset)

    context = {
        'title': 'تقرير المبيعات حسب العميل',
        'report_data': queryset,
        'grand_total': grand_total,
        'total_invoices': total_invoices,
        'search_query': search_query,
    }
    
    return render(request, 'invoice/reports/sales_by_customer_report.html', context)


#  تقرير المشتريات حسب المورد (Purchases by Supplier Report)


@login_required
def purchases_by_supplier_report(request):
    """
    تقرير يوضح إجمالي مشتريات كل مورد وعدد الفواتير
    """
    search_query = request.GET.get('q', '')

    # تجميع المشتريات لكل مورد
    queryset = Purch.objects.values(
        'purch_supplier__id',
        'purch_supplier__username',
        'purch_supplier__first_name',
        'purch_supplier__last_name'
    ).annotate(
        total_amount=Sum('purch_final_total'),
        paid_amount=Sum('paid_amount'),
        invoice_count=Count('id')
    ).order_by('-total_amount') # ترتيب تنازلي حسب المبلغ

    # تطبيق فلتر البحث
    if search_query:
        queryset = queryset.filter(
            Q(purch_supplier__username__icontains=search_query) |
            Q(purch_supplier__first_name__icontains=search_query) |
            Q(purch_supplier__last_name__icontains=search_query)
        )

    # حساب الإجماليات الكلية
    grand_total = sum(item['total_amount'] or 0 for item in queryset)
    total_invoices = sum(item['invoice_count'] or 0 for item in queryset)

    context = {
        'title': 'تقرير المشتريات حسب المورد',
        'report_data': queryset,
        'grand_total': grand_total,
        'total_invoices': total_invoices,
        'search_query': search_query,
    }
    
    return render(request, 'invoice/reports/purchases_by_supplier_report.html', context)


#تقرير المبيعات اليومية الشامل (Daily Sales Summary)

@login_required
def daily_sales_summary_report(request):
    """
    ملخص مبيعات يومي: يعرض مبيعات اليوم، المصروفات، والصافي
    """
    today = timezone.now().date()
    # السماح باختيار تاريخ آخر
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = timezone.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    # 1. مبيعات اليوم المحدد
    sales_today = Sale.objects.filter(sale_date=selected_date)
    total_sales = sales_today.aggregate(total=Sum('sale_final_total'))['total'] or Decimal('0.00')
    cash_received = sales_today.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
    invoices_count = sales_today.count()

    # 2. مصروفات اليوم (من الصندوق)
    expenses_today = CashTransaction.objects.filter(
        transaction_date__date=selected_date,
        transaction_type__in=['expense', 'withdrawal']
    )
    total_expenses = expenses_today.aggregate(total=Sum('amount_out'))['total'] or Decimal('0.00')

    # 3. صافي الصندوق (المقبوض - المصروف)
    net_cash = cash_received - total_expenses

    context = {
        'title': 'ملخص المبيعات اليومي',
        'selected_date': selected_date,
        'total_sales': total_sales,
        'cash_received': cash_received,
        'invoices_count': invoices_count,
        'total_expenses': total_expenses,
        'net_cash': net_cash,
    }
    
    return render(request, 'invoice/reports/daily_sales_summary.html', context)


# الفواتير الغير مسددة  مبيع  شراء 

@login_required
def unpaid_invoices_report(request):
    """
    تقرير موحد لفواتير المبيعات والمشتريات غير المسددة
    لمعرفة المبالغ المستحقة للشركة والمطلوبة منها.
    """
    # 1. جلب فواتير المبيعات ذات الأرصدة (التي لم تُدفع بالكامل)
    unpaid_sales = Sale.objects.filter(
        Q(balance_due__gt=0) | Q(is_paid=False)
    ).select_related('sale_customer').order_by('-sale_date')

    # 2. جلب فواتير المشتريات غير المدفوعة
    # نفترض أن الفاتورة غير مدفوعة إذا كان المبلغ المدفوع أقل من الإجمالي
    unpaid_purchases = Purch.objects.filter(
        paid_amount__lt=F('purch_final_total')
    ).select_related('purch_supplier').order_by('-purch_date')

    # حساب الإجماليات
    total_customers_debt = unpaid_sales.aggregate(total=Sum('balance_due'))['total'] or Decimal('0.00') # لنا عند العملاء
    total_suppliers_debt = Decimal('0.00') # علينا للموردين
    
    for purch in unpaid_purchases:
        total_suppliers_debt += (purch.purch_final_total - purch.paid_amount)

    # صافي الرصيد (إيجابي يعني لنا، سلبي يعني علينا)
    net_balance = total_customers_debt - total_suppliers_debt

    context = {
        'title': 'تقرير الفواتير غير المسددة',
        'unpaid_sales': unpaid_sales,
        'unpaid_purchases': unpaid_purchases,
        'total_customers_debt': total_customers_debt,
        'total_suppliers_debt': total_suppliers_debt,
        'net_balance': net_balance,
    }
    
    return render(request, 'invoice/reports/unpaid_invoices_report.html', context)




@login_required
def dead_stocks_report(request):
    """تقرير المنتجات الراكدة (موجودة ولم يتم بيعها منذ فترة)"""
    # تحديد فترة الراكد (مثلاً 60 يوماً)
    days_threshold = int(request.GET.get('days', 60))
    date_threshold = timezone.now().date() - timedelta(days=days_threshold)

    # جلب المنتجات التي لها مخزون
    products = Product.objects.filter(current_stock_quantity__gt=0).order_by('product_name')

    dead_items = []

    for product in products:
        # البحث عن آخر عملية بيع لهذا المنتج
        last_sale_item = SaleItem.objects.filter(product=product).order_by('-sale__sale_date').first()
        
        # تحديد آخر تاريخ بيع
        last_sale_date = None
        if last_sale_item and last_sale_item.sale:
            last_sale_date = last_sale_item.sale.sale_date
        
        # التحقق مما إذا كان هناك مبيعات بعد تاريخ الحد (date_threshold)
        has_recent_sales = SaleItem.objects.filter(
            product=product,
            sale__sale_date__gte=date_threshold
        ).exists()

        # إذا لم تكن هناك مبيعات حديثة، نعتبر المنتج راكداً
        if not has_recent_sales:
            dead_items.append({
                'product': product,
                'stock': product.current_stock_quantity,
                'last_sale_date': last_sale_date,
            })

    context = {
        'title': f'تقرير المواد الراكدة (أكثر من {days_threshold} يوم)',
        'dead_items': dead_items,
        'days_threshold': days_threshold,
    }
    
    return render(request, 'invoice/reports/dead_stocks_report.html', context)









# shopping --------------



# ===============================================
#  دوال مساعدة (Helpers)
# ===============================================

def get_product_price(product):
    """
    تحديد السعر النهائي للمنتج في المتجر (ذكية وديناميكية)
    1. تبحث أولاً في تصنيف المنتج (إذا كان مصنفاً ومربوطاً بمستوى تسعير).
    2. إذا لم تجد، ترجع لسعر العرض الأساسي أو سعر الجملة.
    """
    # التحقق مما إذا كان المنتج مصنف ولديه مستوى تسعير ديناميكي
    if hasattr(product, 'category') and product.category and product.category.pricing_tier:
        tier_id = product.category.pricing_tier.id
        try:
            tier_price = ProductPriceTier.objects.get(product=product, tier_id=tier_id)
            if tier_price.price and tier_price.price > 0:
                return tier_price.price
        except ProductPriceTier.DoesNotExist:
            pass # إذا لم يكن هناك سعر محدد، نتجاوز للمنطق التالي

    # المنطق الاحتياطي (كما كان سابقاً)
    if product.offer_1_price and product.offer_1_price > 0:
        return product.offer_1_price
    return product.wholesale_price



def get_product_image_url(product):
    """جلب رابط صورة المنتج بأمان"""
    if product.product_image:
        try:
            return product.product_image.url
        except:
            pass
    return "/static/images/no-image.png"


def get_or_create_cart(request):
    """جلب سلة التسوق الحالية أو إنشاء جديدة مع دمج سلة الزائر عند تسجيل الدخول"""
    user = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key
    
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    if user:
        cart, created = Cart.objects.get_or_create(user=user)
        # دمج سلة الزائر مع سلة المستخدم عند تسجيل الدخول
        if not created:
            guest_cart = Cart.objects.filter(session_key=session_key, user__isnull=True).first()
            if guest_cart:
                for item in guest_cart.items.all():
                    cart_item, item_created = CartItem.objects.get_or_create(
                        cart=cart, product=item.product,
                        defaults={'quantity': item.quantity}
                    )
                    if not item_created:
                        cart_item.quantity += item.quantity
                        cart_item.save()
                guest_cart.delete()
    else:
        cart, _ = Cart.objects.get_or_create(session_key=session_key, user__isnull=True)

    return cart


def prepare_product_data(product, setting=None):
    """تجهيز بيانات المنتج للعرض في لوحة التحكم (دالة موحدة لتجنب التكرار)"""
    if setting is None:
        setting, _ = ProductStoreSetting.objects.get_or_create(product=product)
    
    return {
        'id': product.id,
        'name': product.product_name,
        'image': get_product_image_url(product),
        'price_old': f"{product.wholesale_price:.2f}",
        'price_new': f"{get_product_price(product):.2f}",
        'store_section': setting.store_section,
        'display_order': setting.display_order,
        'is_visible': setting.is_visible,
        'badge_url': setting.badge_image.url if setting.badge_image else "",
        'show_old_price': product.offer_1_price > 0,
    }


def prepare_section_data(section):
    """تجهيز بيانات القسم الديناميكي للعرض في لوحة التحكم"""
    return {
        'id': section.id,
        'name': section.name,
        'style_type': section.style_type,
        'is_active': section.is_active,
        'items': [{
            'item_id': item.id,
            'name': item.product.product_name,
            'image': get_product_image_url(item.product),
            'price': f"{get_product_price(item.product):.2f}",
            'old_price': f"{item.product.wholesale_price:.2f}",
            'show_old_price': item.show_old_price
        } for item in section.items.all()]
    }


# ===============================================
#  واجهة المتجر (للزبون)
# ===============================================


# ===============================================
#  واجهة المتجر (للزبون) - النسخة المحسنة
# ===============================================




def store_front(request):
    """عرض واجهة المتجر الرئيسية - تدعم الفلاش المقسم تلقائياً"""
    cart = get_or_create_cart(request)
    
    # 1. الأقسام الديناميكية
    dynamic_sections = StoreSection.objects.filter(is_active=True).prefetch_related(
        Prefetch('items__product', queryset=Product.objects.select_related('store_setting', 'category__pricing_tier'))
    ).order_by('display_order')

    sections_data = []
    for section in dynamic_sections:
        section_items = []
        for item in section.items.all():
            product = item.product
            price = get_product_price(product)
            show_old_price = (price < product.wholesale_price) and item.show_old_price

            section_items.append({
                'id': product.id,
                'name': product.product_name,
                'image': get_product_image_url(product),
                'price_new': f"{price:.2f}",
                'price_old': f"{product.wholesale_price:.2f}" if show_old_price else "",
                'stock': int(product.current_stock_quantity),
                'show_old_price': show_old_price,
                'custom_badge': item.custom_badge.url if item.custom_badge else None,
                'display_order': item.display_order,
                'category_id': product.category_id,
                'category_name': product.category.name if product.category else "",
            })

        section_items.sort(key=lambda x: x['display_order'])
        sections_data.append({
            'id': section.id,
            'name': section.name,
            'style_type': section.style_type,
            'items': section_items
        })

    # 2. التصنيفات
    categories = Category.objects.filter(is_active=True).order_by('display_order')
    categories_data = []
    for cat in categories:
        visible_products = Product.objects.filter(
            category=cat,
            store_setting__is_visible=True
        ).select_related('store_setting')
        prods = []
        for p in visible_products:
            price = get_product_price(p)
            prods.append({
                'id': p.id,
                'name': p.product_name,
                'image': get_product_image_url(p),
                'price_new': f"{price:.2f}",
                'price_old': f"{p.wholesale_price:.2f}" if price < p.wholesale_price else "",
                'stock': int(p.current_stock_quantity),
            })
        categories_data.append({
            'id': cat.id,
            'name': cat.name,
            'icon': cat.icon.url if cat.icon else None,
            'products': prods,
        })

    # 3. إحصائيات
    store_stats = {
        'total_products': Product.objects.filter(store_setting__is_visible=True).count(),
        'total_orders': WebsiteOrder.objects.count(),
        'total_categories': categories.count(),
    }

    # 4. الطلبات الحديثة
    recent_orders_data = []
    for order in WebsiteOrder.objects.prefetch_related('items').order_by('-order_date')[:20]:
        first_item = order.items.first()
        name = order.full_name.split()[0] if order.full_name else 'عميل'
        try:
            name = name.encode('ascii', 'ignore').decode('ascii').strip()
            if len(name) < 2: name = 'عميل'
        except: name = 'عميل'
        
        product = 'منتج'
        if first_item:
            try:
                product = first_item.product_name.encode('ascii', 'ignore').decode('ascii').strip()
                if len(product) < 2: product = 'منتج'
            except: product = 'منتج'
        
        recent_orders_data.append({
            'name': name,
            'product': product,
            'time': order.order_date.strftime('%Y-%m-%d %H:%M'),
        })

    # 5. عتبة المخزون
    LOW_STOCK_THRESHOLD = 5

    # 6. منطق الفلاش الذكي (مقسم أو فردي)
    # نجلب العروض النشطة، ونأخذ أول 2 فقط
    active_flash_deals = FlashDeal.objects.filter(is_active=True).select_related('product__store_setting')[:2]
    
    flashes_data = []
    for deal in active_flash_deals:
        if not deal.is_currently_active():
            continue
        p = deal.product
        price = get_product_price(p)
        flashes_data.append({
            'id': deal.id,
            'product_id': p.id,
            'product_name': p.product_name,
            'product_image': get_product_image_url(p),
            'original_price': f"{price:.2f}",
            'deal_price': f"{deal.deal_price:.2f}",
            'max_quantity': deal.max_quantity,
            'remaining': deal.remaining_quantity(),
            'percentage': deal.remaining_percentage(),
            'ends_at': deal.ends_at.isoformat(),
            'stock': int(p.current_stock_quantity),
        })

    # 7. الشريط العلوي والأيقونات (الجديد)
    top_announcements = StoreAnnouncement.objects.filter(is_active=True).order_by('order')
    store_features = StoreFeatureIcon.objects.filter(is_active=True).order_by('order')

    context = {
        'cart_count': cart.items.count(),
        'dynamic_sections': dynamic_sections,
        'sections_data': sections_data,
        'top_banners': StoreBanner.objects.filter(is_active=True, position='top').order_by('order'),
        'side_banners': StoreBanner.objects.filter(is_active=True, position='side').order_by('order'),
        'categories': categories,
        'categories_json': json.dumps(categories_data, ensure_ascii=False),
        'sections_json': json.dumps(sections_data, ensure_ascii=False),
        'store_stats': store_stats,
        'recent_orders_json': json.dumps(recent_orders_data, ensure_ascii=False),
        'low_stock_threshold': LOW_STOCK_THRESHOLD,
        'flashes_data': flashes_data,  # قائمة قد تحتوي على 1 أو 2 عنصر
        'announcements': top_announcements,
        'store_features': store_features,
        'flash_deals_url': '/invoice/api/flash-deals/',
    }
    return render(request, 'invoice/store/store.html', context)

# ===============================================
#  سلة التسوق (API & Pages)
# ===============================================


def add_to_cart(request):
    """إضافة منتج للسلة (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=400)
    
    try:
        data = json.loads(request.body)
        product = get_object_or_404(Product, id=data.get('product_id'))
        cart = get_or_create_cart(request)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product,
            defaults={'quantity': int(data.get('quantity', 1))}
        )
        if not created:
            cart_item.quantity += int(data.get('quantity', 1))
            cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': 'تمت الإضافة للسلة' if created else 'تم تحديث الكمية',
            'cart_count': cart.items.count()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


def update_cart_item(request):
    """تعديل كمية منتج في السلة (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=400)
    
    try:
        data = json.loads(request.body)
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=data.get('item_id'))
        
        if cart_item.cart != cart:
            return JsonResponse({'success': False, 'message': 'غير مصرح'}, status=403)
        
        quantity = int(data.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            message = 'تم تحديث الكمية'
        else:
            cart_item.delete()
            message = 'تم حذف المنتج'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'new_total': float(cart.total_price),
            'cart_count': cart.items.count()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


def remove_from_cart(request):
    """حذف منتج من السلة (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=400)
    
    try:
        data = json.loads(request.body)
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=data.get('item_id'))
        
        if cart_item.cart != cart:
            return JsonResponse({'success': False, 'message': 'غير مصرح'}, status=403)
        
        cart_item.delete()
        return JsonResponse({
            'success': True,
            'message': 'تم الحذف',
            'new_total': float(cart.total_price),
            'cart_count': cart.items.count()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


def cart_detail(request):
    """عرض صفحة السلة"""
    cart = get_or_create_cart(request)
    return render(request, 'invoice/store/order.html', {
        'cart': cart,
        'cart_items': cart.items.select_related('product').all(),
        'title': 'سلة التسوق'
    })


def checkout_view(request):
    """صفحة إتمام الشراء"""
    cart = get_or_create_cart(request)
    if cart.items.count() == 0:
        return redirect('invoice:store_front')
    return render(request, 'invoice/store/checkout.html', {'cart': cart, 'title': 'إتمام الشراء'})



from django.db import transaction
from django.db.models import F

def place_order_view(request):
    """تأكيد الطلب وإنشاءه في قاعدة البيانات (النسخة المحصنة)"""
    if request.method != 'POST':
        return redirect('invoice:store_front')
    
    cart = get_or_create_cart(request)
    if cart.items.count() == 0:
        return JsonResponse({'success': False, 'message': 'السلة فارغة'}, status=400)

    try:
        # 1. بدء المعاملة الآمنة (Transaction)
        with transaction.atomic():
            
            # 2. قفل المنتجات الموجودة في السلة لمنع أي شخص آخر من شرائها في نفس الثانية
            product_ids = cart.items.values_list('product_id', flat=True)
            products = Product.objects.select_for_update().filter(id__in=product_ids)
            
            # 3. التحقق من توفر المخزون قبل إنشاء الطلب
            for item in cart.items.all():
                # جلب المنتج المقفل من قاعدة البيانات
                product = products.get(id=item.product.id)
                
                if product.current_stock_quantity < item.quantity:
                    # إذا لم يكن المخزون كافياً، يتم إلغاء العملية بالكامل
                    raise ValueError(f'المنتج "{product.product_name}" غير متوفر بالكمية المطلوبة. المتاح: {product.current_stock_quantity}')

            # 4. إذا وصلنا هنا، فالمخزون متوفر، نقوم بإنشاء الطلب
            order = WebsiteOrder.objects.create(
                user=request.user if request.user.is_authenticated else None,
                full_name=request.POST.get('full_name'),
                phone=request.POST.get('phone'),
                address=request.POST.get('address'),
                notes=request.POST.get('notes', ''),
                total_amount=cart.total_price,
                status='new'
            )

            # 5. إنشاء عناصر الطلب وخصم المخزون (آمناً لأن المنتجات مقفلة)
            for item in cart.items.all():
                WebsiteOrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.product_name,
                    price=get_product_price(item.product),
                    quantity=item.quantity
                )
                # خصم المخزون فوراً
                item.product.current_stock_quantity = F('current_stock_quantity') - item.quantity
                item.product.save(update_fields=['current_stock_quantity'])

            # 6. تفريغ السلة
            cart.items.all().delete()
            
            return JsonResponse({
                'success': True,
                'message': f'تم استلام طلبك! رقم الطلب: #{order.id}',
                'order_id': order.id
            })
            
    except ValueError as e:
        # في حالة عدم توفر المخزون، نرجع رسالة خطأ واضحة للعميل
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'حدث خطأ أثناء معالجة الطلب، يرجى المحاولة مرة أخرى.'}, status=500)




# ===============================================
#  لوحة تحكم المدير
# ===============================================



def prepare_product_data(product, setting=None):
    """تجهيز بيانات المنتج للعرض في لوحة التحكم"""
    if setting is None:
        setting, _ = ProductStoreSetting.objects.get_or_create(product=product)
    
    return {
        'id': product.id,
        'name': product.product_name,
        'image': get_product_image_url(product),
        'price_old': f"{product.wholesale_price:.2f}",
        'price_new': f"{get_product_price(product):.2f}",
        'store_section': setting.store_section,
        'display_order': setting.display_order,
        'is_visible': setting.is_visible,
        'badge_url': setting.badge_image.url if setting.badge_image else "",
        'show_old_price': product.offer_1_price > 0,
        'category_id': product.category_id if product.category_id else None,
    }


@login_required
def control_store(request):
    """لوحة تحكم المتجر الإلكتروني"""
    banners = StoreBanner.objects.all().order_by('order', '-created_at')
    
    products_data = [
        prepare_product_data(p) 
        for p in Product.objects.all().order_by('-date_created')
    ]

    sections_list = [
        prepare_section_data(sec)
        for sec in StoreSection.objects.all().prefetch_related('items__product').order_by('display_order')
    ]

    context = {
        'banners': banners,
        'products_data': products_data,
        'section_choices': ProductStoreSetting.SECTION_CHOICES,
        'sections_list': sections_list,
        'categories': Category.objects.all().order_by('display_order'),
        'flash_deals_url': '/invoice/api/flash-deals/',
        # البيانات الجديدة للتحكم بالشريط والأيقونات
        'announcements_list': StoreAnnouncement.objects.all().order_by('order'),
        'features_list': StoreFeatureIcon.objects.all().order_by('order'),
        'available_flash_deals': FlashDeal.objects.all(),
    }
    return render(request, 'invoice/store/control_store.html', context)





@login_required
@require_POST
def api_update_product_category(request, product_id):
    """تحديث تصنيف المنتج من لوحة التحكم"""
    try:
        product = get_object_or_404(Product, id=product_id)
        data = json.loads(request.body)
        
        category_id = data.get('category_id')
        if category_id == '' or category_id is None:
            product.category = None
        else:
            product.category = get_object_or_404(Category, id=category_id)
            
        product.save()
        return JsonResponse({'success': True, 'message': 'تم تحديث التصنيف'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)





# ===============================================
#  API: إعدادات المنتجات
# ===============================================

@login_required
@require_POST
def api_update_badge_image(request, product_id):
    """تحديث صورة الشعار للمنتج"""
    try:
        product = get_object_or_404(Product, id=product_id)
        settings_obj, _ = ProductStoreSetting.objects.get_or_create(product=product)
        
        if 'badge_image' in request.FILES:
            settings_obj.badge_image = request.FILES['badge_image']
            settings_obj.save()
            return JsonResponse({'success': True, 'image_url': settings_obj.badge_image.url})
        return JsonResponse({'success': False, 'message': 'لم يتم إرسال صورة'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_POST
def api_update_product_store_settings(request, product_id):
    """تحديث إعدادات المتجر للمنتج (الظهور، القسم، الترتيب)"""
    try:
        product = get_object_or_404(Product, id=product_id)
        data = json.loads(request.body)
        field_name, value = data.get('field'), data.get('value')
        
        settings_obj, _ = ProductStoreSetting.objects.get_or_create(product=product)
        
        allowed_fields = ['is_visible', 'store_section', 'show_old_price', 'display_order']
        if field_name in allowed_fields:
            if field_name in ['is_visible', 'show_old_price']:
                value = str(value).lower() in ['true', '1', 'yes']
            elif field_name == 'display_order':
                value = int(value or 0)
            setattr(settings_obj, field_name, value)
            settings_obj.save()
            return JsonResponse({'success': True, 'new_value': value})
        return JsonResponse({'success': False, 'message': 'حقل غير مسموح'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ===============================================
#  API: البنرات الإعلانية
# ===============================================

@login_required
@require_POST
def api_add_banner(request):
    """إضافة بنر جديد"""
    try:
        image = request.FILES.get('image')
        if not image:
            return JsonResponse({'success': False, 'message': 'الصورة مطلوبة'}, status=400)

        banner = StoreBanner.objects.create(
            title=request.POST.get('title') or image.name.rsplit('.', 1)[0],
            image=image,
            link_url=request.POST.get('link_url') or None,
            position=request.POST.get('position', 'top'),
            order=int(request.POST.get('order', 0)),
            is_active=request.POST.get('is_active') == 'true'
        )
        return JsonResponse({'success': True, 'banner_id': banner.id})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_POST
def api_update_banner(request, banner_id):
    """تحديث بنر"""
    try:
        banner = get_object_or_404(StoreBanner, id=banner_id)
        banner.title = request.POST.get('title')
        banner.link_url = request.POST.get('link_url')
        banner.position = request.POST.get('position')
        banner.order = int(request.POST.get('order', 0))
        banner.is_active = request.POST.get('is_active') == 'true'
        
        if 'image' in request.FILES:
            banner.image = request.FILES['image']
        banner.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
def delete_banner(request, banner_id):
    """حذف بنر"""
    get_object_or_404(StoreBanner, id=banner_id).delete()
    messages.success(request, 'تم حذف البنر بنجاح')
    return redirect('invoice:control_store')


# ===============================================
#  API: الأقسام الديناميكية
# ===============================================

@login_required
@require_POST
def api_add_section(request):
    """إنشاء قسم جديد"""
    try:
        data = json.loads(request.body)
        if not data.get('name'):
            return JsonResponse({'success': False, 'message': 'اسم القسم مطلوب'}, status=400)
        
        section = StoreSection.objects.create(
            name=data.get('name'),
            style_type=data.get('style_type', 'grid'),
            display_order=StoreSection.objects.count()
        )
        return JsonResponse({'success': True, 'section_id': section.id})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@require_POST
def api_update_section(request, section_id):
    """تحديث بيانات القسم"""
    try:
        data = json.loads(request.body)
        section = get_object_or_404(StoreSection, id=section_id)
        section.name = data.get('name', section.name)
        section.style_type = data.get('style_type', section.style_type)
        section.is_active = data.get('is_active', section.is_active)
        section.save()
        return JsonResponse({'success': True})
    except StoreSection.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'القسم غير موجود'}, status=404)


@login_required
@require_POST
def api_delete_section(request, section_id):
    """حذف قسم"""
    try:
        get_object_or_404(StoreSection, id=section_id).delete()
        return JsonResponse({'success': True})
    except StoreSection.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'القسم غير موجود'}, status=404)


@login_required
@require_POST
def api_add_product_to_section(request, section_id):
    """إضافة منتج إلى قسم"""
    try:
        data = json.loads(request.body)
        section = get_object_or_404(StoreSection, id=section_id)
        product = get_object_or_404(Product, id=data.get('product_id'))
        
        item, created = ProductSectionItem.objects.get_or_create(
            section=section,
            product=product,
            defaults={'display_order': section.items.count()}
        )
        
        if created:
            return JsonResponse({'success': True, 'item_id': item.id})
        return JsonResponse({'success': False, 'message': 'المنتج مضاف مسبقاً'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@require_POST
def api_remove_product_from_section(request, section_id, item_id):
    """حذف منتج من قسم"""
    try:
        item = get_object_or_404(ProductSectionItem, id=item_id, section_id=section_id)
        item.delete()
        return JsonResponse({'success': True})
    except ProductSectionItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'العنصر غير موجود'}, status=404)



@login_required
@require_POST
def api_update_product_category(request, product_id):
    """تحديث تصنيف المنتج"""
    try:
        product = get_object_or_404(Product, id=product_id)
        data = json.loads(request.body)
        
        # السماح بتفريغ التصنيف (إرسال null)
        category_id = data.get('category_id')
        if category_id == '' or category_id is None:
            product.category = None
        else:
            from .models import Category
            product.category = get_object_or_404(Category, id=category_id)
            
        product.save()
        return JsonResponse({'success': True, 'message': 'تم تحديث التصنيف'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
# ===============================================
#  إدارة الطلبات (عرض وتحويل لفاتورة)
# ===============================================

@login_required
def orders_list_view(request):
    """قائمة طلبات المتجر للمدير"""
    return render(request, 'invoice/store/admin_orders_list.html', {
        'orders': WebsiteOrder.objects.all().order_by('-order_date'),
        'title': 'إدارة طلبات المتجر'
    })


@login_required
def order_detail_view(request, order_id):
    """تفاصيل طلب معين"""
    order = get_object_or_404(WebsiteOrder, id=order_id)
    return render(request, 'invoice/store/admin_order_detail.html', {
        'order': order,
        'title': f'تفاصيل الطلب #{order.id}'
    })


@login_required
def convert_order_to_invoice(request, order_id):
    """تحويل طلب المتجر إلى فاتورة بيع في نظام المحاسبة"""
    order = get_object_or_404(WebsiteOrder, id=order_id)

    if order.related_sale:
        messages.warning(request, 'هذا الطلب تم تحويله مسبقاً إلى فاتورة.')
        return redirect('invoice:order_detail', order_id=order.id)

    try:
        with transaction.atomic():
            sale = Sale(
                created_by=request.user,
                sale_customer=order.user,
                sale_date=order.order_date.date(),
                sale_customer_phone=order.phone,
                sale_address=order.address,
                sale_notes=f"طلب متجر رقم #{order.id} - {order.notes or ''}",
                paid_amount=order.total_amount,
                is_paid=True
            )
            sale.save()

            for item in order.items.all():
                sale_item = SaleItem(
                    sale=sale,
                    product=item.product,
                    item_name=item.product_name,
                    sold_quantity=item.quantity,
                    unit_price=item.price
                )
                sale_item.save()
                # تم تعطيل خصم المخزون لأنه يتم الآن آلياً عند الشراء من المتجر لمنع الخصم المزدوج
                # sale_item.update_product_stock()

            sale.calculate_and_save_totals()
            
            CashTransaction.objects.create(
                transaction_date=timezone.now(),
                amount_in=order.total_amount,
                amount_out=Decimal('0.00'),
                transaction_type='sale_receipt',
                sale_invoice=sale,
                notes=f"تحصيل نقد مقابل طلب متجر #{order.id}",
                created_by=request.user
            )

            order.related_sale = sale
            order.status = 'processing'
            order.save()
            
            messages.success(request, f'تم التحويل بنجاح! رقم الفاتورة: {sale.uniqueId}')
            return redirect('invoice:sale_detail', slug=sale.slug)

    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء التحويل: {str(e)}')
        return redirect('invoice:order_detail', order_id=order.id)

#=====

# ===============================================
#  API: طلب إشعار (من الواجهة)
# ===============================================

def api_request_notification(request):
    """حفظ طلب الإشعار عند نفاد المخزون"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid Request'}, status=405)
    
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        email = data.get('email')
        
        if not product_id or not email:
            return JsonResponse({'success': False, 'message': 'البيانات ناقصة'}, status=400)

        product = get_object_or_404(Product, id=product_id)

        # التعديل الهام: استخدام الحقل الصحيح من الموديل current_stock_quantity
        if product.current_stock_quantity > 0:
            return JsonResponse({'success': False, 'message': 'المنتج متوفر الآن!'})

        # حفظ الطلب
        notification, created = StockNotification.objects.get_or_create(
            product=product,
            email=email
        )
        
        if created:
            msg = 'تم تسجيل طلبك! سنخبرك فور توفر المادة.'
        else:
            msg = 'أنت مسجل مسبقاً في قائمة الانتظار لهذا المنتج.'
            
        return JsonResponse({'success': True, 'message': msg})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ===============================================
#  إدارة: قائمة المنتجات المنتظرة
# ===============================================


@login_required
def admin_stock_notifications(request):
    """
    عرض قائمة بالمنتجات التي ينتظرها أشخاص (فقط الطلبات غير المرسلة)
    """
    # ==========================================
    # التعديل هنا: إضافة .filter(is_sent=False)
    # ==========================================
    # هذا الشرط سيجعل الدالة تجلب فقط الطلبات التي لم يتم إرسالها بعد
    raw_stats = StockNotification.objects.filter(is_sent=False).values('product__id', 'product__product_name', 'product__product_image').annotate(
        waiting_count=Count('id')
    ).order_by('-waiting_count')

    # تجهيز البيانات للقالب (مع معالجة رابط الصورة)
    notifications_stats = []
    for item in raw_stats:
        img_path = item.get('product__product_image')
        
        if img_path:
            image_url = f"/media/{img_path}" 
        else:
            image_url = "/static/images/no-image.png"

        notifications_stats.append({
            'id': item['product__id'],
            'name': item['product__product_name'],
            'image_url': image_url,
            'waiting_count': item['waiting_count']
        })

    return render(request, 'invoice/store/admin_notifications.html', {
        'notifications_stats': notifications_stats,
        'title': 'تنبيهات توفر المواد'
    })


# ===============================================
#  إدارة: إرسال الإشعارات
# ===============================================


# ==========================================================
# دالة إرسال الإشعارات (محدثة لتدعم الأرشيف)
# ==========================================================
@login_required
@require_POST
def admin_send_notification(request, product_id):
    """
    إرسال إيميل للجميع ينتظرون هذا المنتج ثم أرشفة السجلات
    """
    # 1. جلب البيانات والتحقق
    try:
        product = get_object_or_404(Product, id=product_id)
        notifications = StockNotification.objects.filter(product=product)
        
        if notifications.count() == 0:
            return JsonResponse({'success': False, 'message': 'لا يوجد طلبات إشعار لهذا المنتج'})

        # 2. جلب إعدادات البريد الديناميكية (من قاعدة البيانات)
        try:
            connection, from_email = get_active_email_connection()
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'تعذر العثور على إعدادات البريد: {str(e)}'})

        if connection and from_email:
            # 3. حفظ الإعدادات الحالية لاستعادتها لاحقاً
            old_host = getattr(settings, 'EMAIL_HOST', None)
            old_port = getattr(settings, 'EMAIL_PORT', None)
            old_user = getattr(settings, 'EMAIL_HOST_USER', None)
            old_pass = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
            old_tls = getattr(settings, 'EMAIL_USE_TLS', None)
            old_from = getattr(settings, 'DEFAULT_FROM_EMAIL', None)

            try:
                # 4. تطبيق إعدادات البريد من قاعدة البيانات على إعدادات النظام مؤقتاً
                settings.EMAIL_HOST = connection.host
                settings.EMAIL_PORT = connection.port
                settings.EMAIL_HOST_USER = connection.username
                settings.EMAIL_HOST_PASSWORD = connection.password
                settings.EMAIL_USE_TLS = connection.use_tls
                settings.DEFAULT_FROM_EMAIL = from_email

                # 5. إرسال الإيميل
                emails_list = list(notifications.values_list('email', flat=True))
                subject = f"عاد التوفر: {product.product_name}"
                
                # تحضير محتوى الإيميل (HTML)
                message_html = render_to_string('invoice/store/email_notification.html', {
                    'product': product,
                    'site_url': request.build_absolute_uri('/')[:-1]
                })

                email = EmailMessage(
                    subject=subject,
                    body=message_html,
                    from_email=from_email,
                    bcc=emails_list, # إرسال نسخة مخفية للجميع
                )
                email.content_subtype = "html" # تحديد المحتوى كـ HTML
                email.send()

                # 6. أرشفة السجلات (تعديل الحقول بدلاً من الحذف)
                # نحتاج لاستيراد timezone من django.utils
                from django.utils import timezone 
                notifications.update(is_sent=True, sent_at=timezone.now())

                return JsonResponse({
                    'success': True, 
                    'message': f'تم إرسال الإشعار لـ {notifications.count()} شخص ونقله للأرشيف.'
                })

            finally:
                # 7. استعادة الإعدادات الأصلية (تنظيف) ضروري جداً
                settings.EMAIL_HOST = old_host
                settings.EMAIL_PORT = old_port
                settings.EMAIL_HOST_USER = old_user
                settings.EMAIL_HOST_PASSWORD = old_pass
                settings.EMAIL_USE_TLS = old_tls
                settings.DEFAULT_FROM_EMAIL = old_from

        else:
            return JsonResponse({'success': False, 'message': 'لم يتم العثور على إعدادات بريد صالحة في قاعدة البيانات'})

    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
def admin_notification_archive(request):
    """عرض أرشيف الإشعارات التي تم إرسالها"""
    archive = StockNotification.objects.filter(is_sent=True).select_related('product').order_by('-sent_at')
    
    return render(request, 'invoice/store/notification_archive.html', {
        'archive': archive,
        'title': 'أرشيف إشعارات المخزون'
    })



@login_required
@require_POST
def admin_undo_archive_notification(request):
    """
    إعادة تنبيه من الأرشيف إلى القائمة المعلقة
    """
    response_data = {'success': False, 'message': 'حدث خطأ غير متوقع'}
    
    try:
        # محاولة قراءة البيانات
        try:
            data = json.loads(request.body)
            notif_id = data.get('id')
        except json.JSONDecodeError:
            response_data['message'] = 'بيانات غير صالحة'
            return JsonResponse(response_data, status=400)

        # جلب السجل
        try:
            notif = StockNotification.objects.get(id=notif_id, is_sent=True)
        except StockNotification.DoesNotExist:
            response_data['message'] = 'هذا السجل غير موجود أو تم حذفه.'
            return JsonResponse(response_data, status=404)

        # تنفيذ العملية
        notif.is_sent = False
        notif.sent_at = None
        notif.save()

        response_data['success'] = True
        response_data['message'] = 'تم إعادة التنبيه للقائمة المعلقة بنجاح.'

    except Exception as e:
        # طباعة الخطأ في السيرفر للتصحيح
        print(f"Error in undo_archive: {str(e)}")
        response_data['message'] = f'خطأ داخلي: {str(e)}'

    return JsonResponse(response_data)





@login_required
def api_flash_deals(request):
    """قائمة عروض الفلاش"""
    try:
        deals = FlashDeal.objects.select_related('product__store_setting').order_by('-created_at')
        data = []
        for deal in deals:
            p = deal.product
            try:
                original = f"{get_product_price(p):.2f}"
            except:
                original = "0.00"
            try:
                remaining = deal.remaining_quantity()
                percentage = deal.remaining_percentage()
            except:
                remaining = deal.max_quantity
                percentage = 100
            try:
                is_active = deal.is_currently_active()
            except:
                is_active = deal.is_active
            try:
                ends_at = deal.ends_at.strftime('%Y-%m-%d %H:%M') if deal.ends_at else ''
            except:
                ends_at = ''
            
            if is_active:
                status = 'نشط'
            elif deal.ends_at and timezone.now() > deal.ends_at:
                status = 'منتهي'
            else:
                status = 'معطّل'
            
            data.append({
                'id': deal.id,
                'product_id': p.id,
                'product_name': p.product_name,
                'product_image': get_product_image_url(p),
                'original_price': original,
                'deal_price': f"{deal.deal_price:.2f}",
                'max_quantity': deal.max_quantity,
                'remaining': remaining,
                'percentage': percentage,
                'ends_at': ends_at,
                'is_active': is_active,
                'status_text': status,
            })
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def api_add_flash_deal(request):
    """إضافة عرض فلاش"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        if not product_id:
            return JsonResponse({'success': False, 'message': 'المنتج مطلوب'}, status=400)
        
        product = get_object_or_404(Product, id=product_id)
        
        if not hasattr(product, 'store_setting') or not product.store_setting.is_visible:
            return JsonResponse({'success': False, 'message': 'المنتج غير ظاهر في المتجر'}, status=400)
        
        from datetime import timedelta
        hours = int(data.get('hours', 6))
        
        deal = FlashDeal.objects.create(
            product=product,
            deal_price=data.get('deal_price', 0),
            max_quantity=int(data.get('max_quantity', 10)),
            ends_at=timezone.now() + timedelta(hours=hours),
            is_active=data.get('is_active', True),
        )
        return JsonResponse({'success': True, 'message': 'تم إضافة العرض بنجاح', 'deal_id': deal.id})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)




@login_required
@require_POST
def api_toggle_flash_deal(request, deal_id):
    """تفعيل/تعطيل عرض فلاش"""
    try:
        deal = get_object_or_404(FlashDeal, id=deal_id)
        deal.is_active = not deal.is_active
        deal.save()
        return JsonResponse({'success': True, 'is_active': deal.is_active})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
def api_delete_flash_deal(request, deal_id):
    """حذف عرض فلاش"""
    get_object_or_404(FlashDeal, id=deal_id).delete()
    return JsonResponse({'success': True, 'message': 'تم الحذف'})



# ===============================================
#  API: إدارة الشريط العلوي والأيقونات
# ===============================================


# ===============================================
#  API: إدارة الشريط العلوي - النسخة المُصححة
# ===============================================

@login_required
@require_POST
def api_add_announcement(request):
    """إضافة إعلان مع دعم اختيار الأيقونة"""
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        if not text:
            return JsonResponse({'success': False, 'message': 'نص الإعلان مطلوب'}, status=400)
        
        icon_class = data.get('icon_class', 'fa-bullhorn').strip()
        
        StoreAnnouncement.objects.create(
            text=text,
            icon_class=icon_class,
            order=StoreAnnouncement.objects.count()
        )
        return JsonResponse({'success': True, 'message': 'تم إضافة الإعلان بنجاح'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'بيانات غير صالحة'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_POST
def api_delete_announcement(request, ann_id):
    """حذف إعلان - تم إضافة @require_POST ومعالجة أفضل"""
    try:
        announcement = get_object_or_404(StoreAnnouncement, id=ann_id)
        announcement.delete()
        return JsonResponse({'success': True, 'message': 'تم الحذف بنجاح'})
    except StoreAnnouncement.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'الإعلان غير موجود'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)



@login_required
@require_POST
def api_update_feature(request, feature_id):
    """تحديث عنوان الأيقونة"""
    try:
        data = json.loads(request.body)
        feature = get_object_or_404(StoreFeatureIcon, id=feature_id)
        feature.title = data.get('title', feature.title)
        # icon_class يمكن تعديله أيضاً لكن سنكتفي بالعنوان للتبسيط في الواجهة
        feature.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


