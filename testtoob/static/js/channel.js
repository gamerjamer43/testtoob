document.addEventListener('DOMContentLoaded', function() {
    const subscribeButton = document.querySelector('.subscribe-button'); // Changed to class selector

    if (subscribeButton) {
        subscribeButton.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            const isSubscribed = this.getAttribute('data-subscribed') === 'true';
            const subscriberCountElement = document.querySelector('.subscriber-count');

            toggleSubscription(userId, isSubscribed)
                .then(data => {
                    if (data.isSubscribed) {
                        this.innerText = 'Unsubscribe';
                        subscriberCountElement.innerText = (parseInt(subscriberCountElement.innerText.split(' ')[0]) + 1) + ' Subscribers';
                    } else {
                        this.innerText = 'Subscribe';
                        subscriberCountElement.innerText = (parseInt(subscriberCountElement.innerText.split(' ')[0]) - 1) + ' Subscribers';
                    }
                    this.setAttribute('data-subscribed', data.isSubscribed);
                });
        });
    } else {
        console.error('Subscribe button not found in the DOM.');
    }

    const deleteButtons = document.querySelectorAll('.delete-button');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const videoId = this.getAttribute('data-video-id');
            if (confirm('Are you sure you want to delete this video?')) {
                deleteVideo(videoId)
                    .then(data => {
                        alert(data.message);
                        if (data.success) {
                            location.reload();
                        }
                    });
            }
        });
    });

    const notificationBell = document.getElementById('notification-bell'); // Select by ID
    if (notificationBell) {
        notificationBell.addEventListener('click', function() {
            const button = this;
            const subscribeButton = document.querySelector('.subscribe-button'); // Corrected selection to class
            if (subscribeButton) {
                const channelId = subscribeButton.getAttribute('data-user-id'); // Updated to use data-user-id
                const isSubscribed = subscribeButton.getAttribute('data-subscribed') === 'true';
                const notificationsEnabled = button.classList.toggle('active');

                if (!isSubscribed) {
                    alert('You must be subscribed to enable notifications.');
                    button.classList.toggle('active', !notificationsEnabled);
                    return;
                }

                fetch(`/toggle_notifications/${channelId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ enabled: notificationsEnabled })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        if (data.notifications_enabled) {
                            button.innerHTML = '<i class="fas fa-bell" id="notification-icon"></i> Enabled';
                        } else {
                            button.innerHTML = '<i class="fas fa-bell" id="notification-icon"></i> Disabled';
                        }
                    } else {
                        alert('Error updating notification settings: ' + (data.error || 'Unknown error.'));
                    }
                })
                .catch(err => {
                    console.error('Error:', err);
                    alert('An error occurred while updating notification settings.');
                });
            } else {
                console.error('Subscribe button not found for notification settings.');
            }
        });
    } else {
        console.error('Notification bell button not found in the DOM.');
    }
});

async function toggleSubscription(userId, isSubscribed) {
    const response = await fetch(`/subscribe/${userId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ subscribed: !isSubscribed })
    });

    return await response.json();
}

async function deleteVideo(videoId) {
    const response = await fetch(`/delete_video/${videoId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    });

    return await response.json();
}
