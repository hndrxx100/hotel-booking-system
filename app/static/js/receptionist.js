let bookings = [];

async function fetchBookings() {
  try {
    const res = await fetch('/receptionist/bookings');
    const data = await res.json();
    bookings = data.bookings.map(b => ({
      ...b,
      type: getBookingType(b.check_in_date, b.check_out_date)
    }));
    const activeTab = document.querySelector('.tab-btn.active-tab')?.getAttribute('data-tab') || 'today';
    loadBookingsByTab(activeTab);
  } catch (error) {
    console.error('Failed to fetch bookings:', error);
  }
}

function getBookingType(checkInDateStr, checkOutDateStr) {
  const today = new Date().toISOString().split('T')[0];
  if (checkInDateStr > today) return 'upcoming';
  if (checkOutDateStr < today) return 'past';
  return 'today';
}

function renderBookingCard(booking) {
  let actionButton = '';
  if (booking.status === 'Pending') {
    actionButton = `<button onclick="updateStatus(${booking.id}, 'Checked-in')" class="bg-green-600 text-white text-sm px-4 py-2 rounded hover:bg-green-700 min-w-[100px]">Check In</button>`;
  } else if (booking.status === 'Checked-in') {
    actionButton = `<button onclick="updateStatus(${booking.id}, 'Checked-out')" class="bg-red-600 text-white text-sm px-4 py-2 rounded hover:bg-red-700 min-w-[100px]">Check Out</button>`;
  }

  const statusBadgeColor =
    booking.status === 'Pending' ? 'bg-yellow-100 text-yellow-800' :
    booking.status === 'Checked-in' ? 'bg-green-100 text-green-800' :
    booking.status === 'Checked-out' ? 'bg-blue-100 text-blue-800' :
    'bg-gray-100 text-gray-700';

  const paymentStatus = booking.is_paid ? 'Paid' : 'Unpaid';
  const paymentStatusColor = booking.is_paid ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800';
  const methodColor = 'bg-blue-100 text-blue-800';

  return `
    <div class="bg-white shadow rounded-lg p-4 flex items-center justify-between mb-3">
      <div>
        <h3 class="text-lg font-semibold text-blue-800 cursor-pointer hover:underline" onclick="viewGuestProfile('${booking.guest_id}')">
          ${booking.guest_name}
        </h3>
        <p class="text-sm text-gray-600">Room ${booking.room_number} • Check-in: ${booking.check_in_date}</p>

        <div class="flex gap-2 mt-2">
          <span class="text-xs px-2 py-1 rounded-full min-w-[90px] text-center inline-block ${statusBadgeColor}">${booking.status}</span>
          <span class="text-xs px-2 py-1 rounded-full min-w-[80px] text-center inline-block ${paymentStatusColor}">${paymentStatus}</span>
          <span class="text-xs px-2 py-1 rounded-full min-w-[80px] text-center inline-block ${methodColor}">${booking.payment_method || 'N/A'}</span>
        </div>
      </div>

      <div class="flex items-center gap-4">
        ${actionButton}
        <button class="bg-blue-50 text-blue-700 text-sm px-3 py-1 rounded hover:underline">View</button>
      </div>
    </div>
  `;
}

function loadBookingsByTab(tabType) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active-tab', 'border-blue-500', 'text-blue-700'));
  document.querySelector(`.tab-btn[data-tab="${tabType}"]`).classList.add('active-tab', 'border-b-2', 'border-blue-500', 'text-blue-700');

  const filtered = applyFilters(bookings, tabType);
  const container = document.getElementById('bookingCardsContainer');
  container.innerHTML = filtered.length > 0
    ? filtered.map(renderBookingCard).join('')
    : `<div class="col-span-full text-center text-gray-500">No bookings found</div>`;
}

function applyFilters(bookings, tabType) {
  const search = document.getElementById('searchInput')?.value.toLowerCase() || '';
  const statusFilter = document.getElementById('statusFilter')?.value || '';
  const selectedDate = document.getElementById('filterDate')?.value || '';
  const matchesDate = !selectedDate || b.check_in_date === selectedDate;

  return bookings.filter(b => {
    const matchesTab = b.type === tabType;
    const matchesSearch = b.guest_name.toLowerCase().includes(search);
    const matchesStatus = !statusFilter || b.status === statusFilter;
    return matchesTab && matchesSearch && matchesStatus;
  });
}

async function updateStatus(bookingId, newStatus) {
  try {
    const formData = new FormData();
    formData.append('booking_id', bookingId);
    formData.append('status', newStatus);

    const res = await fetch('/receptionist/booking/update_status', {
      method: 'POST',
      body: formData
    });

    const result = await res.json();
    if (result.success) {
      await fetchBookings(); // Refresh
    } else {
      alert(result.message || 'Failed to update');
    }
  } catch (err) {
    console.error('Update error:', err);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  fetchBookings();

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.getAttribute('data-tab');
      loadBookingsByTab(tab);
    });
  });

  ['searchInput', 'statusFilter'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', () => {
      const activeTab = document.querySelector('.tab-btn.active-tab')?.getAttribute('data-tab') || 'today';
      loadBookingsByTab(activeTab);
    });
  });
});

function openAddRoomModal() {
  document.getElementById('addRoomModal').classList.remove('hidden');
  document.getElementById('addRoomModal').classList.add('flex');
}

function closeAddRoomModal() {
  document.getElementById('addRoomModal').classList.add('hidden');
  document.getElementById('addRoomModal').classList.remove('flex');
}

document.getElementById('addRoomForm')?.addEventListener('submit', async function (e) {
  e.preventDefault();

  const form = e.target;
  const formData = new FormData(form);

  try {
    const response = await fetch('/receptionist/room/add', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    if (data.success) {
      alert('Room added successfully');
      form.reset();
      closeAddRoomModal();
      // Optional: refresh room list if you're showing it
    } else {
      alert(data.message || 'Something went wrong');
    }
  } catch (err) {
    alert('Error: ' + err.message);
  }
});

