// static/js/settings.js
function updateProfilePictureLabel(input) {
    const label = input.previousElementSibling;
    if (input.files.length > 0) {
        label.textContent = input.files[0].name;
    } else {
        label.textContent = 'Upload Profile Picture';
    }
}

function updateChannelBannerLabel(input) {
    const label = input.previousElementSibling;
    if (input.files.length > 0) {
        label.textContent = input.files[0].name;
    } else {
        label.textContent = 'Upload Channel Banner';
    }
}