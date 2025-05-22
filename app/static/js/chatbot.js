// Chatbot functionality
document.addEventListener('DOMContentLoaded', function() {
    const chatbotButton = document.getElementById('chatbot-button');
    const chatbotWindow = document.getElementById('chatbot-window');
    const chatbotClose = document.getElementById('chatbot-close');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');


    // Khai báo các câu hỏi và trả lời thường gặp
    const faqs = {
        'xin chào': 'Xin chào! Tôi là TechBot, trợ lý ảo của TechMart. Tôi có thể giúp gì cho bạn?',
        'hello': 'Xin chào! Tôi là TechBot, trợ lý ảo của TechMart. Tôi có thể giúp gì cho bạn?',
        'hi': 'Xin chào! Tôi là TechBot, trợ lý ảo của TechMart. Tôi có thể giúp gì cho bạn?',
        'giờ mở cửa': 'TechMart mở cửa từ 8:00 sáng đến 22:00 tối tất cả các ngày trong tuần, kể cả cuối tuần và ngày lễ.',
        'cửa hàng': 'TechMart có cửa hàng tại TP.HCM, Hà Nội, Đà Nẵng và nhiều tỉnh thành khác. Bạn có thể xem danh sách đầy đủ tại mục "Hệ thống cửa hàng" trên website của chúng tôi.',
        'thanh toán': 'TechMart hỗ trợ nhiều phương thức thanh toán: Tiền mặt, thẻ ATM nội địa, thẻ tín dụng/ghi nợ, chuyển khoản ngân hàng, ví điện tử (MoMo, ZaloPay, VNPay), và trả góp 0%.',
        'bảo hành': 'Các sản phẩm tại TechMart đều được bảo hành chính hãng từ 12 đến 24 tháng tùy loại sản phẩm. Bạn có thể mang sản phẩm đến bất kỳ cửa hàng TechMart nào để được hỗ trợ.',
        'đổi trả': 'TechMart áp dụng chính sách đổi trả trong vòng 15 ngày với các sản phẩm lỗi do nhà sản xuất. Sản phẩm đổi trả phải còn nguyên vẹn, đầy đủ phụ kiện và hộp sản phẩm.',
        'vận chuyển': 'TechMart giao hàng miễn phí cho đơn hàng từ 500.000đ trở lên trong phạm vi 20km. Thời gian giao hàng thông thường là 1-3 ngày tùy khu vực.',
        'khuyến mãi': 'TechMart thường xuyên có các chương trình khuyến mãi vào dịp lễ, Tết và sinh nhật cửa hàng. Bạn có thể đăng ký nhận thông báo email để cập nhật các khuyến mãi mới nhất.',
        'mua hàng': 'Bạn có thể mua hàng trực tiếp tại cửa hàng, đặt mua online qua website hoặc gọi điện thoại đến hotline 1900.1234 để được tư vấn và đặt hàng.',
        'giá cả': 'Giá sản phẩm tại TechMart đã bao gồm VAT. Chúng tôi cam kết giá tốt nhất thị trường và có chính sách đảm bảo giá.',
        'trả góp': 'TechMart hỗ trợ mua trả góp với lãi suất 0% cho nhiều sản phẩm. Thời gian trả góp từ 6-12 tháng tùy đối tác tài chính.',
        'tài khoản': 'Bạn có thể tạo tài khoản tại TechMart để theo dõi đơn hàng, tích điểm thành viên và nhận các ưu đãi đặc biệt.',
        'tư vấn': 'Vui lòng cho tôi biết bạn cần tư vấn về sản phẩm nào? Tôi sẽ cung cấp thông tin chi tiết hoặc chuyển yêu cầu của bạn đến nhân viên tư vấn.'
    };

    // Các gợi ý câu hỏi nhanh
    const quickReplies = [
        'Giờ mở cửa',
        'Cửa hàng',
        'Thanh toán',
        'Bảo hành',
        'Đổi trả',
        'Vận chuyển'
    ];

    // Tin nhắn chào mừng
    const welcomeMessage = 'Xin chào! Tôi là TechBot, trợ lý ảo của TechMart. Tôi có thể giúp bạn trả lời các câu hỏi về sản phẩm, dịch vụ, chính sách và nhiều thông tin khác. Bạn cần hỗ trợ gì?';

    // Mở cửa sổ chat
    chatbotButton.addEventListener('click', function() {
        chatbotWindow.classList.add('active'); // Chỉ thêm lớp active
        chatbotButton.style.display = 'none';   // Ẩn nút chatbot

        if (chatbotMessages.children.length === 0) {
            addBotMessage(welcomeMessage);
            addQuickReplies(quickReplies);
        }
    });

    // Đóng cửa sổ chat
    chatbotClose.addEventListener('click', function() {
        chatbotWindow.classList.remove('active'); // Xóa lớp active
        chatbotButton.style.display = 'flex';     // Hiển thị lại nút chatbot
    });

    // Xử lý gửi tin nhắn
    function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            addUserMessage(message);
            messageInput.value = '';
            showBotTyping();
            setTimeout(() => {
                hideBotTyping();
                respondToMessage(message);
            }, 1000);
        }
    }

    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendMessage();
    });

    function addBotMessage(text) {
        const message = document.createElement('div');
        message.className = 'message bot-message';
        message.textContent = text;
        chatbotMessages.appendChild(message);
        scrollToBottom();
    }

    function addUserMessage(text) {
        const message = document.createElement('div');
        message.className = 'message user-message';
        message.textContent = text;
        chatbotMessages.appendChild(message);
        scrollToBottom();
    }

    function showBotTyping() {
        const typing = document.createElement('div');
        typing.className = 'bot-typing';
        typing.id = 'bot-typing';
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            typing.appendChild(dot);
        }
        chatbotMessages.appendChild(typing);
        scrollToBottom();
    }

    function hideBotTyping() {
        const typing = document.getElementById('bot-typing');
        if (typing) typing.remove();
    }

    function addQuickReplies(replies) {
        const container = document.createElement('div');
        container.className = 'quick-replies';
        replies.forEach(reply => {
            const button = document.createElement('button');
            button.className = 'quick-reply';
            button.textContent = reply;
            button.addEventListener('click', function() {
                addUserMessage(reply);
                showBotTyping();
                setTimeout(() => {
                    hideBotTyping();
                    respondToMessage(reply);
                }, 1000);
            });
            container.appendChild(button);
        });
        chatbotMessages.appendChild(container);
        scrollToBottom();
    }

    function respondToMessage(message) {
        const lowerMessage = message.toLowerCase();
        let responded = false;
        for (const [keyword, response] of Object.entries(faqs)) {
            if (lowerMessage.includes(keyword.toLowerCase())) {
                addBotMessage(response);
                responded = true;
                break;
            }
        }
        if (!responded) {
            addBotMessage('Xin lỗi, tôi không hiểu câu hỏi của bạn. Bạn có thể thử hỏi theo cách khác hoặc chọn một trong các câu hỏi gợi ý dưới đây:');
            addQuickReplies(quickReplies);
        }
    }

    function scrollToBottom() {
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }
});