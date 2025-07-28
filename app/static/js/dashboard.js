document.addEventListener('DOMContentLoaded', () => {
  console.log('dashboard.js loaded');

  // DOM Elements
  const bookingsContent = document.getElementById('bookingsContent');
  const roomsContent = document.getElementById('roomsContent');
  const guestsTableBody = document.querySelector('#guestsTable tbody');
  const bookingsPagination = document.getElementById('bookingsPagination');
  const roomsPagination = document.getElementById('roomsPagination');
  const searchForm = document.getElementById('searchForm');
  const walkinForm = document.getElementById('walkinForm');
  const addRoomForm = document.getElementById('addRoomForm');
  const modifyBookingModal = document.getElementById('modifyBookingModal');
  const modifyBookingForm = document.getElementById('modifyBookingForm');
  const walkinConfirmModal = document.getElementById('walkinConfirmModal');
  const walkinConfirmSubmit = document.getElementById('walkinConfirmSubmit');
  const walkinConfirmCancel = document.getElementById('walkinConfirmCancel');
  const walkinConfirmCancelBtn = document.getElementById('walkinConfirmCancelBtn');
  const feedbackModal = document.getElementById('feedbackModal');
  const feedbackMessage = document.getElementById('feedbackMessage');
  const bookingReferenceDisplay = document.getElementById('bookingReferenceDisplay');
  const deleteRoomModal = document.getElementById('deleteRoomModal');
  const deleteRoomConfirm = document.getElementById('deleteRoomConfirm');
  const deleteRoomCancel = document.getElementById('deleteRoomCancel');
  const deleteRoomId = document.getElementById('deleteRoomId');
  const deleteBookingModal = document.getElementById('deleteBookingModal');
  const deleteBookingConfirm = document.getElementById('deleteBookingConfirm');
  const deleteBookingCancel = document.getElementById('deleteBookingCancel');
  const deleteBookingId = document.getElementById('deleteBookingId');
  const refreshDashboard = document.getElementById('refreshDashboard');
  const statusTabs = document.querySelectorAll('.status-tab');
  const bookingFilter = document.getElementById('bookingFilter');
  const searchRoomsBtn = document.getElementById('searchRoomsBtn');
  const walkinRoomSelect = document.getElementById('walkin-room-id');
  const walkinRoomsMessage = document.getElementById('walkinRoomsMessage');
  const searchModifyRoomsBtn = document.getElementById('searchModifyRoomsBtn');
  const modifyRoomSelect = document.getElementById('modify-room-id');
  const modifyRoomsMessage = document.getElementById('modifyRoomsMessage');
  const walkinBtn = document.getElementById('walkinBtn');
  const walkinBtnModal = document.getElementById('walkinBtnModal');
  const addRoomBtnModal = document.getElementById('addRoomBtnModal');
  const walkinFormModal = document.getElementById('walkinFormModal');
  const walkinFormCloseBtn = document.getElementById('walkinFormCloseBtn');
  const addRoomModal = document.getElementById('addRoomModal');
  const addRoomCloseBtn = document.getElementById('addRoomCloseBtn');
  const contentSpinner = document.getElementById('contentSpinner');
  const modifyCloseBtn = document.getElementById('modifyCloseBtn');
  const modifyCloseXBtn = document.getElementById('modifyCloseXBtn');
  const feedbackCloseBtn = document.getElementById('feedbackCloseBtn');
  const feedbackCloseXBtn = document.getElementById('feedbackCloseXBtn');
  const clearSearch = document.getElementById('clearSearch');

  let currentBookingsPage = 1;
  let currentRoomsPage = 1;
  let currentStatusFilter = 'all';
  let currentBookingFilter = 'all';
  let walkinFormData = null;

  // Date Formatting Functions
  function formatDateToDisplay(dateStr) {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
    } catch (error) {
      console.error('Error formatting date for display:', dateStr, error);
      return '';
    }
  }

  function formatDateToBackend(dateStr) {
    if (!dateStr) return '';
    try {
      const date = flatpickr.parseDate(dateStr, 'd F Y');
      return date.toISOString().split('T')[0]; // YYYY-MM-DD
    } catch (error) {
      console.error('Error parsing date for backend:', dateStr, error);
      return '';
    }
  }

  // Initialize Flatpickr
  const walkinCheckIn = document.getElementById('walkin-check-in-date');
  const walkinCheckOut = document.getElementById('walkin-check-out-date');
  const modifyCheckIn = document.getElementById('modify-check-in-date');
  const modifyCheckOut = document.getElementById('modify-check-out-date');

  if (walkinCheckIn && walkinCheckOut) {
    flatpickr(walkinCheckIn, {
      dateFormat: 'd F Y',
      minDate: 'today',
      onChange: (selectedDates, dateStr) => {
        walkinCheckIn.value = dateStr;
        if (selectedDates[0]) {
          const minCheckOut = new Date(selectedDates[0]);
          minCheckOut.setDate(minCheckOut.getDate() + 1);
          walkinCheckOut._flatpickr.set('minDate', minCheckOut);
        }
      }
    });

    flatpickr(walkinCheckOut, {
      dateFormat: 'd F Y',
      minDate: 'tomorrow'
    });
  }

  if (modifyCheckIn && modifyCheckOut) {
    flatpickr(modifyCheckIn, {
      dateFormat: 'd F Y',
      minDate: 'today',
      onChange: (selectedDates, dateStr) => {
        modifyCheckIn.value = dateStr;
        if (selectedDates[0]) {
          const minCheckOut = new Date(selectedDates[0]);
          minCheckOut.setDate(minCheckOut.getDate() + 1);
          modifyCheckOut._flatpickr.set('minDate', minCheckOut);
        }
      }
    });

    flatpickr(modifyCheckOut, {
      dateFormat: 'd F Y',
      minDate: 'tomorrow'
    });
  }

  // Show/Hide Spinner
  function showSpinner(element) {
    if (element) {
      element.querySelector('.spinner').classList.remove('hidden');
      element.disabled = true;
    }
    contentSpinner.classList.remove('hidden');
  }

  function hideSpinner(element) {
    if (element) {
      element.querySelector('.spinner').classList.add('hidden');
      element.disabled = false;
    }
    contentSpinner.classList.add('hidden');
  }

  function trapFocus(modal) {
  const focusableElements = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  const firstFocusable = focusableElements[0];
  const lastFocusable = focusableElements[focusableElements.length - 1];

  modal.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      if (e.shiftKey) {
        if (document.activeElement === firstFocusable) {
          e.preventDefault();
          lastFocusable.focus();
        }
      } else {
        if (document.activeElement === lastFocusable) {
          e.preventDefault();
          firstFocusable.focus();
        }
      }
    }
  });

  if (firstFocusable) firstFocusable.focus();
  }

  // Show Feedback Modal
  function showFeedback(message, bookingReference = null) {
  feedbackMessage.textContent = message;
  if (bookingReference) {
    bookingReferenceDisplay.textContent = `Booking Reference: ${bookingReference}`;
    bookingReferenceDisplay.classList.remove('hidden');
  } else {
    bookingReferenceDisplay.classList.add('hidden');
  }
  feedbackModal.classList.remove('hidden');
  feedbackModal.setAttribute('aria-hidden', 'false');
  trapFocus(feedbackModal);
  }

  // Close Feedback Modal
  function closeFeedback() {
    feedbackModal.classList.add('hidden');
    feedbackModal.setAttribute('aria-hidden', 'true');
    bookingReferenceDisplay.classList.add('hidden');
  }

  feedbackCloseBtn.addEventListener('click', closeFeedback);
  feedbackCloseXBtn.addEventListener('click', closeFeedback);

  // Navigation
  // Navigation
