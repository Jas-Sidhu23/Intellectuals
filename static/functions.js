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
        var messagesContainer = document.getElementById('messagesContainer'); // Assuming you have this element in your HTML
        var newMessageElement = document.createElement('div');
        newMessageElement.textContent = data.username + ": " + data.message; // Display the username and message
        messagesContainer.appendChild(newMessageElement);
    });

    // Handle button clicks to send replies
    document.getElementById('sendReplyButton').addEventListener('click', function(event) {
        button.addEventListener('click', function(event) {
            var form = event.target.closest('form');
            var messageInput = form.querySelector('[name="message"]');
            var messageIdInput = form.querySelector('[name="msg_id"]');
            if (messageInput.value.trim()) {
                socket.emit('send_reply', {
                    message: messageInput.value,
                    msg_id: messageIdInput.value
                });
                messageInput.value = '';  // Clear the input after sending
            }
        });
    });

    // Listen for replies posted to the server
    socket.on('reply_posted', function(data) {
        console.log('Reply posted:', data);
        // Add code here to append the reply to the appropriate message on the webpage
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