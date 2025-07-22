document.addEventListener("DOMContentLoaded", function () {
  console.log("JS is working");

  const categoryTabs = document.querySelectorAll(".category-tab");
  const form = document.getElementById("availability-form");
  const checkIn = document.getElementById("check-in");
  const checkOut = document.getElementById("check-out");
  const roomsContainer = document.getElementById("rooms-container");
  const spinner = document.getElementById("spinner");

  let availableRooms = [];

    // Set today's date as default for check-in and restrict past dates
  const today = new Date().toISOString().split("T")[0];
  checkIn.value = today;
  checkIn.min = today;
  checkOut.min = today;


  // Update min check-out when check-in is selected
  checkIn.addEventListener("change", () => {
    checkOut.min = checkIn.value;
  });

  // Category tab click logic
  categoryTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      categoryTabs.forEach((btn) => {
        btn.classList.remove("bg-blue-100", "text-blue-700", "shadow-sm", "active-tab");
        btn.classList.add("text-gray-700");
      });

      tab.classList.remove("text-gray-700");
      tab.classList.add("bg-blue-100", "text-blue-700", "shadow-sm", "active-tab");

      const selectedCategory = tab.textContent.trim();
      renderRoomsByCategory(selectedCategory);
    });
  });

// Form submit logic
form.addEventListener("submit", async function (e) {
  e.preventDefault();

  const checkinDate = checkIn.value;
  const checkoutDate = checkOut.value;

  if (!checkinDate || !checkoutDate) {
    alert("Please select both check-in and check-out dates.");
    return;
  }

  if (checkoutDate <= checkinDate) {
    alert("Check-out date must be after check-in date.");
    return;
  }

  try {
    spinner.classList.remove("hidden");
    roomsContainer.innerHTML = "";

    const response = await fetch(`/get_available_rooms?checkin=${checkinDate}&checkout=${checkoutDate}`);
    const data = await response.json();
    availableRooms = data.rooms;

    // 🔥 Get the current active category tab
    const activeTab = document.querySelector(".category-tab.active-tab");
    const activeCategory = activeTab ? activeTab.textContent.trim() : null;

    if (activeCategory) {
      renderRoomsByCategory(activeCategory);
    } else {
      // fallback if no tab is selected
      roomsContainer.innerHTML = `<p class="text-gray-500 text-center col-span-full">Please select a room category.</p>`;
    }
  } catch (error) {
    console.error("Error fetching rooms:", error);
    roomsContainer.innerHTML = `<p class="text-red-500 text-center col-span-full">Error loading rooms. Try again later.</p>`;
  } finally {
    spinner.classList.add("hidden");
  }
});


  function renderRoomsByCategory(category) {
    const filtered = availableRooms.filter(room => room.category === category);

    // Clear existing content
    spinner.classList.remove("hidden");
    roomsContainer.innerHTML = "";

    // Simulate delay
    setTimeout(() => {
      spinner.classList.add("hidden");

      if (filtered.length === 0) {
        roomsContainer.innerHTML = `<p class="text-gray-500 text-center col-span-full">No rooms available for ${category}.</p>`;
        return;
      }

      filtered.forEach(room => {
        const card = `
          <div class="bg-white rounded-lg shadow overflow-hidden">
            <img src="${room.image_url}" alt="${room.name}" class="w-full h-48 object-cover">
            <div class="p-4">
              <h3 class="text-xl font-semibold mb-2">${room.name}</h3>
              <p class="text-gray-600 mb-2">${room.description}</p>
              <p class="text-blue-700 font-bold">GHS ${room.price_per_night} / night</p>
              <button class="book-btn mt-3 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
                      data-room-id="${room.id}"
                      data-room-name="${room.name}">
                Book Now
              </button>
            </div>
          </div>`;
        roomsContainer.insertAdjacentHTML("beforeend", card);
      });
    }, 600);
  }
});
