document.addEventListener("DOMContentLoaded", function() {
    // Function to retrieve a cookie value by its name
    function getCookie(name) {
        var value = `; ${document.cookie}`;
        var parts = value.split(`; ${name}=`);
        if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
        return null;
    }

    // Get the authentication token from cookies
    var authToken = getCookie('auth_token');
    if (!authToken) {
        console.error("Authentication token not found or not accessible.");
        return;  // Stop further execution if no token is found
    }

    // Connect to the WebSocket server with the authentication token
    var socket = io({ query: { token: authToken } });

    socket.on('connect', function() {
        console.log('Connected to the WebSocket server.');
    });

    socket.on('connection_response', function(data) {
        console.log(data.message);  // Display a connection response message from the server
    });

    // Handle button click to send new messages
    document.getElementById('sendMessageButton').addEventListener('click', function() {
        var messageInput = document.querySelector('[name="message"]');
        if (messageInput.value.trim()) {
            socket.emit('post_message', {
                username: 'YourUsername',  // This should be dynamically assigned
                message: messageInput.value
            });
            messageInput.value = '';  // Clear the input after sending
        }
    });

    // Listen for new messages from the server
    socket.on('new_message', function(data) {
        console.log('New message received:', data);
        var messagesContainer = document.getElementById('messagesContainer'); // Target the messages container
        var newMessageElement = document.createElement('div');
        newMessageElement.classList.add('message');
        newMessageElement.innerHTML = `
            <p>-----------------------------------</p>
            <p>Post User: ${data.username}</p>
            <h2>${data.message}</h2>
        `;
        // Add reply form
        var replyForm = document.createElement('form');
        var replyLabel = document.createElement('label');
        replyLabel.textContent = 'Make a reply to message:';
        var replyInput = document.createElement('input');
        replyInput.setAttribute('type', 'text');
        replyInput.setAttribute('placeholder', 'Type your message');
        replyInput.setAttribute('name', 'message');
        var msgIdInput = document.createElement('input');
        msgIdInput.setAttribute('type', 'text');
        msgIdInput.setAttribute('name', 'msg_id');
        msgIdInput.setAttribute('value', data._id);
        msgIdInput.setAttribute('hidden', 'true');
        var replyButton = document.createElement('button');
        replyButton.setAttribute('type', 'button');
        replyButton.classList.add('sendReplyButton');
        replyButton.textContent = 'Reply';

        replyForm.appendChild(replyLabel);
        replyForm.appendChild(document.createElement('br'));
        replyForm.appendChild(replyInput);
        replyForm.appendChild(msgIdInput);
        replyForm.appendChild(replyButton);

        newMessageElement.appendChild(replyForm);
        messagesContainer.appendChild(newMessageElement);
    });

    // Handle button clicks to send replies
    document.querySelectorAll('.sendReplyButton').forEach(button => {
        button.addEventListener('click', function(event) {
            var form = event.target.closest('form');
            var messageInput = form.querySelector('[name="message"]');
            var messageIdInput = form.querySelector('[name="msg_id"]');
            if (messageInput.value.trim() && messageIdInput.value) { // Check if messageIdInput has value
                socket.emit('send_reply', {
                    username: 'YourUsername',  // This should be dynamically assigned
                    message: messageInput.value,
                    chat_id: messageIdInput.value // Include the chat_id field
                });
                messageInput.value = '';  // Clear the input after sending
            }
        });
    });

// Listen for replies posted to the server
socket.on('reply_posted', function(data) {
    console.log('Reply posted:', data);
    // Find the message container with the corresponding message ID
    var messageContainers = document.querySelectorAll(`[data-msg-id="${data.chat_id}"]`);
    messageContainers.forEach(function(messageContainer) {
        // If the message container exists, find the replies container within it
        var repliesContainer = messageContainer.querySelector('.repliesContainer');
        if (repliesContainer) {
            // Create a new reply element
            var newReplyElement = document.createElement('div');
            newReplyElement.classList.add('reply');
            newReplyElement.innerHTML = `
                <p>Reply User: ${data.username}</p>
                <h2>${data.message}</h2>
            `;
            // Append the new reply element to the replies container
            repliesContainer.appendChild(newReplyElement);
        } else {
            console.error('Replies container not found in the message container.');
        }
    });
});





    // Handle WebSocket errors
    socket.on('error', function(error) {
        console.error('WebSocket Error:', error);
    });

    // Handle connection errors
    socket.on('connect_error', function(error) {
        console.error('Connection Error:', error);
    });

    // Display current date and time on the page
    const dateElement = document.createElement("div");
    dateElement.id = "current-date";
    dateElement.style.textAlign = "right";
    dateElement.style.margin = "10px";
    document.body.prepend(dateElement);

    function updateDateTime() {
        const now = new Date();
        dateElement.textContent = now.toLocaleString();
    }

    setInterval(updateDateTime, 1000);
});
