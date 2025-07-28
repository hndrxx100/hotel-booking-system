document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('staffForm');
  const loginBtn = document.getElementById('staffLoginBtn');
  const loader = loginBtn.querySelector('.spinner');
  const feedbackModal = document.getElementById('feedbackModal');
  const feedbackMessage = document.getElementById('feedbackMessage');
  const feedbackCloseBtn = document.getElementById('feedbackCloseBtn');
  const feedbackCloseFooterBtn = document.getElementById('feedbackCloseFooterBtn');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = form.querySelector('input[name="email"]').value.trim();
    const password = form.querySelector('input[name="password"]').value;

    // Client-side validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email) {
      showError('Email is required');
      return;
    }
    if (!emailRegex.test(email)) {
      showError('Please enter a valid email address');
      return;
    }
    if (!password) {
      showError('Password is required');
      return;
    }

    // Show loader
    loginBtn.disabled = true;
    loader.classList.remove('hidden');

    try {
      const startTime = Date.now();
      const minSpinnerDuration = 1000; // Minimum 1s spinner duration

      const response = await fetch(form.action, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: new URLSearchParams({
          email,
          password,
        }),
      });

      // Ensure spinner is shown for at least 1s
      const elapsedTime = Date.now() - startTime;
      if (elapsedTime < minSpinnerDuration) {
        await new Promise(resolve => setTimeout(resolve, minSpinnerDuration - elapsedTime));
      }

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          window.location.href = data.redirect; // Redirect to dashboard
        } else {
          showError(data.message || 'Invalid email or password');
        }
      } else {
        showError('Invalid email or password');
      }
    } catch (error) {
      showError('An error occurred. Please try again.');
      console.error('Login error:', error);
    } finally {
      loginBtn.disabled = false;
      loader.classList.add('hidden');
    }
  });

  function showError(message) {
    feedbackMessage.textContent = message;
    feedbackModal.classList.remove('hidden');
    feedbackModal.setAttribute('aria-hidden', 'false');
    feedbackCloseFooterBtn.focus();
    setTimeout(() => {
      feedbackModal.classList.add('hidden');
      feedbackModal.setAttribute('aria-hidden', 'true');
    }, 5000);
  }

  if (feedbackCloseBtn) {
    feedbackCloseBtn.addEventListener('click', () => {
      feedbackModal.classList.add('hidden');
      feedbackModal.setAttribute('aria-hidden', 'true');
      form.querySelector('input[name="email"]').focus();
    });
  }

  if (feedbackCloseFooterBtn) {
    feedbackCloseFooterBtn.addEventListener('click', () => {
      feedbackModal.classList.add('hidden');
      feedbackModal.setAttribute('aria-hidden', 'true');
      form.querySelector('input[name="email"]').focus();
    });
  }

  // Prevent form submission if JavaScript is disabled
  if (form) {
    form.addEventListener('click', (e) => {
      if (!form.dataset.jsEnabled) {
        e.preventDefault();
        alert('JavaScript is required to log in. Please try enabling JavaScript.');
      }
    });
    form.dataset.jsEnabled = 'true';
  }
});