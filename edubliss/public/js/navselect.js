function submitForm() {
    const form = document.getElementById('userForm');
    const formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === 'success') {
            const redirectUrl = formData.get('initial_url') || window.location.href;
            window.location.href = redirectUrl;

            // Check if the redirect URL is the same as the current URL and reload if so
            if (redirectUrl === window.location.href) {
                location.reload();
            }
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
        location.reload(); // Reload the page on error
    });

    return false; // Prevent the form from submitting the default way
}
