/**
 * TechMart - Main JavaScript File
 */

// Sử dụng Strict Mode
'use strict';

// DOM Elements
const menuToggle = document.getElementById('menu-toggle');
const closeMenu = document.getElementById('close-menu');
const navLinks = document.getElementById('nav-links');
const quantityInputs = document.querySelectorAll('.quantity-input input');
const flashMessages = document.querySelectorAll('.alert');
const productGallery = document.querySelectorAll('.product-gallery-item');
const productFilters = document.querySelectorAll('.product-filter input');

// Toggle Mobile Menu
if (menuToggle) {
    menuToggle.addEventListener('click', () => {
        navLinks.classList.add('active');
        document.body.style.overflow = 'hidden';
    });
}

if (closeMenu) {
    closeMenu.addEventListener('click', () => {
        navLinks.classList.remove('active');
        document.body.style.overflow = 'auto';
    });
}

// Auto-dismiss Flash Messages
flashMessages.forEach(message => {
    setTimeout(() => {
        message.style.opacity = '0';
        setTimeout(() => {
            message.style.display = 'none';
        }, 500);
    }, 5000);
});

// Quantity Input Controls
if (quantityInputs) {
    quantityInputs.forEach(input => {
        const decreaseBtn = input.previousElementSibling;
        const increaseBtn = input.nextElementSibling;

        if (decreaseBtn) {
            decreaseBtn.addEventListener('click', () => {
                let value = parseInt(input.value);
                if (value > 1) {
                    input.value = value - 1;
                }
            });
        }

        if (increaseBtn) {
            increaseBtn.addEventListener('click', () => {
                let value = parseInt(input.value);
                input.value = value + 1;
            });
        }

        // Validate manually entered values
        input.addEventListener('change', () => {
            let value = parseInt(input.value);
            if (isNaN(value) || value < 1) {
                input.value = 1;
            }
        });
    });
}

// Product Gallery
if (productGallery.length > 0) {
    productGallery.forEach(item => {
        item.addEventListener('click', () => {
            const mainImg = document.querySelector('.product-detail-image');
            const imgSrc = item.getAttribute('data-src');

            // Thay đổi ảnh chính
            mainImg.src = imgSrc;

            // Loại bỏ class active từ tất cả các item
            productGallery.forEach(i => i.classList.remove('active'));

            // Thêm class active cho item được chọn
            item.classList.add('active');
        });
    });
}

// Auto-submit filter form when inputs change
if (productFilters.length > 0) {
    productFilters.forEach(filter => {
        filter.addEventListener('change', () => {
            const filterForm = document.getElementById('filter-form');
            if (filterForm) {
                filterForm.submit();
            }
        });
    });
}

// Price range slider (if present)
const priceRange = document.getElementById('price-range');
const minPriceDisplay = document.getElementById('min-price-display');
const maxPriceDisplay = document.getElementById('max-price-display');
const minPriceInput = document.getElementById('min-price');
const maxPriceInput = document.getElementById('max-price');

if (priceRange && minPriceDisplay && maxPriceDisplay && minPriceInput && maxPriceInput) {
    const rangeMin = parseInt(priceRange.getAttribute('data-min'));
    const rangeMax = parseInt(priceRange.getAttribute('data-max'));

    // Hàm định dạng số tiền
    const formatCurrency = (value) => {
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND',
            maximumFractionDigits: 0
        }).format(value);
    };

    // Khởi tạo noUiSlider
    if (typeof noUiSlider !== 'undefined') {
        noUiSlider.create(priceRange, {
            start: [
                minPriceInput.value ? parseInt(minPriceInput.value) : rangeMin,
                maxPriceInput.value ? parseInt(maxPriceInput.value) : rangeMax
            ],
            connect: true,
            step: 100000,
            range: {
                'min': rangeMin,
                'max': rangeMax
            }
        });

        // Cập nhật giá trị hiển thị và input khi slider thay đổi
        priceRange.noUiSlider.on('update', (values, handle) => {
            const value = parseInt(values[handle]);

            if (handle === 0) {
                minPriceDisplay.textContent = formatCurrency(value);
                minPriceInput.value = value;
            } else {
                maxPriceDisplay.textContent = formatCurrency(value);
                maxPriceInput.value = value;
            }
        });
    }
}

// Xử lý phần thanh toán
const paymentMethodInputs = document.querySelectorAll('input[name="payment_method"]');
const paymentDetails = document.querySelectorAll('.payment-details');

if (paymentMethodInputs.length > 0 && paymentDetails.length > 0) {
    paymentMethodInputs.forEach(input => {
        input.addEventListener('change', () => {
            const selectedMethod = input.value;

            // Ẩn tất cả các chi tiết thanh toán
            paymentDetails.forEach(detail => {
                detail.style.display = 'none';
            });

            // Hiển thị chi tiết thanh toán được chọn
            const selectedDetails = document.getElementById(`${selectedMethod}-details`);
            if (selectedDetails) {
                selectedDetails.style.display = 'block';
            }
        });
    });
}