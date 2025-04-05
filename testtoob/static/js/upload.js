// static/js/upload.js
function updateThumbnailLabel(input) {
    const label = input.previousElementSibling;
    if (input.files.length > 0) {
        label.textContent = input.files[0].name;
    } else {
        label.textContent = 'Upload Thumbnail';
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

function validateFileType(input, allowedTypes, type) {
    const file = input.files[0];
    if (file) {
        const fileType = file.type;
        const isValidType = allowedTypes.includes(fileType);
        
        // Check for valid file extensions
        const allowedExtensions = ['.mp4', '.mov'];
        const fileName = file.name;
        const fileExtension = fileName.slice((fileName.lastIndexOf("."))).toLowerCase();
        const isValidExtension = allowedExtensions.includes(fileExtension);

        if (!isValidType && !isValidExtension) {
            input.value = ""; // Clear the input
            if (type === 'thumbnail') {
                updateThumbnailLabel(input);
            } else if (type === 'video') {
                updateVideoLabel(input);
            }
        }
    }
}

function validateVideo(input) {
    validateFileType(input, ['video/mp4', 'video/quicktime'], 'video');
}

function validateThumbnail(input) {
    validateFileType(input, ['image/jpeg', 'image/png'], 'thumbnail');
}

document.getElementById('video_upload_form').onsubmit = function(event) {
    const fileInput = document.getElementById('video_file');
    const maxSize = 250 * 1024 * 1024;

    if (fileInput.files[0].size > maxSize) {
        alert('The video file exceeds the 250 MB limit.');
        event.preventDefault();
    }
};