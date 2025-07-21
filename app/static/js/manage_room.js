document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("add-room-form");
  const roomList = document.getElementById("room-list");

  fetchRooms(); // Load existing rooms on page load

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(form);

    try {
      const res = await fetch("/add_room", {
        method: "POST",
        body: formData
      });

      const result = await res.json();

      if (result.success) {
        alert("Room added successfully");
        form.reset();
        fetchRooms(); // Reload rooms
      } else {
        alert(result.message || "Could not add room.");
      }
    } catch (err) {
      console.error("Room add error:", err);
      alert("Server error. Try again.");
    }
  });

  async function fetchRooms() {
    roomList.innerHTML = "";

    try {
      const res = await fetch("/get_all_rooms");
      const data = await res.json();

      data.rooms.forEach(room => {
        const card = `
          <div class="bg-white rounded-lg shadow p-4">
            <h3 class="text-xl font-semibold text-blue-700 mb-2">${room.room_type} Room ${room.room_number}</h3>
            <p class="text-gray-600 mb-2">${room.description || 'No description'}</p>
            <p class="text-blue-600 font-bold">GHS ${room.price} / night</p>
          </div>`;
        roomList.insertAdjacentHTML("beforeend", card);
      });
    } catch (err) {
      console.error("Fetch rooms error:", err);
      roomList.innerHTML = `<p class="text-red-500">Error loading rooms.</p>`;
    }
  }
});
