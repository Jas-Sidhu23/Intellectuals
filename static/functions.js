const socket = io.connect('http://' + document.domain + ':' + location.port);

document.addEventListener("DOMContentLoaded", function() {
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
    updateDateTime();
});

function submitMessage() {
    const messageInput = document.querySelector('input[name="message"]');
    const imageInput = document.querySelector('input[name="image"]');
    const message = messageInput.value;
    const image = imageInput.files[0];

    if (!message.trim() && !image) {
        alert('Please enter a message or select an image.');
        return;
    }

    const formData = new FormData();
    formData.append('message', message);
    if (image) {
        formData.append('image', image);
    }

    // Emit the message event to the server with the form data
    socket.emit('message', formData);

    // Clear the input fields
    messageInput.value = '';
    if (imageInput) {
        imageInput.value = '';
    }
}

// Listen for server responses
socket.on('message_success', function(data) {
    alert(data.message);
});

socket.on('message_error', function(data) {
    alert(data.error);
});