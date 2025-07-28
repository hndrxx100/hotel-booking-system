document.addEventListener("DOMContentLoaded", function () {
  const roomsContainer = document.getElementById("rooms-container");
  const modal = document.getElementById("booking-modal");
  const modalClose = document.getElementById("modal-close");
  const bookingForm = document.getElementById("booking-form");
  const bookingSubmitBtn = bookingForm.querySelector("button[type='submit']");
  const bookingSpinner = bookingSubmitBtn.querySelector(".spinner");
  const roomIdInput = document.getElementById("modal-room-id");

  let selectedRoomId = null;
  let bookingPayload = {};

  // Book button opens modal
  roomsContainer.addEventListener("click", (e) => {
    if (e.target.classList.contains("book-btn")) {
      selectedRoomId = e.target.dataset.roomId;
      const roomName = e.target.dataset.roomName;

      // Set room name and room ID field
      document.getElementById("modal-room-name").textContent = roomName;
      roomIdInput.value = selectedRoomId;

      // Reset form state
      bookingForm.reset();
      bookingSpinner.classList.add("hidden");
      bookingSubmitBtn.disabled = false;

      modal.classList.remove("hidden");
    }
  });

  modalClose.addEventListener("click", () => {
    modal.classList.add("hidden");
  });

  bookingForm.addEventListener("submit", async function (e) {
  e.preventDefault();

  bookingSubmitBtn.disabled = true;
  bookingSpinner.classList.remove("hidden");

  // Get check-in and check-out values from main search inputs
  const checkInValue = document.getElementById("check-in").value;
  const checkOutValue = document.getElementById("check-out").value;

  // Set them into the hidden modal inputs before creating FormData
  document.getElementById("modal-checkin").value = checkInValue;
  document.getElementById("modal-checkout").value = checkOutValue;

  const formData = new FormData(bookingForm);

  bookingPayload = {
    room_id: formData.get("room_id"),
    guest_name: formData.get("guest_name"),
    guest_email: formData.get("guest_email"),
    guest_phone: formData.get("guest_phone"),
    payment_method: formData.get("payment_method"),
    check_in: formData.get("check_in"),
    check_out: formData.get("check_out")
  };

  try {
    const response = await fetch("/submit_booking", {
      method: "POST",
      body: formData
    });

    const result = await response.json();

    if (result.success) {
      showCreateAccountModal(bookingPayload.guest_email);
      modal.classList.add("hidden");
      bookingForm.reset();
    } else {
      alert("Booking failed. Try again.");
    }
  } catch (err) {
    console.error("Booking error:", err);
    alert("Something went wrong.");
  } finally {
    bookingSubmitBtn.disabled = false;
    bookingSpinner.classList.add("hidden");
  }
});


  // Account creation modal
  function showCreateAccountModal(email) {
    document.getElementById("account-email").value = email;
    document.getElementById("account-modal").classList.remove("hidden");
  }

  document.getElementById("close-account-modal").addEventListener("click", () => {
    document.getElementById("account-modal").classList.add("hidden");
  });

  document.getElementById("account-form").addEventListener("submit", async function (e) {
    e.preventDefault();

    const submitBtn = e.target.querySelector("button[type='submit']");
    const spinner = submitBtn.querySelector(".spinner");

    submitBtn.disabled = true;
    spinner.classList.remove("hidden");

    const accountFormData = new FormData(e.target);

    try {
      const response = await fetch("/create_account", {
        method: "POST",
        body: accountFormData
      });

      const result = await response.json();

      if (result.success) {
        alert("Account created! You can now manage your booking.");
        document.getElementById("account-modal").classList.add("hidden");

        // Redirect to payment if selected earlier
        if (bookingPayload.payment_method === "online") {
          const params = new URLSearchParams(bookingPayload);
          window.location.href = `/payment_gateway?${params.toString()}`;
        }
      } else {
        alert(result.message || "Could not create account.");
      }
    } catch (err) {
      console.error("Account creation error:", err);
      alert("Something went wrong.");
    } finally {
      submitBtn.disabled = false;
      spinner.classList.add("hidden");
    }
  });
});
