

function togglePassword() {
      const passwordInput = document.getElementById("passwordField");
      const eyeIcon = document.getElementById("eyeIcon");

      if (passwordInput.type === "password") {
        passwordInput.type = "text";
        eyeIcon.classList.remove("fa-eye");
        eyeIcon.classList.add("fa-eye-slash");
      } else {
        passwordInput.type = "password";
        eyeIcon.classList.remove("fa-eye-slash");
        eyeIcon.classList.add("fa-eye");
      }
    }

  

    // mouse track

    const title = document.getElementById("title");
    const buttons = document.getElementById("buttons");

    function applyTransform(x, y) {
      const offsetX = (x - window.innerWidth / 2) / 50;
      const offsetY = (y - window.innerHeight / 2) / 50;

      title.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
      buttons.style.transform = `translate(${offsetX * 1.8}px, ${offsetY * 1.8}px)`;
    }

// Mouse movement
document.addEventListener("mousemove", (e) => {
  applyTransform(e.clientX, e.clientY);
});

// Touch movement (mobile)
document.addEventListener("touchmove", (e) => {
  if (e.touches.length > 0) {
    const touch = e.touches[0];
    applyTransform(touch.clientX, touch.clientY);
  }
});


// Reset transform on mouse leave
  let timeout;

  function startInactivityTimer() {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      window.location.href = '/home/';  // Redirect to home after 5 mins of inactivity
    }, 300000);  // 5 minutes = 300,000 ms
  }

  // Reset timer on user activity
  ['mousemove', 'keydown', 'click', 'scroll'].forEach(event => {
    document.addEventListener(event, startInactivityTimer);
  });

  startInactivityTimer();  // Start on page load

function checkOrientation() {
  const msg = document.getElementById('rotate-screen-message');
  if(window.matchMedia("(max-width: 600px) and (orientation: portrait)").matches) {
    msg.style.display = 'block';
  } else {
    msg.style.display = 'none';
  }
}

// Check on load
window.addEventListener('load', checkOrientation);

// Check on orientation change
window.addEventListener('orientationchange', checkOrientation);
