document.addEventListener("DOMContentLoaded", function () {
  const roomsContainer = document.getElementById("rooms-container");
  const modal = document.getElementById("booking-modal");
  const modalOverlay = document.getElementById("modal-overlay");
  const modalClose = document.getElementById("modal-close");
  const bookingForm = document.getElementById("booking-form");
  const bookingSubmitBtn = bookingForm.querySelector("button[type='submit']");
  const bookingSpinner = bookingSubmitBtn.querySelector(".spinner");

  let selectedRoomId = null;
  let bookingPayload = {};

  // Book button opens modal
  roomsContainer.addEventListener("click", (e) => {
    if (e.target.classList.contains("book-btn")) {
      selectedRoomId = e.target.dataset.roomId;
      const roomName = e.target.dataset.roomName;
      document.getElementById("modal-room-name").textContent = roomName;
      modal.classList.remove("hidden");
      modalOverlay.classList.remove("hidden");
    }
  });

  modalClose.addEventListener("click", () => {
    modal.classList.add("hidden");
    modalOverlay.classList.add("hidden");
  });

  bookingForm.addEventListener("submit", async function (e) {
    e.preventDefault();

    bookingSubmitBtn.disabled = true;
    bookingSpinner.classList.remove("hidden");

    const formData = new FormData(bookingForm);
    formData.append("room_id", selectedRoomId);

    bookingPayload = {
      room_id: selectedRoomId,
      guest_name: formData.get("guest_name"),
      guest_email: formData.get("guest_email"),
      guest_phone: formData.get("guest_phone"),
      payment_method: formData.get("payment_method")
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
        modalOverlay.classList.add("hidden");
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
