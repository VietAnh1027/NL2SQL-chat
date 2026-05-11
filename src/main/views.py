from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

@login_required
def chat_screen(request):
    
    # ==========================================
    # 1. LUỒNG DÀNH CHO QUẢN TRỊ VIÊN (SUPERUSER)
    # ==========================================
    if request.user.is_superuser:
        
        # Xử lý khi Admin nhấn nút "+ Thêm Nhân Viên" (Gửi form POST)
        if request.method == 'POST':
            emp_id = request.POST.get('username')
            password = request.POST.get('password')
            role = request.POST.get('is_superuser') == 'True'
            
            # Kiểm tra xem mã nhân viên (username) đã tồn tại chưa
            if User.objects.filter(username=emp_id).exists():
                messages.error(request, f"Lỗi: Mã nhân viên [{emp_id}] đã tồn tại trong hệ thống!")
            else:
                try:
                    # Tạo user mới
                    new_user = User.objects.create_user(username=emp_id, password=password)
                    new_user.is_superuser = role
                    new_user.save()
                    messages.success(request, f"Đã cấp tài khoản thành công cho: {emp_id}")
                except Exception as e:
                    messages.error(request, f"Lỗi hệ thống: {str(e)}")
            
            # Chuyển hướng lại chính trang này để tránh lỗi gửi lại form khi F5 (Resubmission)
            # Lưu ý: Thay 'chat_screen' bằng thuộc tính 'name' của URL path này trong urls.py của bạn
            return redirect('chat_screen') 

        # Xử lý khi Admin chỉ load trang (Method GET)
        # Quét DB lấy danh sách user, sắp xếp người mới tạo lên đầu
        users = User.objects.all().order_by('-id') 
        
        # Render ra trang Admin kèm dữ liệu
        return render(request, "admin_dashboard.html", {
            "userName": request.user.username,
            "users_list": users
        })

    # ==========================================
    # 2. LUỒNG DÀNH CHO NHÂN VIÊN THƯỜNG (USER)
    # ==========================================
    else:
        # Giữ nguyên như code cũ của bạn
        return render(request, "chat.html", {"userName": request.user.username})
    
from django.http import JsonResponse
import json

@login_required
def delete_user_api(request, user_id):
    # Chỉ cho phép Admin và method POST được xóa
    if request.method == 'POST' and request.user.is_superuser:
        try:
            user_to_delete = User.objects.get(id=user_id)
            # Ngăn không cho admin tự xóa chính mình
            if user_to_delete.id != request.user.id:
                user_to_delete.delete()
                return JsonResponse({"status": "success"})
            else:
                return JsonResponse({"status": "error", "message": "Cannot delete self"}, status=403)
        except User.DoesNotExist:
            return JsonResponse({"status": "error", "message": "User not found"}, status=404)
            
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)