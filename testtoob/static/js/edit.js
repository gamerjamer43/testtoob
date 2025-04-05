//static/js/edit.js
document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');
    
    form.addEventListener('submit', async function (event) {
        event.preventDefault();

        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const result = await response.json();
                alert(result.message);
                window.location.href = `/channel/${result.user_id}`;
            } else {
                const errorData = await response.json();
                alert(errorData.message);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while updating the video.');
        }
    });
});

function validateTags() {
    const tagsInput = document.getElementById('tags');
    const tagError = document.getElementById('tagError');
    const tags = tagsInput.value.split(',').map(tag => tag.trim()).filter(tag => tag);
    
    if (tags.length > 5) {
        tagError.textContent = "You can only enter a maximum of 5 tags.";
        tagError.style.display = "block";
    } else {
        tagError.style.display = "none";
    }
}

function updateVideoLabel(input) {
    const label = input.previousElementSibling;
    if (input.files.length > 0) {
        label.textContent = input.files[0].name;
    } else {
        label.textContent = 'Upload Video';
    }
}