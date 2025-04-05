$(document).ready(function() {
    $('#notifications-button').click(function() {
        $.ajax({
            url: '/notifications',
            type: 'GET',
            success: function(data) {
                console.log("Notifications data received:", data);
                $('#notifications-modal-body').html(data.html);
                $('#notification-count').text(data.count);
                if (parseInt(data.count) === 0) {
                    $('#notification-count').css('display', 'none'); // Hides the count element
                } else {
                    $('#notification-count').css('display', 'inline'); // Shows the count element
                }
                $('#notifications-modal').modal('show');
            },
            error: function(xhr, status, error) {
                console.error("Error fetching notifications:", status, error);
                alert("Could not fetch notifications. Please try again later.");
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    fetchNotifications();
});

function fetchNotifications() {
    fetch('/notifications')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (parseInt(data.count) === 0) {
                $('#notification-count').css('display', 'none');
            } else {
                $('#notification-count').css('display', 'inline');
            }
        })
        .catch(error => {
            console.error('Error fetching notifications:', error);
        });
}