//static/js/time.js
document.addEventListener("DOMContentLoaded", function() {
    const timeElements = document.querySelectorAll("[data-time]");
    timeElements.forEach(function(element) {
        const utcTime = element.getAttribute('data-time');
        const localTime = new Date(utcTime);

        const options = { year: 'numeric', month: 'long', day: 'numeric', hour: 'numeric', minute: 'numeric', hour12: true };
        const formattedTime = localTime.toLocaleString(undefined, options);

        element.textContent = formattedTime;
    });
});