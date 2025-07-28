document.addEventListener("DOMContentLoaded", function () {
  console.log('booking.js loaded');
  const form = document.getElementById("availability-form");
  const checkIn = document.getElementById("check-in");
  const checkOut = document.getElementById("check-out");
  const roomsContainer = document.getElementById("rooms-container");
  const spinner = document.getElementById("spinner");
  const availabilityBtn = form ? form.querySelector('button[type="submit"]') : null;
  const categoryTabs = document.querySelectorAll(".category-tab");
  const bookingModal = document.getElementById("booking-modal");
  const bookingForm = document.getElementById("booking-form");
  const confirmationModal = document.getElementById("confirmation-modal");
  const errorModal = document.getElementById("error-modal");
  const modalClose = document.getElementById("modal-close");
  const closeConfirmationModal = document.getElementById("close-confirmation-modal");
  const closeConfirmationModalX = document.getElementById("close-confirmation-modal-x");
  const closeErrorModal = document.getElementById("close-error-modal");
  const closeErrorModalX = document.getElementById("close-error-modal-x");

  let availableRooms = [];
  let searchDates = { checkIn: '', checkOut: '' };
  let isSubmitting = false;

  // Room category images
  const roomCategories = {
    Single: {
      image: 'https://images.unsplash.com/photo-1611892440504-42a792e24d32',
      description: 'Cozy single room with one bed'
    },
    Double: {
      image: 'https://images.unsplash.com/photo-1598928636135-d146006ff4be',
      description: 'Spacious double room with two beds or one large bed'
    },
    Suite: {
      image: 'https://images.unsplash.com/photo-1578683014728-903d95dab136',
      description: 'Luxury suite with living area and premium amenities'
    }
  };

  // Error message mapping aligned with backend
  const errorMessages = {
    'UNAUTHORIZED': 'You are not authorized to perform this action.',
    'MISSING_DATA': 'Please fill in all required fields.',
    'INVALID_CHECK_IN': 'Check-in date must be today or in the future.',
    'INVALID_CHECK_OUT': 'Check-out date must be after check-in date.',
    'INVALID_DATE_FORMAT': 'Please enter dates in D MMMM YYYY format (e.g., 1 August 2025).',
    'ROOM_NOT_FOUND': 'The selected room does not exist.',
    'ROOM_BOOKED': 'This room is already booked for the selected dates.',
    'BOOKING_NOT_FOUND': 'The booking was not found.',
    'INVALID_MODIFICATION': 'Cannot modify a checked-in or checked-out booking.',
    'GUEST_NOT_FOUND': 'No guest found with that email.',
    'PAYMENT_REQUIRED': 'Payment must be completed before this action.',
    'INVALID_CHECK_IN_DATE': 'Check-in is only allowed on the check-in date.',
    'INVALID_PAYMENT_STATUS': 'Invalid payment status selected.',
    'INVALID_PAYMENT_UPDATE': 'Cannot set payment to pending for this booking.',
    'INVALID_CHECKOUT': 'Booking must be checked-in to check out.',
    'ROOM_EXISTS': 'A room with this number already exists.',
    'ROOM_HAS_BOOKINGS': 'Cannot delete a room with active or future bookings.',
    'SERVER_ERROR': 'An unexpected server error occurred.',
    'NO_ROOMS_AVAILABLE': 'No rooms available for your selected dates. Please try different dates.',
    'ROOM_NOT_AVAILABLE': 'The selected room is not available.',
    'DUPLICATE_REQUEST': 'This booking request has already been submitted.',
    'DB_CONNECTION': 'Database connection issue. Please try again.',
    'INVALID_ROOM_ID': 'Invalid room ID selected.',
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

  // Initialize Flatpickr
  if (checkIn) {
    flatpickr('#check-in', {
      dateFormat: 'd F Y',
      minDate: 'today',
      onChange: (selectedDates, dateStr) => {
        console.log('Check-in date selected:', dateStr);
        checkIn.value = dateStr;
        if (selectedDates[0]) {
          const minCheckOut = new Date(selectedDates[0]);
          minCheckOut.setDate(minCheckOut.getDate() + 1);
          checkOut._flatpickr.set('minDate', minCheckOut);
        }
      }
    });
  } else {
    console.error('check-in input not found in DOM');
  }

  if (checkOut) {
    flatpickr('#check-out', {
      dateFormat: 'd F Y',
      minDate: 'tomorrow'
    });
  } else {
    console.error('check-out input not found in DOM');
  }

  // Set default check-in date only
  if (checkIn) {
    checkIn.value = formatDateToDisplay(new Date().toISOString().split('T')[0]);
  }
  if (checkOut) {
    checkOut.value = '';
  }

  // Handle query parameters for pre-filled booking modal
  function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    return {
      room_id: params.get('room_id'),
      guest_name: params.get('guest_name'),
      guest_email: params.get('guest_email'),
      guest_phone: params.get('guest_phone')
    };
  }

  async function initializeBookingModalFromQuery() {
    const { room_id, guest_name, guest_email, guest_phone } = getQueryParams();
    if (room_id && guest_name && guest_email && guest_phone && checkIn.value && checkOut.value) {
      console.log('Query params detected:', { room_id, guest_name, guest_email, guest_phone });
      try {
        const response = await fetch('/search_rooms?page=1', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
          body: JSON.stringify({
            check_in_date: formatDateToBackend(checkIn.value),
            check_out_date: formatDateToBackend(checkOut.value)
          })
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.code || 'Failed to load rooms');
        }
        const room = data.rooms.find(r => r.id === parseInt(room_id));
        if (room) {
          searchDates.checkIn = checkIn.value;
          searchDates.checkOut = checkOut.value;
          availableRooms = data.rooms;
          openBookingModal(room.id, room.room_number, room.room_type, room.price);
          const form = bookingForm;
          if (form) {
            form.querySelector('input[name="guest_name"]').value = guest_name;
            form.querySelector('input[name="guest_email"]').value = guest_email;
            form.querySelector('input[name="guest_phone"]').value = guest_phone;
          } else {
            console.error('booking-form not found for query params population');
            showErrorModal('Error', 'Booking form not found.');
          }
        } else {
          showErrorModal('Room Not Found', errorMessages['ROOM_NOT_FOUND']);
        }
      } catch (error) {
        console.error('Error initializing booking modal from query params:', error.message);
        showErrorModal('Error', errorMessages[error.message] || errorMessages['default']);
      }
    } else {
      console.log('No or incomplete query params for auto-booking:', { room_id, guest_name, guest_email, guest_phone });
    }
  }

  // Category tab styles
  const tabStyles = {
    Single: { bg: 'bg-blue-600', text: 'text-white', border: 'border-blue-600', hover: 'hover:bg-blue-600' },
    Double: { bg: 'bg-blue-600', text: 'text-white', border: 'border-blue-600', hover: 'hover:bg-blue-600' },
    Suite: { bg: 'bg-blue-600', text: 'text-white', border: 'border-blue-600', hover: 'hover:bg-blue-600' }
  };

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
    if (!modal) {
      console.error(`Modal ${modalId} not found`);
      return;
    }
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
    console.log(`Modal classes after hiding ${modalId}: ${modal.classList}`);
  }

  function showErrorModal(title, message) {
    console.log(`Showing error modal: ${title} - ${message}`);
    const titleElement = document.getElementById('error-modal-title');
    const messageElement = document.getElementById('error-message');
    if (!titleElement || !messageElement) {
      console.error('Error modal elements not found');
      return;
    }
    titleElement.textContent = title;
    messageElement.textContent = message;
    errorModal.classList.remove('hidden');
    errorModal.setAttribute('aria-hidden', 'false');
    closeErrorModal.focus();
  }

  function showConfirmationModal(bookingReference) {
    console.log(`Showing confirmation modal: ${bookingReference}`);
    document.getElementById('confirmed-booking-id').textContent = bookingReference;
    confirmationModal.classList.remove('hidden');
    confirmationModal.setAttribute('aria-hidden', 'false');
    closeConfirmationModal.focus();
  }

  async function fetchRooms(checkinDate, checkoutDate) {
    console.log('Fetching rooms for dates:', { checkinDate, checkoutDate });
    try {
      spinner.classList.remove('hidden');
      roomsContainer.classList.add('opacity-50');
      const minSpinnerTime = new Promise(resolve => setTimeout(resolve, 1000));
      const response = await fetch('/search_rooms?page=1', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify({
          check_in_date: formatDateToBackend(checkinDate),
          check_out_date: formatDateToBackend(checkoutDate)
        })
      });

      const [data] = await Promise.all([response.json(), minSpinnerTime]);
      console.log('fetchRooms response:', data);
      if (!response.ok) {
        throw new Error(data.code || 'Failed to load rooms');
      }

      availableRooms = data.rooms || [];
      searchDates = { checkIn: checkinDate, checkOut: checkoutDate };

      const activeTab = document.querySelector(".category-tab.active-tab");
      const activeCategory = activeTab ? activeTab.dataset.category : "Single";

      if (availableRooms.length === 0) {
        showErrorModal("No Rooms", errorMessages['NO_ROOMS_AVAILABLE']);
        roomsContainer.innerHTML = `<p class="text-gray-300 text-center col-span-full">
          No rooms available for ${formatDateToDisplay(data.check_in)} to ${formatDateToDisplay(data.check_out)}.
        </p>`;
      } else {
        renderRoomsByCategory(activeCategory);
        const dateRange = document.getElementById('date-range');
        const selectedDates = document.getElementById('selected-dates');
        if (dateRange && selectedDates) {
          dateRange.textContent = `${formatDateToDisplay(data.check_in)} to ${formatDateToDisplay(data.check_out)}`;
          selectedDates.classList.remove('hidden');
        }
      }
    } catch (error) {
      console.error('fetchRooms error:', error.message);
      showErrorModal("Error", errorMessages[error.message] || errorMessages['default']);
    } finally {
      spinner.classList.add('hidden');
      roomsContainer.classList.remove('opacity-50');
    }
  }

  function renderRoomsByCategory(category) {
    console.log('Rendering rooms for category:', category);
    const filtered = availableRooms.filter(room => room.room_type.toLowerCase() === category.toLowerCase());
    roomsContainer.innerHTML = '';

    if (filtered.length === 0) {
      roomsContainer.innerHTML = `
        <p class="text-gray-300 text-center col-span-full">
          No ${category} rooms available for selected dates.
        </p>`;
      return;
    }

    filtered.forEach(room => {
      const roomImage = roomCategories[room.room_type]?.image || 'https://images.unsplash.com/photo-1611892440504-42a792e24d32';
      const roomDescription = roomCategories[room.room_type]?.description || 'Room description';
      const card = `
        <div class="bg-gray-700 rounded-xl shadow-lg hover:shadow-xl transition duration-300" aria-label="Room ${room.room_number}">
          <img src="${roomImage}" alt="${roomDescription}" class="w-full h-48 object-cover">
          <div class="p-4">
            <h3 class="text-xl font-semibold text-white mb-2">Room ${room.room_number}</h3>
            <p class="text-gray-300 mb-2">${room.room_type} room</p>
            <p class="text-gray-300 mb-2">${roomDescription}</p>
            <p class="text-blue-400 font-bold text-lg">${formatCurrency(room.price)} / night</p>
            <button class="book-btn mt-3 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition w-full flex items-center justify-center gap-2"
                    data-room-id="${room.id}"
                    data-room-number="${room.room_number}"
                    data-room-type="${room.room_type}"
                    data-room-price="${room.price}"
                    aria-label="Book Room ${room.room_number}">
              <span class="spinner hidden w-5 h-5 border-2 border-blue-400 border-t-blue-600 rounded-full animate-spin"></span>
              <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              Book Now
            </button>
          </div>
        </div>`;
      roomsContainer.insertAdjacentHTML("beforeend", card);
    });

    addBookButtonListeners();
  }

  function addBookButtonListeners() {
    document.querySelectorAll('.book-btn').forEach(button => {
      button.removeEventListener('click', handleBookButtonClick); // Prevent duplicate listeners
      button.addEventListener('click', handleBookButtonClick);
    });
  }

  function handleBookButtonClick() {
    console.log('Book button clicked:', this.dataset.roomId);
    openBookingModal(
      this.dataset.roomId,
      this.dataset.roomNumber,
      this.dataset.roomType,
      this.dataset.roomPrice
    );
  }

  function openBookingModal(roomId, roomNumber, roomType, price) {
    console.log('Opening booking modal:', { roomId, roomNumber, roomType, price });
    const modalRoomName = document.getElementById('modal-room-name');
    const modalRoomId = document.getElementById('modal-room-id');
    if (!modalRoomName || !modalRoomId || !bookingForm) {
      console.error('Booking modal elements missing:', { modalRoomName: !!modalRoomName, modalRoomId: !!modalRoomId, bookingForm: !!bookingForm });
      showErrorModal('Error', 'Booking form is not properly configured.');
      return;
    }
    modalRoomName.textContent = `${roomType} - Room ${roomNumber}`;
    modalRoomId.value = roomId;
    bookingModal.classList.remove('hidden');
    bookingModal.setAttribute('aria-hidden', 'false');
    const nameInput = bookingForm.querySelector('input[name="guest_name"]');
    if (nameInput) {
      nameInput.focus();
    } else {
      console.error('guest_name input not found in booking form');
    }
  }

  async function handleFormSubmit(e) {
    e.preventDefault();
    e.stopPropagation();
    console.log('Availability form submit event triggered');

    if (isSubmitting) {
      console.log('Form submission blocked: isSubmitting true');
      return;
    }
    isSubmitting = true;
    const buttonSpinner = availabilityBtn ? availabilityBtn.querySelector('.spinner') : null;
    if (buttonSpinner) buttonSpinner.classList.remove('hidden');
    if (availabilityBtn) availabilityBtn.disabled = true;

    try {
      const checkinDate = checkIn.value;
      const checkoutDate = checkOut.value;

      console.log('Form values:', { checkinDate, checkoutDate });

      if (!checkinDate || !checkoutDate) {
        showErrorModal("Missing Dates", errorMessages['MISSING_DATA']);
        return;
      }

      const checkInParsed = flatpickr.parseDate(checkinDate, 'd F Y');
      const checkOutParsed = checkoutDate ? flatpickr.parseDate(checkoutDate, 'd F Y') : null;
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      if (checkInParsed < today) {
        showErrorModal("Invalid Check-In", errorMessages['INVALID_CHECK_IN']);
        return;
      }

      if (checkOutParsed && checkOutParsed <= checkInParsed) {
        showErrorModal("Invalid Check-Out", errorMessages['INVALID_CHECK_OUT']);
        return;
      }

      await Promise.all([
        fetchRooms(checkinDate, checkoutDate),
        new Promise(resolve => setTimeout(resolve, 1000))
      ]);
    } catch (error) {
      console.error('Form submit error:', error.message);
      showErrorModal("Error", errorMessages[error.message] || errorMessages['default']);
    } finally {
      isSubmitting = false;
      if (buttonSpinner) buttonSpinner.classList.add('hidden');
      if (availabilityBtn) availabilityBtn.disabled = false;
    }
  }

  async function handleBookingSubmit(e) {
    e.preventDefault();
    e.stopPropagation();
    console.log('Booking form submit event triggered');

    if (isSubmitting) {
      console.log('Booking submission blocked: isSubmitting true');
      return;
    }
    isSubmitting = true;
    const submitBtn = bookingForm.querySelector('.submit-btn');
    const buttonText = submitBtn ? submitBtn.querySelector('.button-text') : null;
    const buttonSpinner = submitBtn ? submitBtn.querySelector('.spinner') : null;
    if (buttonText) buttonText.classList.add('hidden');
    if (buttonSpinner) buttonSpinner.classList.remove('hidden');
    if (submitBtn) submitBtn.disabled = true;

    try {
      const roomId = parseInt(bookingForm.querySelector('input[name="room_id"]').value);
      const guestName = bookingForm.querySelector('input[name="guest_name"]')?.value;
      const guestEmail = bookingForm.querySelector('input[name="guest_email"]')?.value;
      const guestPhone = bookingForm.querySelector('input[name="guest_phone"]')?.value;

      console.log('Booking form data:', { roomId, guestName, guestEmail, guestPhone, checkIn: searchDates.checkIn, checkOut: searchDates.checkOut });

      if (!roomId || !guestName || !guestEmail || !guestPhone || !searchDates.checkIn || !searchDates.checkOut) {
        console.error('Missing required booking fields:', { roomId, guestName, guestEmail, guestPhone, checkIn: searchDates.checkIn, checkOut: searchDates.checkOut });
        throw new Error('MISSING_DATA');
      }

      const minSpinnerTime = new Promise(resolve => setTimeout(resolve, 1000));
      const response = await fetch('/create_booking', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify({
          room_id: roomId,
          full_name: guestName,
          email: guestEmail,
          phone: guestPhone,
          check_in_date: formatDateToBackend(searchDates.checkIn),
          check_out_date: formatDateToBackend(searchDates.checkOut),
          request_id: `REQ${Date.now()}${Math.floor(Math.random() * 1000)}`
        })
      });

      const [data] = await Promise.all([response.json(), minSpinnerTime]);
      console.log('Booking response:', data);
      if (!response.ok) {
        throw new Error(data.code || 'Booking failed');
      }

      availableRooms = availableRooms.filter(room => room.id !== roomId);
      bookingForm.reset();
      closeModal('booking-modal');
      showConfirmationModal(data.booking_reference);

      const activeTab = document.querySelector(".category-tab.active-tab");
      const activeCategory = activeTab ? activeTab.dataset.category : "Single";
      renderRoomsByCategory(activeCategory);
    } catch (error) {
      console.error('Booking error:', error.message);
      showErrorModal('Booking Failed', errorMessages[error.message] || errorMessages['default']);
    } finally {
      isSubmitting = false;
      if (buttonText) buttonText.classList.remove('hidden');
      if (buttonSpinner) buttonSpinner.classList.add('hidden');
      if (submitBtn) submitBtn.disabled = false;
    }
  }

  const debouncedBookingSubmit = debounce(handleBookingSubmit, 500);

  // Event listeners
  if (form) {
    form.addEventListener('submit', (e) => {
      console.log('Availability form submit event triggered');
      handleFormSubmit(e);
    });
    console.log('Availability form event listener attached');
  } else {
    console.error('availability-form not found in DOM');
  }
  if (bookingForm) {
    bookingForm.addEventListener('submit', (e) => {
      console.log('Booking form submit event triggered');
      debouncedBookingSubmit(e);
    });
    console.log('Booking form event listener attached');
  } else {
    console.error('booking-form not found in DOM');
  }
  if (availabilityBtn) {
    availabilityBtn.addEventListener('click', () => {
      console.log('Check Availability button clicked');
    });
  } else {
    console.error('availabilityBtn not found in DOM');
  }
  if (modalClose) {
    modalClose.addEventListener('click', () => closeModal('booking-modal'));
  } else {
    console.error('modal-close not found in DOM');
  }
  if (closeConfirmationModal) {
    closeConfirmationModal.addEventListener('click', () => closeModal('confirmation-modal'));
  }
  if (closeConfirmationModalX) {
    closeConfirmationModalX.addEventListener('click', () => closeModal('confirmation-modal'));
  }
  if (closeErrorModal) {
    closeErrorModal.addEventListener('click', () => closeModal('error-modal'));
  }
  if (closeErrorModalX) {
    closeErrorModalX.addEventListener('click', () => closeModal('error-modal'));
  }

  categoryTabs.forEach((tab) => {
    tab.addEventListener("click", async () => {
      console.log('Category tab clicked:', tab.dataset.category);
      categoryTabs.forEach((btn) => {
        btn.classList.remove(
          'bg-blue-600', 'text-white', 'shadow-md', 'border-blue-600', 'active-tab'
        );
        btn.classList.add('text-gray-300', 'bg-gray-700', 'border', 'border-gray-600', 'hover:bg-blue-600', 'hover:text-white');
      });

      const selectedCategory = tab.dataset.category;
      const styles = tabStyles[selectedCategory];
      tab.classList.remove('text-gray-300', 'bg-gray-700', 'hover:bg-blue-600', 'hover:text-white');
      tab.classList.add(styles.bg, styles.text, 'shadow-md', styles.border, 'border', 'active-tab');

      roomsContainer.innerHTML = "";
      const checkinDate = checkIn.value;
      const checkoutDate = checkOut.value;

      if (!checkinDate || !checkoutDate) {
        showErrorModal("Missing Dates", errorMessages['MISSING_DATA']);
        return;
      }

      const checkInParsed = flatpickr.parseDate(checkinDate, 'd F Y');
      const checkOutParsed = checkoutDate ? flatpickr.parseDate(checkoutDate, 'd F Y') : null;
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      if (checkInParsed < today) {
        showErrorModal("Invalid Check-In", errorMessages['INVALID_CHECK_IN']);
        return;
      }

      if (checkOutParsed && checkOutParsed <= checkInParsed) {
        showErrorModal("Invalid Check-Out", errorMessages['INVALID_CHECK_OUT']);
        return;
      }

      if (!availableRooms.length || searchDates.checkIn !== checkinDate || searchDates.checkOut !== checkoutDate) {
        await Promise.all([
          fetchRooms(checkinDate, checkoutDate),
          new Promise(resolve => setTimeout(resolve, 1000))
        ]);
      } else {
        renderRoomsByCategory(selectedCategory);
      }
    });
  });

  // Modal click-outside-to-close
  [bookingModal, confirmationModal, errorModal].forEach(modal => {
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          closeModal(modal.id);
        }
      });
    }
  });

  // Initialize booking modal if query parameters are present
  initializeBookingModalFromQuery();
});