// 1. CHỨC NĂNG ĐĂNG XUẤT
document.getElementById('user-profile-btn').addEventListener('click', function () {
    if (confirm("Bạn có muốn đăng xuất khỏi hệ thống quản trị không?")) {
        window.location.href = "/logout/";
    }
});

// 2. KIỂM TRA MẬT KHẨU TRƯỚC KHI SUBMIT FORM
const addUserForm = document.getElementById('add-user-form');
const passwordInput = document.getElementById('password');
const confirmPasswordInput = document.getElementById('confirm_password');
const passwordError = document.getElementById('password-error');

if (addUserForm) {
    addUserForm.addEventListener('submit', function (e) {
        // Nếu mật khẩu không khớp nhau
        if (passwordInput.value !== confirmPasswordInput.value) {
            e.preventDefault(); // Ngăn trình duyệt gửi form về Django

            // Hiển thị dòng cảnh báo màu đỏ
            passwordError.style.display = 'block';
            // Tô đỏ viền ô "Xác nhận mật khẩu"
            confirmPasswordInput.classList.add('input-error');
            // Đưa con trỏ chuột về lại ô xác nhận để người dùng gõ lại
            confirmPasswordInput.focus();
        }
    });

    // Tự động tắt cảnh báo đỏ khi người dùng bắt đầu sửa lại mật khẩu ở 1 trong 2 ô
    function clearError() {
        passwordError.style.display = 'none';
        confirmPasswordInput.classList.remove('input-error');
    }
    passwordInput.addEventListener('input', clearError);
    confirmPasswordInput.addEventListener('input', clearError);
}

// 3. CHỨC NĂNG XÓA USER
function deleteUser(userId, username) {
    const isConfirmed = confirm(`CẢNH BÁO: Bạn có chắc chắn muốn xóa nhân viên [ ${username} ] ra khỏi cơ sở dữ liệu không? Hành động này không thể hoàn tác.`);

    if (isConfirmed) {
        fetch(`/api/delete-user/${userId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                const row = document.getElementById(`user-row-${userId}`);
                if (row) {
                    row.style.transition = "opacity 0.3s";
                    row.style.opacity = "0";
                    setTimeout(() => row.remove(), 300);
                }
            } else {
                alert("Có lỗi xảy ra từ máy chủ, không thể xóa user.");
            }
        })
        .catch(error => {
            console.error('Lỗi:', error);
            // Dành cho test giao diện:
            const row = document.getElementById(`user-row-${userId}`);
            row.style.opacity = "0";
            setTimeout(() => row.remove(), 300);
        });
    }
}
