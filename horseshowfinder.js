document.addEventListener("DOMContentLoaded", () => {
  const icons = {
    jumping: new L.Icon({
      iconUrl:
        "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",
      shadowUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41],
    }),
    eventing: new L.Icon({
      iconUrl:
        "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
      shadowUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41],
    }),
    dressage: new L.Icon({
      iconUrl:
        "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-violet.png",
      shadowUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41],
    }),
    other: new L.Icon({
      iconUrl:
        "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png",
      shadowUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41],
    }),
  };

  const isMobile = window.innerWidth <= 500;

  const map = L.map("map", {
    center: [50.0, -90.0],
    zoom: isMobile ? 3 : 4, // must be integer here
    zoomSnap: 0.1,
    maxZoom: 11,
  });

  // Apply fractional zoom after initialization
  if (isMobile) {
    map.setZoom(3.5);
  } else {
    map.setZoom(4.6); // Or whatever default you prefer for desktop
  }

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);

  let allMarkers = [];

  fetch("heatmap.json")
    .then((response) => response.json())
    .then((data) => {
      const markerGroup = L.markerClusterGroup({
        zoomToBoundsOnClick: false,
      });

      markerGroup.on("clusterclick", (a) => {
        map.fitBounds(a.layer.getBounds(), {
          padding: [0, 70],
          maxZoom: 13,
          animate: true,
        });
      });

      data.forEach((item) => {
        const discipline = item.discipline.toLowerCase();
        const icon = icons[discipline] || icons.other;

        const marker = L.marker([item.lat, item.lng], { icon: icon });

        const disciplineFormatted =
          item.discipline.charAt(0).toUpperCase() + item.discipline.slice(1);

        let dateDisplay = "";
        if (item.cancelled === "True") {
          dateDisplay = `
              <div style="color: red; font-weight: bold;">Cancelled</div>
              <div style="color: dimgray; text-decoration: line-through;">
                ${item.start_date} to ${item.end_date}
              </div>`;
        } else {
          dateDisplay = `${item.start_date} to ${item.end_date}`;
        }

        let resultsClass = "";
        let resultsDisplay = "";
        const resultsURL = `https://events.equestrian.ca/eventDetails?id=${item.show_id}`;

        if (item.results === "True") {
          resultsClass = "green";
          resultsDisplay = `<a href="${resultsURL}" target="_blank" noopener noreferrer>Results</a>`;
        } else if (item.pending_results === "True") {
          resultsClass = "amber";
          resultsDisplay = "Pending Results";
        } else {
          resultsClass = "none";
          resultsDisplay = "No Results";
        }

        let websiteLink = "";
        if (item.website && item.website.trim() !== "") {
          let websiteURL = item.website.trim();
          if (!/^https?:\/\//i.test(websiteURL)) {
            websiteURL = `https://${websiteURL}`;
          }
          websiteLink = `
              <div style="margin: .5rem 0 0 0;" id="website">
                <a href="${websiteURL}" target="_blank" rel="noopener noreferrer">Competition Website</a>
              </div>`;
        }

        marker.bindPopup(`
            <h3>${item.name || ""}</h3>
            <b>${item.venue}</b><br>
            ${item.city_province}<br>
            ${dateDisplay}<br>
            <div style="margin: .5rem 0 0 0; font-style: italic;">
              ${disciplineFormatted}</div>
            Level: ${item.level}<br>
            <div style="margin: .5rem 0 0 0;" class="${resultsClass}">
              Results: ${resultsDisplay}
            </div>
            ${websiteLink}
          `);

        marker.discipline = discipline;
        markerGroup.addLayer(marker);
        allMarkers.push(marker);
      });

      map.addLayer(markerGroup);

      // Fix map layout after markers are added
      setTimeout(() => {
        map.invalidateSize();
      }, 100);

      // Filtering logic
      const checkboxes = document.querySelectorAll(".discipline-checkbox");

      function filterMarkers() {
        const selectedDisciplines = Array.from(checkboxes)
          .filter((cb) => cb.checked)
          .map((cb) => cb.value);

        markerGroup.clearLayers();

        const filtered =
          selectedDisciplines.length === 0
            ? []
            : allMarkers.filter((m) =>
                selectedDisciplines.includes(m.discipline)
              );

        filtered.forEach((m) => markerGroup.addLayer(m));
      }

      checkboxes.forEach((cb) => {
        cb.addEventListener("change", filterMarkers);
      });
    })
    .catch((error) => {
      console.error("Failed to load heatmap.json:", error);
      alert("Could not load map data.");
    });
});
