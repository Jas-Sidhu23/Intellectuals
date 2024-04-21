document.addEventListener("DOMContentLoaded", function() {
    function getCookie(name) {
        var value = `; ${document.cookie}`;
        var parts = value.split(`; ${name}=`);
        if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
        return null;
    }

    var authToken = getCookie('auth_token');
    if (!authToken) {
        console.error("Authentication token not found or not accessible.");
        return;
    }

    var socket = io({ query: { token: authToken } });
    var currentUser;

    socket.on('connect', function() {
        console.log('Connected to the WebSocket server.');
    });

    socket.on('connection_response', function(data) {
        console.log(data.message);
        if (data.username) {
            currentUser = data.username; // Save the username for later use
        }
    });

    document.getElementById('sendMessageButton').addEventListener('click', function() {
        var messageInput = document.querySelector('[name="message"]');
        var imageInput = document.querySelector('[name="image"]'); // Assuming you have an input field for the image
        var file = imageInput.files[0]; // Get the first file from the input
    
        if (messageInput.value.trim() || file) { // Check if there's a message or an image
            var reader = new FileReader();
            reader.onloadend = function() {
                socket.emit('post_message', {
                    username: 'YourUsername', // This should be dynamically assigned
                    message: messageInput.value,
                    image: {
                        filename: file.name,
                        content: reader.result
                    }
                });
                messageInput.value = ''; // Clear the input after sending
            }
            if (file) {
                reader.readAsArrayBuffer(file); // Read the file as an ArrayBuffer
            } else {
                socket.emit('post_message', {
                    username: 'YourUsername', // This should be dynamically assigned
                    message: messageInput.value
                });
                messageInput.value = ''; // Clear the input after sending
            }
        }
    });

    socket.on('new_message', function(data) {
        console.log('New message received:', data);
        var messagesContainer = document.getElementById('messagesContainer');
        var newMessageElement = document.createElement('div');
        newMessageElement.classList.add('message');
        
        newMessageElement.innerHTML = `
            <p>-----------------------------------</p>
            <p>Post User: ${data.username}</p>
            <h2>${data.message}</h2>
            <div class="repliesContainer"></div>
            <form>
                <label>Make a reply to message:</label>
                <br>
                <input type="text" placeholder="Type your message" name="message">
                <input type="hidden" name="msg_id" value="${data._id}">
                <button type="button" class="sendReplyButton">Reply</button>
            </form>
        `;

        if (data.image_path) {
            // Construct the URL for the image
            var imageUrl = '/static/' + data.image_path;
            // Add the image to the message HTML
            messageHtml += `<img src="${imageUrl}" alt="Uploaded image">`;
        }

        messagesContainer.appendChild(newMessageElement);
    });

    // Event delegation for dynamically created reply buttons
    document.body.addEventListener('click', function(event) {
        if (event.target.classList.contains('sendReplyButton')) {
            var form = event.target.closest('form');
            var messageInput = form.querySelector('[name="message"]');
            var messageIdInput = form.querySelector('[name="msg_id"]');
            if (messageInput.value.trim()) {
                socket.emit('send_reply', {
                    username: currentUser,  // Ensure this variable is correctly maintained and available
                    message: messageInput.value,
                    chat_id: messageIdInput.value
                });
                messageInput.value = '';
            }
        }
    });
    

    socket.on('reply_posted', function(data) {
        console.log('Reply posted:', data);
        var messageContainer = document.querySelector(`[data-msg-id="${data.chat_id}"] .repliesContainer`);
        if (messageContainer) {
            var replyDiv = document.createElement('div');
            replyDiv.classList.add('reply');
            replyDiv.innerHTML = `
                <p>Reply User: ${data.username}</p>
                <h2>${data.message}</h2>
            `;
            messageContainer.appendChild(replyDiv);
        } else {
            console.error('Replies container not found for message ID:', data.chat_id);
        }
    });

    document.querySelectorAll('.sendReplyButton').forEach(button => {
        button.addEventListener('click', function(event) {
            var form = event.target.closest('form');
            var messageInput = form.querySelector('[name="message"]');
            var messageIdInput = form.querySelector('[name="msg_id"]');
            if (messageInput.value.trim() && messageIdInput.value) {
                // You need to ensure that `username` is correctly defined and passed here
                socket.emit('send_reply', {
                    username: 'ActualUsername',  // Replace 'ActualUsername' with the actual username or retrieve it from an appropriate source
                    message: messageInput.value,
                    chat_id: messageIdInput.value
                });
                messageInput.value = '';  // Clear the input after sending
            }
        });
    });

    socket.on('error', function(error) {
        console.error('WebSocket Error:', error);
    });

    socket.on('connect_error', function(error) {
        console.error('Connection Error:', error);
    });

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
