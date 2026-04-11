from .models import Cart

def cart_count(request):
    count = 0
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                count = cart.items.count()
        except Exception:
            pass
    else:
        session_key = request.session.session_key
        if session_key:
            try:
                cart = Cart.objects.filter(session_key=session_key, user__isnull=True).first()
                if cart:
                    count = cart.items.count()
            except Exception:
                pass
            
    return {'cart_count': count}