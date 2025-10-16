
// Matrix rain effect
const canvas = document.getElementById('matrix');
const ctx = canvas.getContext('2d');

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@#$%^&*()_+-=[]{}|;:,.<>?';
const font_size = 12;
const columns = canvas.width / font_size;

const drops = [];

for (let i = 0; i < columns; i++) {
    drops[i] = 1;
}

function drawMatrix() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = '#0F0';
    ctx.font = font_size + 'px monospace';

    for (let i = 0; i < drops.length; i++) {
        const text = characters.charAt(Math.floor(Math.random() * characters.length));
        ctx.fillText(text, i * font_size, drops[i] * font_size);

        if (drops[i] * font_size > canvas.height && Math.random() > 0.975) {
            drops[i] = 0;
        }

        drops[i]++;
    }
}

setInterval(drawMatrix, 33);

// Auto-update terminal noise
function updateNoise() {
    const noise = document.querySelector('.noise');
    noise.style.backgroundImage = `url('data:image/png;base64,${generateNoiseBase64()}')`;
}

function generateNoiseBase64() {
    const canvas = document.createElement('canvas');
    canvas.width = 100;
    canvas.height = 100;
    const ctx = canvas.getContext('2d');

    const imageData = ctx.createImageData(100, 100);
    const data = imageData.data;

    for (let i = 0; i < data.length; i += 4) {
        const value = Math.floor(Math.random() * 255);
        data[i] = value;
        data[i + 1] = value;
        data[i + 2] = value;
        data[i + 3] = Math.random() * 50;
    }

    ctx.putImageData(imageData, 0, 0);
    return canvas.toDataURL().split(',')[1];
}

setInterval(updateNoise, 200);

// Add dynamic terminal messages
const systemMessages = [
    "Package ID: APS-27491 processed by OCR.",
    "Conveyor section C3 maintenance scheduled.",
    "Database backup completed successfully.",
    "OCR accuracy rate: 99.7% in last 24 hours.",
    "System resource utilization: 42%",
    "Network connectivity: OPTIMAL"
];

function addRandomSystemMessage() {
    const systemLog = document.querySelector('.system-log');
    const randomMessage = systemMessages[Math.floor(Math.random() * systemMessages.length)];

    if (Math.random() > 0.5) {
        systemLog.innerHTML += `<p>[<span class="highlight">INFO</span>] ${randomMessage}</p>`;
        systemLog.scrollTop = systemLog.scrollHeight;
    }
}

setInterval(addRandomSystemMessage, 8000);

// Resize canvas on window resize
window.addEventListener('resize', function () {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});

window.onload = function() {
    const loginContainer = document.getElementById('login-container');
    const dashboardContainer = document.getElementById('dashboard-container');
    const dashboardUsernameDisplay = document.getElementById('dashboard-username');


    fetch('/check-session')
        .then(response => response.json())
        .then(data => {
            if (data.loggedIn) {
                loginContainer.style.display = 'none';
                dashboardContainer.style.display = 'block';
                dashboardUsernameDisplay.textContent = data.username;
            } else {
                loginContainer.style.display = 'block';
                dashboardContainer.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error checking session:', error);
            loginContainer.style.display = 'block';
            dashboardContainer.style.display = 'none';
        });
};