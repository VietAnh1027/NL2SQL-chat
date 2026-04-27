from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout_view(request):
    logout(request)
    return redirect('login') # Chuyển hướng về trang đăng nhập của bạn