document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const resultDiv = document.querySelector('.result');

    form.addEventListener('submit', async function(event) {
        event.preventDefault();

        const formData = new FormData(form);
        const response = await postData('/download', formData);

        resultDiv.textContent = response.message;
    });

    async function postData(url, data) {
        const response = await fetch(url, {
            method: 'POST',
            body: data
        });

        return await response.json();
    }
});