document.querySelectorAll('.nav-link').forEach(button => {
  button.addEventListener('click', () => {
    // Remove active and color classes from all buttons
    document.querySelectorAll('.nav-link').forEach(btn => {
      btn.classList.remove('active', btn.dataset.activeBg, btn.dataset.hoverBg);
      btn.classList.add('bg-gray-700', 'hover:bg-gray-600');
    });
    // Add active and specific color classes to clicked button
    button.classList.add('active', button.dataset.activeBg, button.dataset.hoverBg);
    button.classList.remove('bg-gray-700', 'hover:bg-gray-600');
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => section.classList.add('hidden'));
    const sectionId = button.getAttribute('data-section');
    document.getElementById(sectionId).classList.remove('hidden');

    // Show spinner for at least 1 second during content transition
    showSpinner();
    setTimeout(() => {
      if (sectionId === 'bookings') {
        fetchBookings();
      } else if (sectionId === 'rooms') {
        fetchRooms();
      } else if (sectionId === 'guests') {
        fetchGuests();
      } else if (sectionId === 'priorities') {
        fetchPriorities();
      }
    }, 500); // Delay to ensure spinner shows for 1 second
  });
});

// Ensure Priorities is active on page load
document.addEventListener('DOMContentLoaded', () => {
  console.log('dashboard.js loaded');
  const prioritiesButton = document.querySelector('.nav-link[data-section="priorities"]');
  if (prioritiesButton) {
    prioritiesButton.classList.add('active', prioritiesButton.dataset.activeBg, prioritiesButton.dataset.hoverBg);
    prioritiesButton.classList.remove('bg-gray-700', 'hover:bg-gray-600');
    document.getElementById('priorities').classList.remove('hidden');
    fetchPriorities();
  }
  // ... rest of your DOMContentLoaded code ...
});

  // Modal Handlers
  walkinBtnModal.addEventListener('click', () => {
  walkinFormModal.classList.remove('hidden');
  walkinFormModal.setAttribute('aria-hidden', 'false');
  walkinForm.reset();
  walkinRoomSelect.innerHTML = '<option value="">Search rooms first</option>';
  walkinRoomSelect.disabled = true;
  walkinRoomsMessage.classList.add('hidden');
  walkinBtn.disabled = true;
  trapFocus(walkinFormModal);
   });

