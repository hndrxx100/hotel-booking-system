document.addEventListener('DOMContentLoaded', function () {
  const guestToggle = document.getElementById('guestToggle');
  const staffToggle = document.getElementById('staffToggle');
  const guestForm = document.getElementById('guestForm');
  const staffForm = document.getElementById('staffForm');

  if (!guestToggle || !staffToggle || !guestForm || !staffForm) return;

  guestToggle.addEventListener('click', function () {
    guestForm.classList.remove('hidden');
    staffForm.classList.add('hidden');
    guestToggle.classList.add('bg-blue-600', 'text-white');
    guestToggle.classList.remove('bg-gray-200', 'text-blue-600');
    staffToggle.classList.remove('bg-blue-600', 'text-white');
    staffToggle.classList.add('bg-gray-200', 'text-blue-600');
  });

  staffToggle.addEventListener('click', function () {
    staffForm.classList.remove('hidden');
    guestForm.classList.add('hidden');
    staffToggle.classList.add('bg-blue-600', 'text-white');
    staffToggle.classList.remove('bg-gray-200', 'text-blue-600');
    guestToggle.classList.remove('bg-blue-600', 'text-white');
    guestToggle.classList.add('bg-gray-200', 'text-blue-600');
  });

  // Spinner logic
  guestForm.addEventListener('submit', function () {
    const button = document.getElementById('guestLoginBtn');
    const loader = button.querySelector('.loader');
    const text = button.querySelector('span');

    loader.classList.remove('hidden');
    text.classList.add('opacity-50');
    button.disabled = true;
  });

  staffForm.addEventListener('submit', function () {
    const button = document.getElementById('staffLoginBtn');
    const loader = button.querySelector('.loader');
    const text = button.querySelector('span');

    loader.classList.remove('hidden');
    text.classList.add('opacity-50');
    button.disabled = true;
  });

  // ✅ Fix for "Back button keeps spinner spinning"
  document.querySelectorAll('form button').forEach(btn => {
    const loader = btn.querySelector('.loader');
    const text = btn.querySelector('span');
    if (loader) loader.classList.add('hidden');
    if (text) text.classList.remove('opacity-50');
    btn.disabled = false;
  });
});
