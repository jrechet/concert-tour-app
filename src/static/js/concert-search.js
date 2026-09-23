/**
 * Live city search for the dashboard concert list.
 *
 * Debounces keystrokes in #city-search-input, calls the JSON
 * GET /api/v1/concerts/?city=... endpoint, and re-renders #calendar-grid
 * client-side from the response. Clearing the input restores the full,
 * unfiltered list.
 *
 * #city-filter-select offers the same filter as a dropdown, populated from
 * GET /api/v1/concerts/cities, for picking a known city outright instead of
 * typing a substring; picking "All cities" clears the filter.
 */
(function () {
  "use strict";

  const CONCERTS_ENDPOINT = "/api/v1/concerts/";
  const CITIES_ENDPOINT = "/api/v1/concerts/cities";
  const DEBOUNCE_MS = 300;
  const MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
  ];

  function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value === null || value === undefined ? "" : String(value);
    return div.innerHTML;
  }

  function formatDate(isoDateTime) {
    const [datePart] = String(isoDateTime).split("T");
    const [year, month, day] = datePart.split("-").map(Number);
    if (!year || !month || !day) return "";
    return `${MONTH_NAMES[month - 1]} ${String(day).padStart(2, "0")}, ${year}`;
  }

  function renderConcertCard(concert) {
    const venueName = escapeHtml(concert.venue_name);
    const venueCity = escapeHtml(concert.venue_city);
    const cancelledBadge = concert.is_cancelled
      ? '<span class="cancellation-badge" role="status">Annulé</span>'
      : "";
    const cancellationReason = concert.is_cancelled && concert.cancellation_reason
      ? `<p class="cancellation-reason">${escapeHtml(concert.cancellation_reason)}</p>`
      : "";

    let ticketMarkup = "";
    if (concert.sold_out) {
      ticketMarkup = '<span class="ticket-badge ticket-badge-sold-out" role="status">Sold Out</span>';
    } else if (concert.remaining_tickets !== null && concert.remaining_tickets !== undefined) {
      ticketMarkup = `<span class="ticket-count">${escapeHtml(concert.remaining_tickets)} tickets left</span>`;
    }

    return `
      <article class="concert-card">
        <div class="concert-card-date">${escapeHtml(formatDate(concert.date_time))}</div>
        <div class="concert-card-venue">
          ${venueName}, ${venueCity}
          ${cancelledBadge}
        </div>
        ${cancellationReason}
        ${ticketMarkup}
      </article>
    `;
  }

  function renderConcerts(container, concerts) {
    if (!concerts.length) {
      container.innerHTML = '<p class="concert-cards-empty">No concerts found.</p>';
      return;
    }
    const cards = concerts.map(renderConcertCard).join("");
    container.innerHTML = `<div class="concert-cards" role="list">${cards}</div>`;
  }

  function debounce(fn, delayMs) {
    let timeoutId;
    return function debounced(...args) {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn.apply(this, args), delayMs);
    };
  }

  async function populateCityFilterSelect(select) {
    try {
      const response = await fetch(CITIES_ENDPOINT);
      if (!response.ok) throw new Error(`Request failed with ${response.status}`);
      const cities = await response.json();
      for (const city of cities) {
        const option = document.createElement("option");
        option.value = city;
        option.textContent = city;
        select.appendChild(option);
      }
    } catch (error) {
      // Leave the "All cities" default option in place; the dropdown is
      // simply not populated if the cities endpoint is unavailable.
    }
  }

  function initCitySearch() {
    const input = document.getElementById("city-search-input");
    const select = document.getElementById("city-filter-select");
    const container = document.getElementById("calendar-grid");
    if (!input || !container) return;

    let requestToken = 0;

    async function runSearch(city) {
      const token = ++requestToken;
      const url = city
        ? `${CONCERTS_ENDPOINT}?city=${encodeURIComponent(city)}`
        : CONCERTS_ENDPOINT;

      try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Request failed with ${response.status}`);
        const concerts = await response.json();
        if (token !== requestToken) return;
        renderConcerts(container, concerts);
      } catch (error) {
        if (token !== requestToken) return;
        container.innerHTML = '<p class="concert-cards-empty">Unable to load concerts right now.</p>';
      }
    }

    input.addEventListener("input", debounce(() => runSearch(input.value.trim()), DEBOUNCE_MS));

    if (select) {
      populateCityFilterSelect(select);
      select.addEventListener("change", () => {
        const city = select.value;
        input.value = city;
        runSearch(city);
      });
    }
  }

  document.addEventListener("DOMContentLoaded", initCitySearch);
})();
