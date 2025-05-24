document.addEventListener('DOMContentLoaded', function() {
    console.log('New Chatbot JS loaded');

    // Namespace để tránh xung đột
    const CHATBOT_NS = 'xai-chatbot-';

    // Tạo nút toggle
    const toggleButton = document.createElement('button');
    toggleButton.id = CHATBOT_NS + 'toggle';
    toggleButton.style.cssText = `
        position: fixed;
        bottom: 25px;
        right: 25px;
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #1E40AF, #F472B6);
        border-radius: 50%;
        border: none;
        color: #F9FAFB;
        cursor: pointer;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2), 0 0 12px rgba(96, 165, 250, 0.3);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    `;
    toggleButton.innerHTML = '<i class="fas fa-comment" style="font-size: 1.6rem; transition: transform 0.3s ease;"></i>';
    toggleButton.addEventListener('mouseenter', () => {
        toggleButton.style.transform = 'scale(1.15)';
        toggleButton.querySelector('i').style.transform = 'rotate(360deg)';
    });
    toggleButton.addEventListener('mouseleave', () => {
        toggleButton.style.transform = 'scale(1)';
        toggleButton.querySelector('i').style.transform = 'rotate(0deg)';
    });
    document.body.appendChild(toggleButton);

    // Tạo cửa sổ chatbot
    const chatbotWindow = document.createElement('div');
    chatbotWindow.id = CHATBOT_NS + 'window';
    chatbotWindow.style.cssText = `
        position: fixed;
        bottom: 90px;
        right: 25px;
        width: 340px;
        height: 420px;
        background: #F9FAFB;
        border-radius: 16px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
        display: none;
        flex-direction: column;
        z-index: 9999;
        opacity: 0;
        transform: translateY(20px);
        transition: opacity 0.4s ease, transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        font-family: 'Inter', 'Roboto', sans-serif;
    `;

    // Tạo header
    const header = document.createElement('div');
    header.style.cssText = `
        background: linear-gradient(135deg, #1E40AF, #F472B6);
        color: #F9FAFB;
        padding: 16px;
        border-radius: 16px 16px 0 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    `;
    header.innerHTML = '<h3 style="margin: 0; font-size: 1.3rem; font-weight: 700;">TechBot</h3>';
    const closeButton = document.createElement('button');
    closeButton.style.cssText = `
        background: none;
        border: none;
        color: #F9FAFB;
        font-size: 1.1rem;
        cursor: pointer;
        transition: color 0.3s ease;
    `;
    closeButton.innerHTML = '<i class="fas fa-times"></i>';
    closeButton.addEventListener('mouseenter', () => {
        closeButton.style.color = '#F472B6';
    });
    closeButton.addEventListener('mouseleave', () => {
        closeButton.style.color = '#F9FAFB';
    });
    header.appendChild(closeButton);
    chatbotWindow.appendChild(header);

    // Tạo body (khu vực tin nhắn)
    const messages = document.createElement('div');
    messages.id = CHATBOT_NS + 'messages';
    messages.style.cssText = `
        flex: 1;
        padding: 16px;
        overflow-y: auto;
        background: #F3F4F6;
        border-radius: 0 0 16px 16px;
    `;
    chatbotWindow.appendChild(messages);

    // Tạo footer (input và nút gửi)
    const footer = document.createElement('div');
    footer.style.cssText = `
        padding: 12px 16px;
        border-top: 1px solid #D1D5DB;
        display: flex;
        align-items: center;
        background: #F9FAFB;
        border-radius: 0 0 16px 16px;
    `;
    const input = document.createElement('input');
    input.id = CHATBOT_NS + 'input';
    input.type = 'text';
    input.placeholder = 'Nhập câu hỏi của bạn...';
    input.style.cssText = `
        flex: 1;
        padding: 12px;
        border: 1px solid #D1D5DB;
        border-radius: 10px;
        font-size: 0.95rem;
        outline: none;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
        background: #FFFFFF;
    `;
    input.addEventListener('focus', () => {
        input.style.borderColor = '#1E40AF';
        input.style.boxShadow = '0 0 0 3px rgba(96, 165, 250, 0.2)';
    });
    input.addEventListener('blur', () => {
        input.style.borderColor = '#D1D5DB';
        input.style.boxShadow = 'none';
    });
    const sendButton = document.createElement('button');
    sendButton.style.cssText = `
        background: linear-gradient(135deg, #1E40AF, #F472B6);
        border: none;
        width: 44px;
        height: 44px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-left: 12px;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    `;
    sendButton.innerHTML = '<i class="fas fa-paper-plane" style="color: #F9FAFB; font-size: 1.1rem;"></i>';
    sendButton.addEventListener('mouseenter', () => {
        sendButton.style.transform = 'scale(1.1)';
        sendButton.style.boxShadow = '0 0 12px rgba(96, 165, 250, 0.3)';
    });
    sendButton.addEventListener('mouseleave', () => {
        sendButton.style.transform = 'scale(1)';
        sendButton.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.15)';
    });
    footer.appendChild(input);
    footer.appendChild(sendButton);
    chatbotWindow.appendChild(footer);

    // Thêm cửa sổ vào body
    document.body.appendChild(chatbotWindow);

    // FAQ và câu trả lời
    const faqs = {
        'xin chào': 'Xin chào! Tôi là TechBot, trợ lý ảo của TechMart. Tôi có thể giúp gì cho bạn?',
        'hello': 'Xin chào! Tôi là TechBot, trợ lý ảo của TechMart. Tôi có thể giúp gì cho bạn?',
        'hi': 'Xin chào! Tôi là TechBot, trợ lý ảo của TechMart. Tôi có thể giúp gì cho bạn?',
        'giờ mở cửa': 'TechMart mở cửa từ 8:00 sáng đến 22:00 tối tất cả các ngày trong tuần.',
        'cửa hàng': 'TechMart có cửa hàng tại TP.HCM, Hà Nội, Đà Nẵng và nhiều tỉnh thành khác.',
        'thanh toán': 'TechMart hỗ trợ tiền mặt, thẻ ATM, thẻ tín dụng, ví điện tử (MoMo, ZaloPay, VNPay), trả góp 0%.',
        'bảo hành': 'Sản phẩm tại TechMart được bảo hành chính hãng từ 12 đến 24 tháng.',
        'đổi trả': 'TechMart đổi trả trong 15 ngày với sản phẩm lỗi do nhà sản xuất.',
        'vận chuyển': 'Giao hàng miễn phí cho đơn từ 500.000đ trong 20km, thời gian 1-3 ngày.',
        'khuyến mãi': 'TechMart có khuyến mãi dịp lễ, Tết. Đăng ký email để nhận thông báo.',
        'mua hàng': 'Mua trực tiếp tại cửa hàng, online qua website hoặc hotline 1900.1234.',
        'giá cả': 'Giá tại TechMart đã bao gồm VAT, cam kết tốt nhất thị trường.',
        'trả góp': 'Hỗ trợ trả góp 0% từ 6-12 tháng tùy đối tác tài chính.',
        'tài khoản': 'Tạo tài khoản để theo dõi đơn hàng, tích điểm, nhận ưu đãi.',
        'tư vấn': 'Bạn cần tư vấn sản phẩm nào? Tôi sẽ cung cấp thông tin chi tiết.'
    };

    const quickReplies = ['Giờ mở cửa', 'Cửa hàng', 'Thanh toán', 'Bảo hành', 'Đổi trả', 'Vận chuyển'];
    const welcomeMessage = 'Xin chào! Tôi là TechBot, trợ lý ảo của TechMart. Bạn cần hỗ trợ gì?';

    // Trạng thái chatbot
    let isOpen = false;

    // Hàm mở/đóng chatbot
    function toggleChatbot(e) {
        e.preventDefault();
        e.stopPropagation();
        isOpen = !isOpen;
        chatbotWindow.style.display = isOpen ? 'flex' : 'none';
        chatbotWindow.style.opacity = isOpen ? '1' : '0';
        chatbotWindow.style.transform = isOpen ? 'translateY(0)' : 'translateY(20px)';
        if (isOpen && messages.children.length === 0) {
            addBotMessage(welcomeMessage);
            addQuickReplies(quickReplies);
        }
        console.log('Chatbot toggled:', isOpen ? 'open' : 'closed');
    }

    // Sự kiện toggle
    toggleButton.addEventListener('click', toggleChatbot);
    toggleButton.addEventListener('touchstart', toggleChatbot);
    closeButton.addEventListener('click', toggleChatbot);

    // Hàm thêm tin nhắn bot
    function addBotMessage(text) {
        const message = document.createElement('div');
        message.style.cssText = `
            background: #E0F7FA;
            padding: 12px 16px;
            border-radius: 10px;
            margin: 8px 12px;
            font-size: 0.95rem;
            text-align: left;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            animation: slideIn 0.3s ease;
            opacity: 0;
            animation-fill-mode: forwards;
        `;
        message.innerHTML = `<p>${text}</p>`;
        messages.appendChild(message);
        scrollToBottom();
    }

    // Hàm thêm tin nhắn người dùng
    function addUserMessage(text) {
        const message = document.createElement('div');
        message.style.cssText = `
            background: #C8E6C9;
            padding: 12px 16px;
            border-radius: 10px;
            margin: 8px 12px;
            font-size: 0.95rem;
            text-align: right;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            animation: slideIn 0.3s ease;
            opacity: 0;
            animation-fill-mode: forwards;
        `;
        message.innerHTML = `<p>${text}</p>`;
        messages.appendChild(message);
        scrollToBottom();
    }

    // Hàm thêm gợi ý nhanh
    function addQuickReplies(replies) {
        const container = document.createElement('div');
        container.style.cssText = 'margin: 12px; display: flex; flex-wrap: wrap; gap: 8px;';
        replies.forEach(reply => {
            const button = document.createElement('button');
            button.style.cssText = `
                padding: 8px 16px;
                background: linear-gradient(135deg, #60A5FA, #F472B6);
                color: #F9FAFB;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 0.9rem;
                font-weight: 500;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            `;
            button.textContent = reply;
            button.addEventListener('mouseenter', () => {
                button.style.transform = 'translateY(-2px)';
                button.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.15)';
            });
            button.addEventListener('mouseleave', () => {
                button.style.transform = 'translateY(0)';
                button.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
            });
            button.addEventListener('click', () => {
                addUserMessage(reply);
                showBotTyping();
                setTimeout(() => {
                    hideBotTyping();
                    respondToMessage(reply);
                }, 1000);
            });
            container.appendChild(button);
        });
        messages.appendChild(container);
        scrollToBottom();
    }

    // Hàm hiển thị hiệu ứng đang gõ
    function showBotTyping() {
        const typing = document.createElement('div');
        typing.id = CHATBOT_NS + 'typing';
        typing.style.cssText = 'margin: 12px;';
        typing.innerHTML = `
            <div style="display: inline-block; width: 10px; height: 10px; background: #1E40AF; border-radius: 50%; margin-right: 6px; animation: blink 1.2s infinite;"></div>
            <div style="display: inline-block; width: 10px; height: 10px; background: #1E40AF; border-radius: 50%; margin-right: 6px; animation: blink 1.2s infinite 0.2s;"></div>
            <div style="display: inline-block; width: 10px; height: 10px; background: #1E40AF; border-radius: 50%; animation: blink 1.2s infinite 0.4s;"></div>
        `;
        messages.appendChild(typing);
        scrollToBottom();
    }

    // Hàm ẩn hiệu ứng đang gõ
    function hideBotTyping() {
        const typing = document.getElementById(CHATBOT_NS + 'typing');
        if (typing) typing.remove();
    }

    // Hàm xử lý tin nhắn
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
            addBotMessage('Xin lỗi, tôi không hiểu câu hỏi của bạn. Bạn có thể thử hỏi theo cách khác hoặc chọn một gợi ý:');
            addQuickReplies(quickReplies);
        }
    }

    // Hàm cuộn xuống cuối
    function scrollToBottom() {
        messages.scrollTop = messages.scrollHeight;
    }

    // Xử lý gửi tin nhắn
    function sendMessage(e) {
        e.preventDefault();
        const message = input.value.trim();
        if (message) {
            addUserMessage(message);
            input.value = '';
            showBotTyping();
            setTimeout(() => {
                hideBotTyping();
                respondToMessage(message);
            }, 1000);
        }
    }

    sendButton.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage(e);
    });

    // Keyframe cho hiệu ứng
    const style = document.createElement('style');
    style.textContent = `
        @keyframes blink {
            50% { opacity: 0.2; }
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
    `;
    document.head.appendChild(style);
});