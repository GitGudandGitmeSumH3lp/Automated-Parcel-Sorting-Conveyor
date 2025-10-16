document.addEventListener('DOMContentLoaded', function() {
    // Update current year in the footer
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) {
        currentYearSpan.textContent = new Date().getFullYear();
    }

    const loginForm = document.getElementById('loginForm');
    const loginButton = document.getElementById('loginButton');
    const buttonText = loginButton ? loginButton.querySelector('.button-text') : null;
    const buttonLoader = loginButton ? loginButton.querySelector('.button-loader') : null;

    // Input field focus and blur effects (already handled by CSS :focus, but you can add more JS if needed)
    const inputs = document.querySelectorAll('.input-group input');
    inputs.forEach(input => {
        input.addEventListener('focus', () => {
            input.parentElement.classList.add('focused');
        });
        input.addEventListener('blur', () => {
            input.parentElement.classList.remove('focused');
        });
    });

    if (loginForm && loginButton && buttonText && buttonLoader) {
        loginForm.addEventListener('submit', function(event) {
            // Show loader and disable button
            buttonText.style.display = 'none';
            buttonLoader.style.display = 'inline-block';
            loginButton.disabled = true;
            loginButton.classList.add('loading');

            // Simulate network request for demonstration (remove for actual use)
            // For actual use, the Flask backend will handle the response.
            // If Flask redirects on success, the loader will disappear naturally.
            // If Flask re-renders the page with an error, you'll need to handle
            // resetting the button state (see Flask integration notes).

            // Example: setTimeout(() => {
            //     // This is where you'd typically get a response from the server.
            //     // If login fails and the page re-renders with an error,
            //     // this JS won't necessarily know to reset the button unless
            //     // the server sends specific instructions or you check for an error message.
            //     console.log("Form submitted (simulated)");
            //     // If you were staying on the page and handling errors with JS:
            //     // buttonText.style.display = 'inline-block';
            //     // buttonLoader.style.display = 'none';
            //     // loginButton.disabled = false;
            //     // loginButton.classList.remove('loading');
            // }, 2000);
        });
    }

    // If there's an error message displayed by Flask, ensure the button is not in loading state
    // This assumes the page reloads with the error message
    const errorMessage = document.querySelector('.error-message');
    if (errorMessage && errorMessage.textContent.trim() !== '' && loginButton && buttonText && buttonLoader) {
        buttonText.style.display = 'inline-block';
        buttonLoader.style.display = 'none';
        loginButton.disabled = false;
        loginButton.classList.remove('loading');
    }
});