document.addEventListener('DOMContentLoaded', () => {
  console.log('manage_booking.js loaded');
  const queryBookingForm = document.getElementById('queryBookingForm');
  const bookingContainer = document.getElementById('bookingContainer');
  const bookingModal = document.getElementById('bookingModal');
  const modifyBookingForm = document.getElementById('modifyBookingForm');
  const queryBtn = document.getElementById('queryBtn');
  const feedbackModal = document.getElementById('feedbackModal');
  const feedbackMessage = document.getElementById('feedbackMessage');
  const feedbackTitle = document.getElementById('feedback-modal-title');
  const bookingReferenceDisplay = document.getElementById('bookingReferenceDisplay');
  const emailInput = document.getElementById('email');
  const bookingReferenceInput = document.getElementById('booking_reference');
  const modifyCheckInDate = document.getElementById('modify_check_in_date');
  const modifyCheckOutDate = document.getElementById('modify_check_out_date');
  const modifyRoomSelect = document.getElementById('modify_room_id');
  const cancelConfirmModal = document.getElementById('cancelConfirmModal');
  const cancelYesBtn = document.getElementById('cancelYesBtn');
  const cancelNoBtn = document.getElementById('cancelNoBtn');
  const bookingCloseBtn = document.getElementById('bookingCloseBtn');
  const modifyCancelBtn = document.getElementById('modifyCancelBtn');
  const feedbackCloseBtn = document.getElementById('feedbackCloseBtn');
  const searchRoomsBtn = document.getElementById('searchRoomsBtn');
  const searchRoomsMessage = document.getElementById('searchRoomsMessage');
  const feedbackCloseXBtn = document.getElementById('feedbackCloseXBtn');

  let isSubmitting = false;
  let currentBooking = null;

  const errorMessages = {
    'MISSING_DATA': 'Please fill in all required fields.',
    'BOOKING_NOT_FOUND': 'Booking not found.',
    'GUEST_NOT_FOUND': 'No guest found with that email.',
    'INVALID_MODIFICATION': 'Cannot modify or cancel a checked-in or checked-out booking.',
    'BOOKING_CANCELLED': 'This booking has been canceled and cannot be managed. Please check your booking reference or contact support.',
    'PAYMENT_REQUIRED': 'Payment must be completed before modification.',
    'ROOM_NOT_FOUND': 'The selected room does not exist.',
    'ROOM_BOOKED': 'This room is already booked for the selected dates.',
    'INVALID_DATE_FORMAT': 'Please enter dates in D MMMM YYYY format (e.g., 1 August 2025).',
    'INVALID_CHECK_IN': 'Check-in date must be today or in the future.',
    'INVALID_CHECK_OUT': 'Check-out date must be after check-in date.',
    'DB_CONNECTION': 'Database connection issue. Please try again later.',
    'SERVER_ERROR': 'An unexpected server error occurred.',
    'NO_ROOMS_AVAILABLE': 'No rooms available for the selected dates.',
    'default': 'Something went wrong. Please try again.'
  };

  // Date conversion functions
  function formatDateToDisplay(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  }

  function formatDateToBackend(dateStr) {
    if (!dateStr) return '';
    try {
      const date = flatpickr.parseDate(dateStr, 'd F Y');
      return date.toISOString().split('T')[0]; // YYYY-MM-DD
    } catch (error) {
      console.error('Error parsing date:', dateStr, error);
      return '';
    }
  }

  function formatCurrency(amount) {
    return amount.toLocaleString('en-GH', { style: 'currency', currency: 'GHS' });
  }

  // Initialize Flatpickr for date inputs
  flatpickr('#modify_check_in_date', {
    dateFormat: 'd F Y',
    minDate: 'today',
    onChange: (selectedDates, dateStr) => {
      modifyCheckInDate.value = dateStr;
      if (selectedDates[0]) {
        const minCheckOut = new Date(selectedDates[0]);
        minCheckOut.setDate(minCheckOut.getDate() + 1);
        modifyCheckOutDate._flatpickr.set('minDate', minCheckOut);
      }
    }
  });

  flatpickr('#modify_check_out_date', {
    dateFormat: 'd F Y',
    minDate: 'tomorrow'
  });

  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      if (isSubmitting) {
        console.log('Debounce blocked execution: isSubmitting true');
        return;
      }
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        func(...args);
      }, wait);
    };
  }

  function closeModal(modalId) {
    console.log(`Closing modal: ${modalId}`);
    const modal = document.getElementById(modalId);
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
    console.log(`Modal classes after hiding ${modalId}: ${modal.classList}`);
    if (modalId === 'modifyModal') {
      bookingModal.classList.remove('hidden');
      bookingModal.setAttribute('aria-hidden', 'false');
      modifyBookingForm.classList.remove('context-active');
      const bookingModalTitle = bookingModal.querySelector('#booking-modal-title');
      if (bookingModalTitle) {
        bookingModalTitle.focus();
      }
    } else if (modalId === 'cancelConfirmModal') {
      bookingModal.classList.remove('hidden');
      bookingModal.setAttribute('aria-hidden', 'false');
      const bookingModalTitle = bookingModal.querySelector('#booking-modal-title');
      if (bookingModalTitle) {
        bookingModalTitle.focus();
      }
    } else if (modalId === 'feedbackModal') {
      if (modifyBookingForm.classList.contains('context-active')) {
        const modifyModal = document.getElementById('modifyModal');
        modifyModal.classList.remove('hidden');
        modifyModal.setAttribute('aria-hidden', 'false');
        const modifyModalTitle = modifyModal.querySelector('#modify-modal-title');
        if (modifyModalTitle) {
          modifyModalTitle.focus();
        }
      } else {
        bookingModal.classList.add('hidden');
        bookingModal.setAttribute('aria-hidden', 'true');
        const modifyModal = document.getElementById('modifyModal');
        modifyModal.classList.add('hidden');
        modifyModal.setAttribute('aria-hidden', 'true');
        cancelConfirmModal.classList.add('hidden');
        cancelConfirmModal.setAttribute('aria-hidden', 'true');
        modifyBookingForm.classList.remove('context-active');
        queryBookingForm.classList.remove('hidden');
        emailInput.focus();
      }
    } else if (modalId === 'bookingModal') {
      queryBookingForm.classList.remove('hidden');
      currentBooking = null;
      emailInput.focus();
    }
  }

  function showFeedback(title, message, type = 'error', bookingReference = null) {
    console.log(`Showing feedback: ${title} - ${message} (type: ${type})`);
    feedbackTitle.innerHTML = `
      <svg class="w-5 h-5 ${type === 'success' ? 'text-green-400' : 'text-red-400'}" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${type === 'success' ? 'M5 13l4 4L19 7' : 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'}" />
      </svg>
      <span>${title}</span>
    `;
    feedbackMessage.textContent = type === 'success' && bookingReference
      ? `Please keep your booking reference for check-in and future modifications.`
      : errorMessages[message] || message;
    feedbackModal.classList.remove('hidden');
    feedbackModal.setAttribute('aria-hidden', 'false');
    if (bookingReference && type === 'success') {
      bookingReferenceDisplay.textContent = `Booking Reference: ${bookingReference}`;
      bookingReferenceDisplay.classList.remove('hidden');
    } else {
      bookingReferenceDisplay.classList.add('hidden');
    }
    feedbackCloseBtn.focus();
  }

  async function fetchAvailableRooms(checkInDate, checkOutDate, excludeBookingId, currentRoomId = '', roomType = '') {
    if (!checkInDate || !checkOutDate) {
      modifyRoomSelect.innerHTML = '<option value="">Select a Room</option>';
      searchRoomsMessage.classList.add('hidden');
      return;
    }
    console.log(`Fetching available rooms for ${checkInDate} to ${checkOutDate}, excluding booking ID: ${excludeBookingId}, current room ID: ${currentRoomId}, room type: ${roomType}`);
    try {
      const spinner = searchRoomsBtn.querySelector('.spinner');
      if (spinner) spinner.classList.remove('hidden');
      searchRoomsBtn.disabled = true;
      const minSpinnerTime = new Promise(resolve => setTimeout(resolve, 1000));
      const response = await fetch('/available_rooms', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          check_in_date: formatDateToBackend(checkInDate),
          check_out_date: formatDateToBackend(checkOutDate),
          exclude_booking_id: excludeBookingId,
          current_room_id: currentRoomId,
          room_type: roomType
        })
      });
      const [data] = await Promise.all([response.json(), minSpinnerTime]);
      console.log('fetchAvailableRooms response:', data);
      if (response.ok) {
        modifyRoomSelect.innerHTML = '<option value="">Select a Room</option>';
        if (data.rooms.length === 0) {
          showFeedback('Error', 'NO_ROOMS_AVAILABLE', 'error');
        } else {
          data.rooms.forEach(room => {
            const option = document.createElement('option');
            option.value = room.id;
            option.textContent = room.is_current
              ? `Keep my current room: ${room.room_number} (${room.room_type}, ${formatCurrency(room.price)})`
              : `${room.room_number} (${room.room_type}, ${formatCurrency(room.price)})`;
            modifyRoomSelect.appendChild(option);
          });
          if (currentRoomId) {
            modifyRoomSelect.value = currentRoomId;
          }
          searchRoomsMessage.classList.remove('hidden');
        }
      } else {
        showFeedback('Error', data.code || 'Failed to load rooms', 'error');
      }
    } catch (error) {
      console.error('fetchAvailableRooms error:', error);
      showFeedback('Error', 'Error loading rooms', 'error');
    } finally {
      const spinner = searchRoomsBtn.querySelector('.spinner');
      if (spinner) spinner.classList.add('hidden');
      searchRoomsBtn.disabled = false;
    }
  }

  const debouncedQuery = debounce(async (e) => {
    e.preventDefault();
    e.stopPropagation();
    console.log('Query form submitted');
    if (isSubmitting) {
      console.log('Query submission blocked: isSubmitting true');
      return;
    }
    isSubmitting = true;
    queryBtn.disabled = true;
    const spinner = queryBtn.querySelector('.spinner');
    if (spinner) spinner.classList.remove('hidden');

    const data = {
      email: emailInput.value.trim(),
      booking_reference: bookingReferenceInput.value.trim()
    };
    console.log('Sending query data:', data);

    try {
      const minSpinnerTime = new Promise(resolve => setTimeout(resolve, 1000));
      const response = await fetch('/manage_booking', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(data)
      });
      const [result] = await Promise.all([response.json(), minSpinnerTime]);
      console.log('manage_booking response:', result);
      if (response.ok) {
        currentBooking = result.booking;
        console.log('Current booking set:', currentBooking);
        queryBookingForm.classList.add('hidden');
        bookingModal.classList.remove('hidden');
        bookingModal.setAttribute('aria-hidden', 'false');
        bookingContainer.innerHTML = `
          <h3 class="text-lg font-semibold text-white flex items-center gap-2" id="booking-modal-title">
            <svg class="w-5 h-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            Booking: ${currentBooking.booking_reference}
          </h3>
          <p class="text-gray-300"><strong>Guest:</strong> ${currentBooking.guest.full_name}</p>
          <p class="text-gray-300"><strong>Email:</strong> ${currentBooking.guest.email}</p>
          <p class="text-gray-300"><strong>Phone:</strong> ${currentBooking.guest.phone}</p>
          <p class="text-gray-300"><strong>Room:</strong> ${currentBooking.room.room_number} (${currentBooking.room.room_type}, ${formatCurrency(currentBooking.room.price)})</p>
          <p class="text-gray-300"><strong>Check-In:</strong> ${formatDateToDisplay(currentBooking.check_in_date)}</p>
          <p class="text-gray-300"><strong>Check-Out:</strong> ${formatDateToDisplay(currentBooking.check_out_date)}</p>
          <p class="text-gray-300"><strong>Status:</strong> ${currentBooking.status}</p>
          <p class="text-gray-300"><strong>Payment Status:</strong> ${currentBooking.payment_status}</p>
          ${currentBooking.payment_status !== 'paid' ? `
            <p class="text-yellow-500 mt-4 flex items-center gap-2">
              <svg class="w-5 h-5 text-yellow-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              You must complete payment to modify this booking.
            </p>
          ` : ''}
          <div class="mt-4 flex justify-end gap-4">
            <button id="cancelBtn" class="p-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition flex items-center gap-2 ${currentBooking.status === 'checked-in' || currentBooking.status === 'checked-out' || currentBooking.status === 'cancelled' ? 'opacity-50 cursor-not-allowed' : ''}"
                    ${currentBooking.status === 'checked-in' || currentBooking.status === 'checked-out' || currentBooking.status === 'cancelled' ? 'disabled' : ''}
                    aria-label="Cancel booking">
              <span class="spinner hidden w-5 h-5 border-2 border-blue-400 border-t-blue-600 rounded-full animate-spin"></span>
              <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
              <span>Cancel Booking</span>
            </button>
            <button id="modifyBtn" class="p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2 ${currentBooking.payment_status !== 'paid' || currentBooking.status === 'checked-in' || currentBooking.status === 'checked-out' || currentBooking.status === 'cancelled' ? 'opacity-50 cursor-not-allowed' : ''}"
                    ${currentBooking.payment_status !== 'paid' || currentBooking.status === 'checked-in' || currentBooking.status === 'checked-out' || currentBooking.status === 'cancelled' ? 'disabled' : ''}
                    aria-label="Modify booking">
              <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              <span>Modify Booking</span>
            </button>
          </div>
        `;
        const cancelBtn = document.getElementById('cancelBtn');
        const modifyBtn = document.getElementById('modifyBtn');
        if (cancelBtn) cancelBtn.addEventListener('click', () => {
          console.log('Cancel button clicked');
          bookingModal.classList.add('hidden');
          bookingModal.setAttribute('aria-hidden', 'true');
          cancelConfirmModal.classList.remove('hidden');
          cancelConfirmModal.setAttribute('aria-hidden', 'false');
          cancelYesBtn.focus();
        });
        if (modifyBtn) modifyBtn.addEventListener('click', showModifyForm);
      } else {
        showFeedback('Error', result.code || 'Failed to find booking', 'error');
      }
    } catch (error) {
      console.error('manage_booking error:', error);
      showFeedback('Error', errorMessages[error.message] || 'Error querying booking', 'error');
    } finally {
      isSubmitting = false;
      queryBtn.disabled = false;
      if (spinner) spinner.classList.add('hidden');
    }
  }, 500);

  const debouncedCancel = debounce(async () => {
    if (isSubmitting || !currentBooking) {
      console.log('Cancel submission blocked: isSubmitting or no booking');
      return;
    }
    isSubmitting = true;
    cancelYesBtn.disabled = true;
    const spinner = cancelYesBtn.querySelector('.spinner');
    spinner.classList.remove('hidden');

    try {
      const minSpinnerTime = new Promise(resolve => setTimeout(resolve, 1000));
      const response = await fetch('/cancel_booking', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          email: currentBooking.guest.email,
          booking_reference: currentBooking.booking_reference
        })
      });
      const [result] = await Promise.all([response.json(), minSpinnerTime]);
      console.log('cancel_booking response:', result);
      if (response.ok) {
        showFeedback('Success', 'Booking cancelled successfully', 'success', result.booking_reference);
        cancelConfirmModal.classList.add('hidden');
        cancelConfirmModal.setAttribute('aria-hidden', 'true');
        bookingModal.classList.add('hidden');
        bookingModal.setAttribute('aria-hidden', 'true');
        queryBookingForm.classList.remove('hidden');
        currentBooking = null;
      } else {
        showFeedback('Error', result.code || 'Error cancelling booking', 'error');
      }
    } catch (error) {
      console.error('cancel_booking error:', error);
      showFeedback('Error', errorMessages[error.message] || 'Error cancelling booking', 'error');
    } finally {
      isSubmitting = false;
      cancelYesBtn.disabled = false;
      spinner.classList.add('hidden');
    }
  }, 500);

  const debouncedModifySubmit = debounce(async (e) => {
    console.log('Modify form submit event triggered');
    e.preventDefault();
    e.stopPropagation();
    console.log('Modify form submitted');
    if (isSubmitting || !currentBooking) {
      console.log('Modify submission blocked: isSubmitting=', isSubmitting, 'currentBooking=', currentBooking);
      return;
    }
    isSubmitting = true;
    const modifySubmitBtn = document.getElementById('modifySubmitBtn');
    modifySubmitBtn.disabled = true;
    const spinner = modifySubmitBtn.querySelector('.spinner');
    if (spinner) spinner.classList.remove('hidden');

    const data = {
      email: currentBooking.guest.email,
      request_id: `REQ${Date.now()}${Math.floor(Math.random() * 1000)}`
    };
    const roomId = modifyRoomSelect.value;
    const checkInDate = modifyCheckInDate.value;
    const checkOutDate = modifyCheckOutDate.value;

    console.log('Form values:', { roomId, checkInDate, checkOutDate });

    if (roomId && roomId !== currentBooking.room.id.toString()) {
      data.room_id = parseInt(roomId);
    }
    if (checkInDate && checkInDate !== formatDateToDisplay(currentBooking.check_in_date)) {
      data.check_in_date = formatDateToBackend(checkInDate);
    }
    if (checkOutDate && checkOutDate !== formatDateToDisplay(currentBooking.check_out_date)) {
      data.check_out_date = formatDateToBackend(checkOutDate);
    }

    if (!Object.keys(data).some(key => ['room_id', 'check_in_date', 'check_out_date'].includes(key))) {
      console.log('No changes detected in form fields');
      showFeedback('Error', 'Please change at least one field (room, check-in, or check-out)', 'error');
      isSubmitting = false;
      modifySubmitBtn.disabled = false;
      spinner.classList.add('hidden');
      return;
    }

    console.log('Sending modify data:', data);
    try {
      const minSpinnerTime = new Promise(resolve => setTimeout(resolve, 1000));
      const response = await fetch(`/modify_booking/${currentBooking.booking_reference}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(data)
      });
      const [result] = await Promise.all([response.json(), minSpinnerTime]);
      console.log('modify_booking response:', result);
      if (response.ok) {
        showFeedback('Success', 'Booking modified successfully', 'success', result.booking_reference);
        modifyBookingForm.classList.remove('context-active');
      } else {
        showFeedback('Error', result.code || 'Failed to modify booking', 'error');
      }
    } catch (error) {
      console.error('modify_booking error:', error);
      showFeedback('Error', errorMessages[error.message] || 'Error modifying booking', 'error');
    } finally {
      isSubmitting = false;
      modifySubmitBtn.disabled = false;
      if (spinner) spinner.classList.add('hidden');
    }
  }, 500);

  function showModifyForm() {
    if (!currentBooking) {
      console.log('showModifyForm blocked: no currentBooking');
      return;
    }
    console.log('Showing modify form for booking:', currentBooking.booking_reference);
    bookingModal.classList.add('hidden');
    bookingModal.setAttribute('aria-hidden', 'true');
    const modifyModal = document.getElementById('modifyModal');
    modifyModal.classList.remove('hidden');
    modifyModal.setAttribute('aria-hidden', 'false');
    modifyBookingForm.classList.add('context-active');
    modifyBookingForm.querySelector('input[name="booking_reference"]').value = currentBooking.booking_reference;
    modifyBookingForm.querySelector('input[name="email"]').value = currentBooking.guest.email;
    modifyCheckInDate.value = formatDateToDisplay(currentBooking.check_in_date);
    modifyCheckOutDate.value = formatDateToDisplay(currentBooking.check_out_date);
    modifyRoomSelect.innerHTML = '<option value="">Select a Room</option>';
    searchRoomsMessage.classList.add('hidden');
    const firstInput = modifyModal.querySelector('input');
    if (firstInput) {
      firstInput.focus();
    }
  }

  if (queryBookingForm) {
    queryBookingForm.addEventListener('submit', (e) => {
      console.log('Query form submit event captured');
      e.preventDefault();
      debouncedQuery(e);
    });
    console.log('Query form event listener attached');
  } else {
    console.error('queryBookingForm not found in DOM');
  }
  if (modifyBookingForm) {
    modifyBookingForm.addEventListener('submit', (e) => {
      console.log('Modify form submit event listener triggered');
      debouncedModifySubmit(e);
    });
    console.log('Modify form event listener attached');
  } else {
    console.error('modifyBookingForm not found in DOM');
  }
  if (modifyCancelBtn) {
    modifyCancelBtn.removeEventListener('click', modifyCancelHandler);
    modifyCancelBtn.addEventListener('click', modifyCancelHandler);
    console.log('Modify cancel button event listener attached');
  }
  function modifyCancelHandler() {
    console.log('modifyCancelBtn clicked');
    const modifyModal = document.getElementById('modifyModal');
    modifyModal.classList.add('hidden');
    modifyModal.setAttribute('aria-hidden', 'true');
    modifyBookingForm.classList.remove('context-active');
    const bookingModalTitle = bookingModal.querySelector('#booking-modal-title');
    if (bookingModalTitle) {
      bookingModalTitle.focus();
    }
    bookingModal.classList.remove('hidden');
    bookingModal.setAttribute('aria-hidden', 'false');
  }
  const modifyCloseBtn = document.getElementById('modifyCloseBtn');
  if (modifyCloseBtn) {
    modifyCloseBtn.removeEventListener('click', modifyCloseHandler);
    modifyCloseBtn.addEventListener('click', modifyCloseHandler);
    console.log('Modify close button event listener attached');
  } else {
    console.error('modifyCloseBtn not found in DOM');
  }
  function modifyCloseHandler() {
    console.log('modifyCloseBtn clicked');
    closeModal('modifyModal');
  }
  if (cancelNoBtn) {
    cancelNoBtn.addEventListener('click', () => closeModal('cancelConfirmModal'));
    console.log('Cancel no button event listener attached');
  }
  if (cancelYesBtn) {
    cancelYesBtn.addEventListener('click', debouncedCancel);
    console.log('Cancel yes button event listener attached');
  }
  if (bookingCloseBtn) {
    bookingCloseBtn.removeEventListener('click', closeModalHandler);
    bookingCloseBtn.addEventListener('click', closeModalHandler);
    console.log('Booking close button event listener attached');
  }
  function closeModalHandler() {
    closeModal('bookingModal');
  }
  if (feedbackCloseBtn) {
    feedbackCloseBtn.addEventListener('click', () => closeModal('feedbackModal'));
    console.log('Feedback close button event listener attached');
  }
  if (feedbackCloseXBtn) {
    feedbackCloseXBtn.addEventListener('click', () => closeModal('feedbackModal'));
    console.log('Feedback close X button event listener attached');
  } else {
    console.error('feedbackCloseXBtn not found in DOM');
  }
  if (searchRoomsBtn) {
    searchRoomsBtn.addEventListener('click', () => {
      console.log('searchRoomsBtn clicked');
      fetchAvailableRooms(
        modifyCheckInDate.value,
        modifyCheckOutDate.value,
        currentBooking?.id,
        currentBooking?.room.id,
        currentBooking?.room.room_type
      );
    });
    console.log('Search rooms button event listener attached');
  } else {
    console.error('searchRoomsBtn not found in DOM');
  }
  if (queryBookingForm) {
    queryBookingForm.addEventListener('click', (e) => {
      if (!queryBookingForm.dataset.jsEnabled) {
        e.preventDefault();
        alert('JavaScript is required to manage bookings. Please try enabling JavaScript.');
      }
    });
    queryBookingForm.dataset.jsEnabled = 'true';
  }
});