const logoutBtn = document.getElementById("user-profile-btn");
const chatArea = document.getElementById('chat-area');
const queryInput = document.getElementById('query-input');
const sendBtn = document.getElementById('send-btn');
const schemaSelect = document.getElementById('schema-select');

const API_ENDPOINT = "http://localhost:8000/api/generate-sql";

logoutBtn.addEventListener('click', function (e) {
    const isConfirmed = confirm("Bạn có muốn đăng xuất khỏi hệ thống không?");
    if (isConfirmed) {
        window.location.href = "logout/";
    }
});

function appendMessage(sender, content, contentType = 'text') {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);

    const senderDiv = document.createElement('div');
    senderDiv.classList.add('message-sender');
    senderDiv.textContent = sender === 'user' ? 'USER' : 'BOT';

    const bubbleDiv = document.createElement('div');
    bubbleDiv.classList.add('message-bubble');

    if (contentType === 'code') {
        const pre = document.createElement('pre');
        const code = document.createElement('code');
        code.textContent = content;
        pre.appendChild(code);
        bubbleDiv.appendChild(pre);

    } else if (contentType === 'table') {

        // Kiểm tra nếu dữ liệu không phải là mảng (vd: thông báo lỗi)
        if (!Array.isArray(content)) {
            bubbleDiv.textContent = content || "Không có dữ liệu trả về.";
        }
        // Kiểm tra nếu mảng rỗng (truy vấn thành công nhưng ko có row nào)
        else if (content.length === 0) {
            bubbleDiv.textContent = "Truy vấn thành công nhưng không có dữ liệu (0 rows).";
        }
        else {
            const tableWrapper = document.createElement('div');
            tableWrapper.className = 'table-wrapper';
            const table = document.createElement('table');
            table.className = 'message-table';

            const thead = document.createElement('thead');
            const tbody = document.createElement('tbody');
            const headerRow = document.createElement('tr');

            // TH1: Dữ liệu là mảng các Object/Dict (Ví dụ: [{"id": 1, "name": "A"}])
            if (typeof content[0] === 'object' && !Array.isArray(content[0]) && content[0] !== null) {
                // Trích xuất Header từ các keys của Object đầu tiên
                Object.keys(content[0]).forEach(key => {
                    const th = document.createElement('th');
                    th.textContent = key;
                    headerRow.appendChild(th);
                });
                thead.appendChild(headerRow);

                // Đổ dữ liệu vào các hàng
                content.forEach(rowItem => {
                    const tr = document.createElement('tr');
                    Object.values(rowItem).forEach(val => {
                        const td = document.createElement('td');
                        td.textContent = val !== null ? val : 'NULL';
                        tr.appendChild(td);
                    });
                    tbody.appendChild(tr);
                });
            }
            // TH2: Dữ liệu là mảng của các mảng/tuples (Ví dụ: [[1, "A"], [2, "B"]]) - fetchall() thuần
            else if (Array.isArray(content[0])) {
                // Sinh header giả vì tuple không chứa tên cột
                content[0].forEach((_, index) => {
                    const th = document.createElement('th');
                    th.textContent = `Cột ${index + 1}`;
                    headerRow.appendChild(th);
                });
                thead.appendChild(headerRow);

                // Đổ dữ liệu
                content.forEach(rowItem => {
                    const tr = document.createElement('tr');
                    rowItem.forEach(val => {
                        const td = document.createElement('td');
                        td.textContent = val !== null ? val : 'NULL';
                        tr.appendChild(td);
                    });
                    tbody.appendChild(tr);
                });
            }
            else {
                // TH3: Mảng phẳng (ít gặp)
                bubbleDiv.textContent = JSON.stringify(content);
                messageDiv.appendChild(senderDiv);
                messageDiv.appendChild(bubbleDiv);
                chatArea.appendChild(messageDiv);
                scrollToBottom();
                return;
            }

            table.appendChild(thead);
            table.appendChild(tbody);
            tableWrapper.appendChild(table);
            bubbleDiv.appendChild(tableWrapper);
        }
    } else {
        bubbleDiv.textContent = content;
    }

    messageDiv.appendChild(senderDiv);
    messageDiv.appendChild(bubbleDiv);
    chatArea.appendChild(messageDiv);

    // Cuộn xuống cuối cùng
    scrollToBottom();
}

function appendTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'bot');
    messageDiv.id = 'typing-indicator';

    const senderDiv = document.createElement('div');
    senderDiv.classList.add('message-sender');
    senderDiv.textContent = 'BOT';

    const bubbleDiv = document.createElement('div');
    bubbleDiv.classList.add('message-bubble');
    bubbleDiv.innerHTML = `
        <div class="typing-indicator">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    `;

    messageDiv.appendChild(senderDiv);
    messageDiv.appendChild(bubbleDiv);
    chatArea.appendChild(messageDiv);
    scrollToBottom();
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

function scrollToBottom() {
    chatArea.scrollTop = chatArea.scrollHeight;
}

async function handleSend() {
    const query = queryInput.value.trim();
    if (!query) return;

    const topKValue = parseInt(schemaSelect.value, 10);

    appendMessage('user', query);
    queryInput.value = '';

    appendTypingIndicator();

    try {
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: query, topK: topKValue })
        });

        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        const sqlQuery = data.sql_query;
        const results = data.results;

        removeTypingIndicator();

        appendMessage('bot', sqlQuery, 'code');

        if (results !== undefined && results !== null) {
            appendMessage('bot', results, 'table');
        }

    } catch (error) {
        console.error('Error fetching SQL:', error);
        removeTypingIndicator();
        appendMessage('bot', '-- Lỗi kết nối đến máy chủ LLM. Vui lòng kiểm tra lại API Endpoint.', 'text');
    }
}

sendBtn.addEventListener('click', handleSend);

queryInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        handleSend();
    }
});
