// static/js/video.js
document.getElementById('like-button').addEventListener('click', function() {
    const button = this;
    const dislikebutton = document.getElementById('dislike-button')
    const videoId = button.getAttribute('data-video-id');

    fetch(`/like/${videoId}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.isLiked) {
                dislikebutton.classList.remove('btn-danger');
                dislikebutton.classList.add('btn-outline-light');
                button.classList.remove('btn-outline-light');
                button.classList.add('btn-success');
                button.innerHTML = '<i class="fas fa-thumbs-up"></i> Unlike (<span id="like-count">' + data.likeCount + '</span>)';
                dislikebutton.innerHTML = '<i class="fas fa-thumbs-down"></i> Dislike (<span id="like-count">' + data.dislikeCount + '</span>)';
            } else {
                button.classList.add('btn-outline-light');
                button.classList.remove('btn-success');
                button.innerHTML = '<i class="fas fa-thumbs-up"></i> Like (<span id="like-count">' + data.likeCount + '</span>)';
            }
            button.setAttribute('data-liked', data.isLiked);
            dislikebutton.setAttribute('data-disliked', false);
        });
});

document.getElementById('dislike-button').addEventListener('click', function() {
    const button = this;
    const likebutton = document.getElementById('like-button')
    const videoId = button.getAttribute('data-video-id');

    fetch(`/dislike/${videoId}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.isDisliked) {
                button.classList.remove('btn-outline-light');
                button.classList.add('btn-danger');
                likebutton.classList.remove('btn-success');
                likebutton.classList.add('btn-outline-light');
                button.innerHTML = '<i class="fas fa-thumbs-down"></i> Undislike (<span id="like-count">' + data.dislikeCount + '</span>)';
                likebutton.innerHTML = '<i class="fas fa-thumbs-up"></i> Like (<span id="like-count">' + data.likeCount + '</span>)';
            } else {
                button.classList.add('btn-outline-light');
                button.classList.remove('btn-danger');
                button.innerHTML = '<i class="fas fa-thumbs-down"></i> Dislike (<span id="dislike-count">' + data.dislikeCount + '</span>)';
            }
            button.setAttribute('data-disliked', data.isDisliked);
            likebutton.setAttribute('data-liked', false);
        });
});

document.getElementById('subscribe-button').addEventListener('click', function() {
    const button = this;
    const channelId = button.getAttribute('data-channel-id');

    fetch(`/subscribe/${channelId}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.isSubscribed) {
                button.innerHTML = 'Unsubscribe (<span id="subscription-count" style="color: white;">' + data.subscriptionCount + '</span>)';
                button.classList.add('btn-success');
                button.classList.remove('btn-outline-light')
            } else {
                button.innerHTML = 'Subscribe (<span id="subscription-count">' + data.subscriptionCount + '</span>)';
                button.classList.remove('btn-success');
                button.classList.add('btn-outline-light')
            }
            button.setAttribute('data-subscribed', data.isSubscribed);
        });
});

document.getElementById('comment-form').addEventListener('submit', function(e) {
    e.preventDefault();

    const form = this;
    const formData = new FormData(form);
    const videoId = formData.get('video-id');

    fetch(`/video/${videoId}`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const newComment = `
            <div class="comment mb-2" id="comment-${data.comment.id}">
                <strong><h5><a href="/channel/${data.comment.author_id}">${data.comment.author_username}</a>: ${data.comment.content}</h5></strong> 
                <div>
                    <form action="/comment/${data.comment.id}/like" method="POST" class="d-inline">
                        <button class="fas fa-thumbs-up"></button> (0) Like
                    </form>
                    <form action="/comment/${data.comment.id}/dislike" method="POST" class="d-inline">
                        <button class="fas fa-thumbs-down"></button> (0) Dislike
                    </form>
                <br>
                </div>
                <form method="POST" action="/reply_to_comment/${data.comment.id}">
                    <br>
                    <textarea class="form-control mb-2" name="reply" rows="2" placeholder="Reply to this comment" style="background-color: #1a1a1a; border-color: gray;"></textarea>
                    <button type="submit" class="btn btn-secondary">Reply</button>
                </form>
            </div>
            `;

            document.getElementById('comments-section').insertAdjacentHTML('beforeend', newComment);
            form.reset();
        } else {
            alert('Error submitting comment');
        }
    })
    .catch(err => {
        console.error('Error:', err);
        alert('An error occurred while submitting the comment.');
    });
});

document.getElementById('notification-bell').addEventListener('click', function() {
    const button = this;
    const channelId = document.getElementById('subscribe-button').getAttribute('data-channel-id');
    const isSubscribed = document.getElementById('subscribe-button').getAttribute('data-subscribed') === 'true';
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
                button.classList.add('btn-primary');
                button.classList.remove('btn-outline-light');
            } else {
                button.classList.remove('btn-primary');
                button.classList.add('btn-outline-light');
            }
        } else {
            alert('Error updating notification settings: ' + (data.error || 'Unknown error.'));
        }
    })
    .catch(err => {
        console.error('Error:', err);
        alert('An error occurred while updating notification settings.');
    });
});


function deleteComment(commentId) {
    const form = document.getElementById(`delete-comment-form-${commentId}`);
    fetch(form.action, {
        method: 'DELETE',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ comment_id: commentId }),
    })
    .then(response => {
        if (response.ok) {
            form.closest('.comment').remove();
        } else {
            alert('Error deleting comment.');
        }
    });
}

function deleteReply(commentId) {
    const form = document.getElementById(`delete-reply-form-${commentId}`);
    fetch(form.action, {
        method: 'DELETE',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reply_id: commentId }),
    })
    .then(response => {
        if (response.ok) {
            form.closest('.reply').remove();
        } else {
            alert('Error deleting comment.');
        }
    });
}