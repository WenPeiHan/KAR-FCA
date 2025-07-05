document.getElementById('sendButton').addEventListener('click', function(event) {
    event.preventDefault();
    const query = document.getElementById('queryInput').value;
    if (query.trim() === '') return;

    // 清空输入框
    document.getElementById('queryInput').value = '';

    const chatHistory = document.getElementById('chatHistory');

    // 添加用户气泡
    const userMessage = document.createElement('div');
    userMessage.className = 'chat-bubble user-bubble';
    userMessage.textContent = query;
    chatHistory.appendChild(userMessage);

    // 滚动到底部（确保用户输入后立即滚到底）
    setTimeout(() => {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }, 100);

    // 向后端发送请求
    fetch('/ask', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: query })
    })
    .then(response => response.json())
    .then(data => {
        // 添加 AI 气泡
        const aiMessage = document.createElement('div');
        aiMessage.className = 'chat-bubble ai-bubble';

        // 使用 marked 解析 markdown
        const htmlContent = marked.parse(data.response);
        aiMessage.innerHTML = htmlContent;
        chatHistory.appendChild(aiMessage);

        // 延迟滚动到底部，确保 DOM 渲染完成后滚动
        setTimeout(() => {
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }, 100);
    })
    .catch(error => console.error('Error:', error));
});
