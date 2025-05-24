document.addEventListener('DOMContentLoaded', () => {
    // Tìm tất cả các dropdown trên trang
    const dropdowns = document.querySelectorAll('.custom-dropdown');

    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.custom-toggle');
        const menu = dropdown.querySelector('.custom-menu');

        // Kiểm tra xem các phần tử có tồn tại
        if (toggle && menu) {
            // Toggle dropdown khi click vào nút
            toggle.addEventListener('click', (e) => {
                e.stopPropagation(); // Ngăn sự kiện click lan ra ngoài
                menu.classList.toggle('show');
            });

            // Đóng dropdown khi click bên ngoài
            document.addEventListener('click', (e) => {
                if (!dropdown.contains(e.target)) {
                    menu.classList.remove('show');
                }
            });
        }
    });
});