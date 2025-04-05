function deleteNotification(notificationId) {
    if (confirm('Are you sure you want to delete this notification?')) {
        fetch(`/delete_notification/${notificationId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const notificationItem = document.querySelector(`li[data-notification-id="${notificationId}"]`);
                if (notificationItem) {
                    notificationItem.remove();
                }
            } else {
                alert(result.error);
            }
        })
        .catch(error => console.error('Error:', error));
    }
}
