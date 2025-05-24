document.addEventListener('DOMContentLoaded', () => {
    // Tìm tất cả các form tìm kiếm trên trang
    const searchForms = document.querySelectorAll('.search-form');

    searchForms.forEach(form => {
        const input = form.querySelector('.search-input');
        const button = form.querySelector('.search-btn');

        // Kiểm tra xem các phần tử có tồn tại
        if (input && button) {
            form.addEventListener('submit', (e) => {
                e.preventDefault(); // Ngăn form submit mặc định
                const query = input.value.trim();
                if (query) {
                    // Ví dụ: Chuyển hướng đến trang sản phẩm với query
                    window.location.href = `/products?search=${encodeURIComponent(query)}`;
                    // Hoặc log giá trị để kiểm tra
                    console.log('Tìm kiếm:', query);
                }
            });

            // Tùy chọn: Thêm hiệu ứng khi click nút tìm kiếm
            button.addEventListener('click', (e) => {
                if (!input.value.trim()) {
                    e.preventDefault(); // Ngăn submit nếu input rỗng
                    input.focus(); // Tập trung vào input
                }
            });
        }
    });
});