addRoomBtnModal.addEventListener('click', () => {
  addRoomModal.classList.remove('hidden');
  addRoomModal.setAttribute('aria-hidden', 'false');
  addRoomForm.reset();
  trapFocus(addRoomModal);
   });

  walkinFormCloseBtn.addEventListener('click', () => {
    walkinFormModal.classList.add('hidden');
    walkinFormModal.setAttribute('aria-hidden', 'true');
    walkinForm.reset();
  });

  addRoomCloseBtn.addEventListener('click', () => {
    addRoomModal.classList.add('hidden');
    addRoomModal.setAttribute('aria-hidden', 'true');
    addRoomForm.reset();
  });

  // Fetch Priorities
  async function fetchPriorities() {
    try {
      showSpinner();
      const response = await fetch('/receptionist/priorities', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      renderPriorities(data);
    } catch (error) {
      console.error('Error fetching priorities:', error);
      showFeedback('Failed to load priorities. Please try again.');
    } finally {
      hideSpinner();
    }
  }

  // Render Priorities
  function renderPriorities(data) {
    document.getElementById('checkInsToday').textContent = data.check_ins_today || 0;
    document.getElementById('checkOutsToday').textContent = data.check_outs_today || 0;
    document.getElementById('overduePayments').textContent = data.overdue_payments || 0;
    document.getElementById('recentBookings').textContent = data.recent_bookings || 0;
    document.getElementById('upcomingCheckIns').textContent = data.upcoming_check_ins || 0;
    document.getElementById('totalBookingsToday').textContent = data.total_bookings_today || 0;
  }

  // Fetch Bookings
  async function fetchBookings(page = currentBookingsPage, status = currentStatusFilter, filter = currentBookingFilter, search = '') {
    try {
      showSpinner();
      const params = new URLSearchParams({
        page,
        status,
        filter,
        search_reference: search
      });
      const response = await fetch(`/receptionist/bookings?${params}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      renderBookings(data.bookings);
      renderPagination(bookingsPagination, data.pagination, (newPage) => {
        currentBookingsPage = newPage;
        fetchBookings(newPage, status, filter, search);
      });
    } catch (error) {
      console.error('Error fetching bookings:', error);
      showFeedback('Failed to load bookings. Please try again.');
      bookingsContent.innerHTML = '<p class="text-gray-200">No bookings found.</p>';
    } finally {
      hideSpinner();
    }
  }

  // Render Bookings as Cards
  function renderBookings(bookings) {
  if (!bookings || bookings.length === 0) {
    bookingsContent.innerHTML = '<p class="text-gray-200 col-span-full">No bookings found.</p>';
    return;
  }
  bookingsContent.innerHTML = bookings.map(booking => {
    const checkInDate = formatDateToDisplay(booking.check_in_date);
    const checkOutDate = formatDateToDisplay(booking.check_out_date);
    const isBooked = booking.status === 'booked';
    const isCheckedIn = booking.status === 'checked-in';
    const isCheckedOut = booking.status === 'checked-out';
    const isCancelled = booking.status === 'cancelled';
    const isPaid = booking.payment_status === 'paid';

    // Button states based on status and payment_status
    const modifyDisabled = isCheckedOut || isCancelled ? 'disabled' : '';
    const checkInDisabled = !isBooked || isPaid ? 'disabled' : '';
    const checkOutDisabled = !isCheckedIn || isPaid ? 'disabled' : '';
    const paymentDisabled = isPaid || isCancelled ? 'disabled' : '';
    const deleteDisabled = isCheckedOut || isCancelled ? '' : 'disabled'; // Backend allows only checked-out or cancelled

    return `
      <div class="bg-gray-800 p-4 rounded-xl shadow-lg border border-gray-600">
        <div class="flex justify-between items-center mb-2">
          <h3 class="text-lg font-semibold text-white">${booking.guest.full_name || 'Unknown'}</h3>
          <span class="text-sm font-medium text-blue-400">${booking.booking_reference}</span>
        </div>
        <p class="text-gray-200"><strong>Room:</strong> ${booking.room.room_number || 'N/A'}</p>
        <p class="text-gray-200"><strong>Check-In:</strong> ${checkInDate}</p>
        <p class="text-gray-200"><strong>Check-Out:</strong> ${checkOutDate}</p>
        <p class="text-gray-200"><strong>Status:</strong> <span class="${isCancelled ? 'text-red-400' : isCheckedOut ? 'text-gray-400' : isCheckedIn ? 'text-green-400' : 'text-yellow-400'}">${booking.status}</span></p>
        <p class="text-gray-200"><strong>Payment:</strong> <span class="${isPaid ? 'text-green-400' : 'text-red-400'}">${booking.payment_status}</span></p>
        <div class="flex flex-wrap gap-2 mt-4">
          <button class="modify-booking-btn p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-1 ${modifyDisabled}" data-booking-id="${booking.id}" data-email="${booking.guest.email || ''}" data-check-in="${booking.check_in_date}" data-check-out="${booking.check_out_date}" data-room-id="${booking.room.id || ''}" aria-label="Modify booking ${booking.booking_reference}">
            <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Modify
          </button>
          <button class="check-in-btn p-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center gap-1 ${checkInDisabled}" data-booking-id="${booking.id}" aria-label="Check-in booking ${booking.booking_reference}">
            <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            Check-In
          </button>
          <button class="check-out-btn p-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition flex items-center gap-1 ${checkOutDisabled}" data-booking-id="${booking.id}" aria-label="Check-out booking ${booking.booking_reference}">
            <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Check-Out
          </button>
          <button class="payment-btn p-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition flex items-center gap-1 ${paymentDisabled}" data-booking-id="${booking.id}" aria-label="Record payment for booking ${booking.booking_reference}">
            <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Payment
          </button>
          <button class="delete-booking-btn p-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition flex items-center gap-1 ${deleteDisabled}" data-booking-id="${booking.id}" aria-label="Delete booking ${booking.booking_reference}">
            <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5-4h4M4 7h16" />
            </svg>
            Delete
          </button>
        </div>
      </div>
    `;
  }).join('');
}

  // Fetch Rooms
  async function fetchRooms(page = currentRoomsPage) {
    try {
      showSpinner();
      const response = await fetch(`/receptionist/rooms?page=${page}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      renderRooms(data.rooms);
      renderPagination(roomsPagination, data.pagination, (newPage) => {
        currentRoomsPage = newPage;
        fetchRooms(newPage);
      });
    } catch (error) {
      console.error('Error fetching rooms:', error);
      showFeedback('Failed to load rooms. Please try again.');
      roomsContent.innerHTML = '<p class="text-gray-200">No rooms found.</p>';
    } finally {
      hideSpinner();
    }
  }

  // Render Rooms as Cards
  function renderRooms(rooms) {
    if (!rooms || rooms.length === 0) {
      roomsContent.innerHTML = '<p class="text-gray-200 col-span-full">No rooms found.</p>';
      return;
    }
    roomsContent.innerHTML = rooms.map(room => `
      <div class="bg-gray-800 p-4 rounded-xl shadow-lg border border-gray-600">
        <h3 class="text-lg font-semibold text-white">Room ${room.room_number}</h3>
        <p class="text-gray-200"><strong>Type:</strong> ${room.room_type}</p>
        <p class="text-gray-200"><strong>Price:</strong> GHS ${room.price}</p>
        <p class="text-gray-200"><strong>Status:</strong> <span class="${room.status === 'available' ? 'text-green-400' : 'text-red-400'}">${room.status}</span></p>
        <button class="delete-room-btn p-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition flex items-center gap-1 mt-2" data-room-id="${room.id}" aria-label="Delete room ${room.room_number}">
          <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5-4h4M4 7h16" />
          </svg>
          Delete
        </button>
      </div>
    `).join('');
  }

  // Fetch Guests
  async function fetchGuests() {
    try {
      showSpinner();
      const response = await fetch('/receptionist/guests', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      renderGuests(data.guests);
    } catch (error) {
      console.error('Error fetching guests:', error);
      showFeedback('Failed to load guests. Please try again.');
      guestsTableBody.innerHTML = '<tr><td colspan="4" class="p-3 text-gray-200">No guests found.</td></tr>';
    } finally {
      hideSpinner();
    }
  }

  // Render Guests
  function renderGuests(guests) {
    if (!guests || guests.length === 0) {
      guestsTableBody.innerHTML = '<tr><td colspan="4" class="p-3 text-gray-200">No guests found.</td></tr>';
      return;
    }
    guestsTableBody.innerHTML = guests.map(guest => `
      <tr class="bg-gray-700 hover:bg-gray-600 transition">
        <td class="p-3 text-gray-200">${guest.id}</td>
        <td class="p-3 text-gray-200">${guest.full_name}</td>
        <td class="p-3 text-gray-200">${guest.email}</td>
        <td class="p-3 text-gray-200">${guest.phone || 'N/A'}</td>
      </tr>
    `).join('');
  }

  // Render Pagination
  function renderPagination(container, pagination, onPageChange) {
    container.innerHTML = '';
    if (!pagination || pagination.total_pages <= 1) return;

    const prevButton = document.createElement('button');
    prevButton.textContent = 'Previous';
    prevButton.className = `p-2 rounded-lg ${pagination.current_page === 1 ? 'bg-gray-600 text-gray-400 cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'}`;
    prevButton.disabled = pagination.current_page === 1;
    prevButton.addEventListener('click', () => {
      if (pagination.current_page > 1) onPageChange(pagination.current_page - 1);
    });

    const nextButton = document.createElement('button');
    nextButton.textContent = 'Next';
    nextButton.className = `p-2 rounded-lg ${pagination.current_page === pagination.total_pages ? 'bg-gray-600 text-gray-400 cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'}`;
    nextButton.disabled = pagination.current_page === pagination.total_pages;
    nextButton.addEventListener('click', () => {
      if (pagination.current_page < pagination.total_pages) onPageChange(pagination.current_page + 1);
    });

    const pageInfo = document.createElement('span');
    pageInfo.textContent = `Page ${pagination.current_page} of ${pagination.total_pages}`;
    pageInfo.className = 'text-gray-200';

    container.append(prevButton, pageInfo, nextButton);
  }

  // Status Filter Tabs
  statusTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      statusTabs.forEach(t => t.classList.remove('active', 'bg-blue-600', 'hover:bg-blue-700'));
      tab.classList.add('active', 'bg-blue-600', 'hover:bg-blue-700');
      currentStatusFilter = tab.getAttribute('data-status');
      currentBookingsPage = 1;
      fetchBookings();
    });
  });

  // Booking Filter Dropdown
  bookingFilter.addEventListener('change', () => {
    currentBookingFilter = bookingFilter.value;
    currentBookingsPage = 1;
    fetchBookings();
  });

  // Search Form
  searchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const searchReference = document.getElementById('searchReference').value.trim();
    currentBookingsPage = 1;
    fetchBookings(currentBookingsPage, currentStatusFilter, currentBookingFilter, searchReference);
  });

  clearSearch.addEventListener('click', () => {
    document.getElementById('searchReference').value = '';
    currentBookingsPage = 1;
    fetchBookings(currentBookingsPage, currentStatusFilter, currentBookingFilter, '');
  });

  // Search Rooms for Walk-in
  searchRoomsBtn.addEventListener('click', async () => {
  const checkInDate = walkinCheckIn.value;
  const checkOutDate = walkinCheckOut.value;
  const roomType = document.getElementById('walkin-room-type').value;

  if (!checkInDate || !checkOutDate) {
    showFeedback('Please select check-in and check-out dates.');
    return;
  }

  try {
    showSpinner(searchRoomsBtn);
    const response = await fetch('/receptionist/rooms/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify({
        check_in_date: formatDateToBackend(checkInDate),
        check_out_date: formatDateToBackend(checkOutDate),
        room_type: roomType || ''
      })
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    const rooms = await response.json(); // Backend returns array directly
    walkinRoomSelect.innerHTML = '<option value="">Select a room</option>';
    if (rooms && rooms.length > 0) {
      rooms.forEach(room => {
        const option = document.createElement('option');
        option.value = room.id;
        option.textContent = `Room ${room.room_number} (${room.room_type}, GHS ${room.price})`;
        walkinRoomSelect.appendChild(option);
      });
      walkinRoomSelect.disabled = false;
      walkinRoomsMessage.classList.remove('hidden');
      walkinBtn.disabled = false;
    } else {
      walkinRoomSelect.disabled = true;
      walkinRoomsMessage.textContent = 'No rooms available for the selected dates.';
      walkinRoomsMessage.classList.remove('hidden');
      walkinBtn.disabled = true;
    }
  } catch (error) {
    console.error('Error searching rooms:', error);
    let message = 'Failed to search rooms. Please try again.';
    if (error.message.includes('INVALID_CHECK_IN')) {
      message = 'Check-in date must be today or in the future.';
    } else if (error.message.includes('INVALID_CHECK_OUT')) {
      message = 'Check-out date must be after check-in date.';
    } else if (error.message.includes('INVALID_DATE_FORMAT')) {
      message = 'Invalid date format. Please use valid dates.';
    }
    showFeedback(message);
    walkinRoomSelect.disabled = true;
    walkinRoomsMessage.classList.add('hidden');
    walkinBtn.disabled = true;
  } finally {
    hideSpinner(searchRoomsBtn);
  }
   });

  // Search Rooms for Modify Booking
  searchModifyRoomsBtn.addEventListener('click', async () => {
  const checkInDate = modifyCheckIn.value;
  const checkOutDate = modifyCheckOut.value;

  if (!checkInDate || !checkOutDate) {
    showFeedback('Please select check-in and check-out dates.');
    return;
  }

  try {
    showSpinner(searchModifyRoomsBtn);
    const response = await fetch('/receptionist/rooms/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify({
        check_in_date: formatDateToBackend(checkInDate),
        check_out_date: formatDateToBackend(checkOutDate),
        exclude_booking_id: parseInt(modifyBookingForm.querySelector('[name="booking_id"]').value)
      })
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    const rooms = await response.json(); // Backend returns array directly
    modifyRoomSelect.innerHTML = '<option value="">Keep Current Room</option>';
    if (rooms && rooms.length > 0) {
      rooms.forEach(room => {
        const option = document.createElement('option');
        option.value = room.id;
        option.textContent = `Room ${room.room_number} (${room.room_type}, GHS ${room.price})`;
        modifyRoomSelect.appendChild(option);
      });
      modifyRoomSelect.disabled = false;
      modifyRoomsMessage.classList.remove('hidden');
    } else {
      modifyRoomSelect.disabled = true;
      modifyRoomsMessage.textContent = 'No rooms available for the selected dates.';
      modifyRoomsMessage.classList.remove('hidden');
    }
  } catch (error) {
    console.error('Error searching rooms for modify:', error);
    let message = 'Failed to search rooms. Please try again.';
    if (error.message.includes('INVALID_CHECK_IN')) {
      message = 'Check-in date must be today or in the future.';
    } else if (error.message.includes('INVALID_CHECK_OUT')) {
      message = 'Check-out date must be after check-in date.';
    } else if (error.message.includes('INVALID_DATE_FORMAT')) {
      message = 'Invalid date format. Please use valid dates.';
    }
    showFeedback(message);
    modifyRoomSelect.disabled = true;
    modifyRoomsMessage.classList.add('hidden');
  } finally {
    hideSpinner(searchModifyRoomsBtn);
  }
   });

  // Walk-in Form Submission
  walkinForm.addEventListener('submit', (e) => {
  e.preventDefault();
  walkinFormData = new FormData(walkinForm);
  walkinFormData.append('request_id', `WALKIN-${Date.now()}`); // Add request_id
  const data = Object.fromEntries(walkinFormData);
  data.check_in_date = formatDateToBackend(data.check_in_date);
  data.check_out_date = formatDateToBackend(data.check_out_date);

  // Populate confirmation modal
  document.getElementById('walkinConfirmName').textContent = data.full_name;
  document.getElementById('walkinConfirmRoom').textContent = walkinRoomSelect.options[walkinRoomSelect.selectedIndex]?.text || 'N/A';
  document.getElementById('walkinConfirmCheckIn').textContent = data.check_in_date;
  document.getElementById('walkinConfirmCheckOut').textContent = data.check_out_date;

  walkinConfirmModal.classList.remove('hidden');
  walkinConfirmModal.setAttribute('aria-hidden', 'false');
   });

  walkinConfirmSubmit.addEventListener('click', async () => {
  try {
    showSpinner(walkinConfirmSubmit);
    const data = Object.fromEntries(walkinFormData);
    data.check_in_date = formatDateToBackend(data.check_in_date);
    data.check_out_date = formatDateToBackend(data.check_out_date);
    data.request_id = `WALKIN-${Date.now()}`; // Ensure unique request_id
    const response = await fetch('/receptionist/bookings/walkin', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify(data)
    });
    const responseData = await response.json();
    if (!response.ok) {
      throw new Error(responseData.error || `HTTP error! status: ${response.status}`);
    }
    walkinConfirmModal.classList.add('hidden');
    walkinConfirmModal.setAttribute('aria-hidden', 'true');
    walkinFormModal.classList.add('hidden');
    walkinFormModal.setAttribute('aria-hidden', 'true');
    walkinForm.reset();
    walkinRoomSelect.innerHTML = '<option value="">Search rooms first</option>';
    walkinRoomSelect.disabled = true;
    walkinRoomsMessage.classList.add('hidden');
    walkinBtn.disabled = true;
    showFeedback('Booking created successfully!', responseData.booking_reference);
    fetchBookings();
  } catch (error) {
    console.error('Error creating walk-in booking:', error);
    let message = 'Failed to create booking. Please try again.';
    if (error.message.includes('ROOM_BOOKED')) {
      message = 'The selected room is already booked for the given dates.';
    } else if (error.message.includes('INVALID_CHECK_IN')) {
      message = 'Check-in date must be today or in the future.';
    } else if (error.message.includes('INVALID_CHECK_OUT')) {
      message = 'Check-out date must be after check-in date.';
    } else if (error.message.includes('DUPLICATE_REQUEST')) {
      message = 'Duplicate booking request detected.';
    } else if (error.message.includes('INVALID_DATE_FORMAT')) {
      message = 'Invalid date format. Please use valid dates.';
    }
    showFeedback(message);
  } finally {
    hideSpinner(walkinConfirmSubmit);
  }
   });

  [walkinConfirmCancel, walkinConfirmCancelBtn].forEach(btn => {
    btn.addEventListener('click', () => {
      walkinConfirmModal.classList.add('hidden');
      walkinConfirmModal.setAttribute('aria-hidden', 'true');
    });
  });

  // Add Room Form Submission
  addRoomForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      showSpinner(document.getElementById('addRoomBtn'));
      const formData = new FormData(addRoomForm);
      const response = await fetch('/receptionist/room/add', {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || `HTTP error! status: ${response.status}`);
      }
      addRoomModal.classList.add('hidden');
      addRoomModal.setAttribute('aria-hidden', 'true');
      addRoomForm.reset();
      showFeedback('Room added successfully!');
      fetchRooms();
    } catch (error) {
      console.error('Error adding room:', error);
      let message = 'Failed to add room. Please try again.';
      if (error.message.includes('ROOM_NUMBER_EXISTS')) {
        message = 'Room number already exists.';
      }
      showFeedback(message);
    } finally {
      hideSpinner(document.getElementById('addRoomBtn'));
    }
  });

  // Modify Booking
  bookingsContent.addEventListener('click', (e) => {
  if (e.target.closest('.modify-booking-btn')) {
    const btn = e.target.closest('.modify-booking-btn');
    const bookingId = btn.dataset.bookingId;
    const email = btn.dataset.email;
    const checkIn = formatDateToDisplay(btn.dataset.checkIn);
    const checkOut = formatDateToDisplay(btn.dataset.checkOut);
    const roomId = btn.dataset.roomId;

    modifyBookingForm.querySelector('[name="booking_id"]').value = bookingId;
    modifyBookingForm.querySelector('[name="email"]').value = email;
    modifyCheckIn.value = checkIn;
    modifyCheckOut.value = checkOut;
    modifyRoomSelect.innerHTML = '<option value="">Keep Current Room</option>';
    modifyRoomSelect.disabled = true;
    modifyRoomsMessage.classList.add('hidden');
    modifyBookingModal.classList.remove('hidden');
    modifyBookingModal.setAttribute('aria-hidden', 'false');
    trapFocus(modifyBookingModal);
  }
  });

  modifyBookingForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  try {
    showSpinner(modifyBookingForm.querySelector('button[type="submit"]'));
    const formData = new FormData(modifyBookingForm);
    const data = Object.fromEntries(formData);
    data.check_in_date = formatDateToBackend(data.check_in_date);
    data.check_out_date = formatDateToBackend(data.check_out_date);
    const response = await fetch(`/receptionist/booking/modify/${data.booking_id}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify(data)
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    modifyBookingModal.classList.add('hidden');
    modifyBookingModal.setAttribute('aria-hidden', 'true');
    showFeedback('Booking modified successfully!');
    fetchBookings();
  } catch (error) {
    console.error('Error modifying booking:', error);
    let message = 'Failed to modify booking. Please try again.';
    if (error.message.includes('ROOM_BOOKED')) {
      message = 'The selected room is already booked for the given dates.';
    } else if (error.message.includes('INVALID_CHECK_IN')) {
      message = 'Check-in date must be today or in the future.';
    } else if (error.message.includes('INVALID_CHECK_OUT')) {
      message = 'Check-out date must be after check-in date.';
    } else if (error.message.includes('GUEST_NOT_FOUND')) {
      message = 'No guest found with that email.';
    } else if (error.message.includes('INVALID_DATE_FORMAT')) {
      message = 'Invalid date format. Please use valid dates.';
    } else if (error.message.includes('INVALID_MODIFICATION')) {
      message = 'Cannot modify a checked-in or checked-out booking.';
    }
    showFeedback(message);
  } finally {
    hideSpinner(modifyBookingForm.querySelector('button[type="submit"]'));
  }
   });

  [modifyCloseBtn, modifyCloseXBtn].forEach(btn => {
    btn.addEventListener('click', () => {
      modifyBookingModal.classList.add('hidden');
      modifyBookingModal.setAttribute('aria-hidden', 'true');
    });
  });

  // Check-In
  bookingsContent.addEventListener('click', async (e) => {
  if (e.target.closest('.check-in-btn')) {
    const btn = e.target.closest('.check-in-btn');
    const bookingId = btn.dataset.bookingId;
    try {
      showSpinner(btn);
      const response = await fetch('/receptionist/booking/update_status', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ booking_id: parseInt(bookingId), status: 'checked-in' })
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }
      showFeedback('Check-in successful!');
      fetchBookings();
    } catch (error) {
      console.error('Error checking in:', error);
      let message = 'Failed to check in. Please try again.';
      if (error.message.includes('PAYMENT_REQUIRED')) {
        message = 'Payment must be completed before check-in.';
      } else if (error.message.includes('INVALID_CHECK_IN_DATE')) {
        message = 'Check-in is only allowed on the check-in date.';
      } else if (error.message.includes('INVALID_MODIFICATION')) {
        message = 'Cannot modify status of checked-in or checked-out booking.';
      }
      showFeedback(message);
    } finally {
      hideSpinner(btn);
    }
  }
   });

  // Check-Out
  bookingsContent.addEventListener('click', async (e) => {
  if (e.target.closest('.check-out-btn')) {
    const btn = e.target.closest('.check-out-btn');
    const bookingId = btn.dataset.bookingId;
    try {
      showSpinner(btn);
      const response = await fetch('/receptionist/bookings/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ booking_id: parseInt(bookingId) })
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }
      showFeedback('Check-out successful!');
      fetchBookings();
    } catch (error) {
      console.error('Error checking out:', error);
      let message = 'Failed to check out. Please try again.';
      if (error.message.includes('PAYMENT_REQUIRED')) {
        message = 'Payment must be completed before check-out.';
      } else if (error.message.includes('INVALID_CHECKOUT')) {
        message = 'Booking must be checked-in to check out.';
      }
      showFeedback(message);
    } finally {
      hideSpinner(btn);
    }
  }
   });

  // Payment
  bookingsContent.addEventListener('click', async (e) => {
  if (e.target.closest('.payment-btn')) {
    const btn = e.target.closest('.payment-btn');
    const bookingId = btn.dataset.bookingId;
    try {
      showSpinner(btn);
      const response = await fetch('/receptionist/booking/update_payment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ booking_id: parseInt(bookingId), payment_status: 'paid' })
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }
      showFeedback('Payment recorded successfully!');
      fetchBookings();
    } catch (error) {
      console.error('Error recording payment:', error);
      let message = 'Failed to record payment. Please try again.';
      if (error.message.includes('INVALID_PAYMENT_UPDATE')) {
        message = 'Cannot set payment to pending for checked-in or checked-out booking.';
      }
      showFeedback(message);
    } finally {
      hideSpinner(btn);
    }
  }
   });

  // Delete Booking
  bookingsContent.addEventListener('click', (e) => {
  if (e.target.closest('.delete-booking-btn')) {
    const btn = e.target.closest('.delete-booking-btn');
    deleteBookingId.value = btn.dataset.bookingId;
    deleteBookingModal.classList.remove('hidden');
    deleteBookingModal.setAttribute('aria-hidden', 'false');
    trapFocus(deleteBookingModal);
  }
   });



  deleteBookingConfirm.addEventListener('click', async () => {
  try {
    showSpinner(deleteBookingConfirm);
    const response = await fetch(`/receptionist/booking/delete/${deleteBookingId.value}`, {
      method: 'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    deleteBookingModal.classList.add('hidden');
    deleteBookingModal.setAttribute('aria-hidden', 'true');
    showFeedback('Booking deleted successfully!');
    fetchBookings();
  } catch (error) {
    console.error('Error deleting booking:', error);
    let message = 'Failed to delete booking. Please try again.';
    if (error.message.includes('INVALID_BOOKING_STATUS')) {
      message = 'Can only delete checked-out or cancelled bookings.';
    }
    showFeedback(message);
  } finally {
    hideSpinner(deleteBookingConfirm);
  }
  });

   // Delete Room
   roomsContent.addEventListener('click', (e) => {
  if (e.target.closest('.delete-room-btn')) {
    const btn = e.target.closest('.delete-room-btn');
    deleteRoomId.value = btn.dataset.roomId;
    deleteRoomModal.classList.remove('hidden');
    deleteRoomModal.setAttribute('aria-hidden', 'false');
    trapFocus(deleteRoomModal);
  }
  });

  deleteRoomConfirm.addEventListener('click', async () => {
  try {
    showSpinner(deleteRoomConfirm);
    const response = await fetch(`/receptionist/room/delete/${deleteRoomId.value}`, {
      method: 'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    deleteRoomModal.classList.add('hidden');
    deleteRoomModal.setAttribute('aria-hidden', 'true');
    showFeedback('Room deleted successfully!');
    fetchRooms();
  } catch (error) {
    console.error('Error deleting room:', error);
    let message = 'Failed to delete room. Please try again.';
    if (error.message.includes('ROOM_ACTIVE')) {
      message = 'Cannot delete room with active bookings.';
    }
    showFeedback(message);
  } finally {
    hideSpinner(deleteRoomConfirm);
  }
  });


  [deleteRoomCancel, deleteRoomCancelBtn].forEach(btn => {
    btn.addEventListener('click', () => {
      deleteRoomModal.classList.add('hidden');
      deleteRoomModal.setAttribute('aria-hidden', 'true');
    });
  });

  // Refresh Dashboard
  refreshDashboard.addEventListener('click', () => {
    currentBookingsPage = 1;
    currentRoomsPage = 1;
    currentStatusFilter = 'all';
    currentBookingFilter = 'all';
    document.getElementById('searchReference').value = '';
    statusTabs.forEach(tab => tab.classList.remove('active', 'bg-blue-600', 'hover:bg-blue-700'));
    statusTabs[0].classList.add('active', 'bg-blue-600', 'hover:bg-blue-700');
    bookingFilter.value = 'all';
    fetchPriorities();
    fetchBookings();
  });

  // Initial Load
  fetchPriorities();
});