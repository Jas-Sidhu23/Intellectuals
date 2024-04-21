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