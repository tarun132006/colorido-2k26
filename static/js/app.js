(() => {

  "use strict";

  const API_BASE = "/api";


  // =========================================================
  // Escape HTML
  // =========================================================

  window.esc = function (value) {

    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");

  };


  // =========================================================
  // API helper
  // =========================================================

  window.api = async function (path, options = {}) {

    const response = await fetch(`${API_BASE}${path}`, {

      ...options,

      headers: {

        Accept: "application/json",

        ...(options.body
          ? { "Content-Type": "application/json" }
          : {}),

        ...(options.headers || {}),

      },

    });


    const contentType =
      response.headers.get("content-type") || "";


    const payload =
      contentType.includes("application/json")
        ? await response.json()
        : await response.text();


    if (!response.ok) {

      let message = "Something went wrong.";


      if (payload && typeof payload === "object") {

        if (Array.isArray(payload.detail)) {

          message = payload.detail
            .map((item) => item?.msg || "Invalid value")
            .join(". ");

        } else if (payload.detail) {

          message = String(payload.detail);

        }

      } else if (payload) {

        message = String(payload);

      }


      throw new Error(message);

    }


    return payload;

  };


  // =========================================================
  // Toast
  // =========================================================

  window.toast = function (message, duration = 3600) {

    document
      .querySelectorAll(".toast")
      .forEach((el) => el.remove());


    const el = document.createElement("div");

    el.className = "toast";

    el.setAttribute("role", "status");

    el.textContent = message;

    document.body.appendChild(el);


    setTimeout(() => el.remove(), duration);

  };


  // =========================================================
  // Navbar + Footer
  // =========================================================

  window.renderChrome = function (active = "") {

    const nav = document.getElementById("nav");

    const footer = document.getElementById("footer");


    // =======================================================
    // NAVIGATION
    // =======================================================

    if (nav) {

      const links = [

        ["Home", "/", "Home"],

        ["About", "/about.html", "About"],

        ["Events", "/events.html", "Events"],

        ["Cultural", "/events.html?division=cultural", "Cultural"],

        ["Sports", "/events.html?division=sports", "Sports"],

        ["Register", "/register.html", "Register"],

        ["Results", "/results.html", "Results"],

        ["Gallery", "/gallery.html", "Gallery"],

        ["Contact", "/contact.html", "Contact"],

        // =================================================
        // ADMIN
        // =================================================

        ["Admin", "/admin.html", "Admin"],

      ];


      nav.innerHTML = `

        <nav class="nav" aria-label="Primary navigation">

          <div class="wrap">


            <!-- =========================================
                 COLLEGE BRAND
                 ========================================= -->

            <a
              class="college-brand"
              href="/"
              aria-label="R.V.R. & J.C. College of Engineering"
            >

              <img
                src="/images/college-logo.png"
                alt="R.V.R. & J.C. College of Engineering logo"
              >

              <div class="college-name">

                <strong>
                  R.V.R. & J.C.
                </strong>

                <strong>
                  College of Engineering, Guntur
                </strong>

              </div>

            </a>


            <!-- =========================================
                 COLORIDO BRAND
                 ========================================= -->

            <a
              class="event-brand"
              href="/"
              aria-label="COLORIDO 2K26"
            >

              <span>
                COLORIDO
              </span>

              <small>
                2K26
              </small>

            </a>


            <!-- =========================================
                 MOBILE MENU
                 ========================================= -->

            <button
              class="menu-btn"
              type="button"
              aria-expanded="false"
              aria-controls="site-menu"
              aria-label="Open menu"
            >
              ☰
            </button>


            <!-- =========================================
                 LINKS
                 ========================================= -->

            <ul id="site-menu">

              ${links

                .map(

                  ([label, href, key]) => `

                    <li>

                      <a
                        class="link ${
                          active === key ? "active" : ""
                        } ${key === "Admin" ? "admin-link" : ""}"
                        href="${href}"
                      >

                        ${label}

                      </a>

                    </li>

                  `

                )

                .join("")}

            </ul>


          </div>

        </nav>

      `;


      // ===================================================
      // MOBILE MENU
      // ===================================================

      const menuButton =
        nav.querySelector(".menu-btn");


      const menu =
        nav.querySelector("#site-menu");


      menuButton?.addEventListener("click", () => {

        const open =
          menu.classList.toggle("open");


        menuButton.setAttribute(
          "aria-expanded",
          String(open)
        );


        menuButton.setAttribute(
          "aria-label",
          open
            ? "Close menu"
            : "Open menu"
        );

      });

    }


    // =======================================================
    // FOOTER
    // =======================================================

    if (footer) {

      footer.innerHTML = `

        <footer>

          <div class="wrap">

            <div class="cols">


              <!-- =========================================
                   COLORIDO
                   ========================================= -->

              <div>

                <h4>
                  COLORIDO 2K26
                </h4>

                <p>
                  National-level cultural and sports festival.
                  Three days of competition, creativity and community.
                </p>

              </div>


              <!-- =========================================
                   EXPLORE
                   ========================================= -->

              <div>

                <h4>
                  Explore
                </h4>

                <a href="/about.html">
                  About COLORIDO
                </a>

                <a href="/events.html">
                  All events
                </a>

                <a href="/results.html">
                  Results
                </a>

                <a href="/gallery.html">
                  Gallery
                </a>

                <a href="/register.html">
                  Register
                </a>

                <a href="/lookup.html">
                  Find registration
                </a>

              </div>


              <!-- =========================================
                   SUPPORT
                   ========================================= -->

              <div>

                <h4>
                  Support
                </h4>

                <a href="/contact.html">
                  Contact
                </a>

                <a href="/">
                  Festival home
                </a>

              </div>


              <!-- =========================================
                   ADMIN
                   ========================================= -->

              <div>

                <h4>
                  Administration
                </h4>

                <a href="/admin.html">
                  Admin Dashboard
                </a>

                <a href="/admin.html">
                  Manage Registrations
                </a>

              </div>


            </div>


            <!-- =========================================
                 FOOTER BOTTOM
                 ========================================= -->

            <div class="footer-bottom">

              © 2026 COLORIDO 2K26 ·
              All event information is subject
              to coordinator updates.

            </div>


          </div>

        </footer>

      `;

    }

  };


  // =========================================================
  // Event card
  // =========================================================

  window.eventCard = function (event) {

    const team =

      event.team_max === 1

        ? "Solo"

        : event.team_min === event.team_max

        ? `${event.team_max} members`

        : `${event.team_min}–${event.team_max} members`;


    const gender =

      event.division === "sports" &&
      event.gender !== "Open"

        ? ` · ${esc(event.gender)}`

        : "";


    return `

      <a
        class="card reveal"
        href="/event.html?slug=${encodeURIComponent(event.slug)}"
      >

        <span class="tag ${esc(event.division)}">

          ${esc(event.category)}

        </span>


        <h3>

          ${esc(event.name)}

        </h3>


        <p>

          ${esc(
            event.description ||
            "Event details and rules available here."
          )}

        </p>


        <div class="info">

          Day ${esc(event.day)}

          ·

          ${esc(event.start_time)}

          ·

          ${esc(event.venue)}

        </div>


        <div class="info">

          ${team}

          ${gender}

          ·

          ${

            event.fee

              ? `₹${esc(event.fee)} entry`

              : "Free entry"

          }

        </div>


      </a>

    `;

  };


  // =========================================================
  // Countdown
  // =========================================================

  window.startCountdown = function (

    id,

    target = "2026-12-10T09:00:00+05:30"

  ) {

    const el =
      document.getElementById(id);


    if (!el) return;


    const targetMs =
      new Date(target).getTime();


    function render() {

      const diff =
        targetMs - Date.now();


      if (diff <= 0) {

        el.innerHTML = `

          <div>

            <b>
              LIVE
            </b>

            <small>
              Festival started
            </small>

          </div>

        `;

        return false;

      }


      const total =
        Math.floor(diff / 1000);


      const days =
        Math.floor(total / 86400);


      const hours =
        Math.floor(
          (total % 86400) / 3600
        );


      const minutes =
        Math.floor(
          (total % 3600) / 60
        );


      const seconds =
        total % 60;


      el.innerHTML = [

        [days, "Days"],

        [hours, "Hours"],

        [minutes, "Minutes"],

        [seconds, "Seconds"],

      ]

        .map(

          ([value, label]) => `

            <div>

              <b>
                ${String(value).padStart(2, "0")}
              </b>

              <small>
                ${label}
              </small>

            </div>

          `

        )

        .join("");


      return true;

    }


    render();


    const timer =
      setInterval(() => {

        if (!render()) {

          clearInterval(timer);

        }

      }, 1000);

  };


  // =========================================================
  // Reveal animation
  // =========================================================

  window.initReveal = function () {

    const items =
      document.querySelectorAll(
        ".reveal:not(.in)"
      );


    if (!items.length) return;


    if (!("IntersectionObserver" in window)) {

      items.forEach((el) =>
        el.classList.add("in")
      );

      return;

    }


    const observer =
      new IntersectionObserver(

        (entries, obs) => {

          entries.forEach((entry) => {

            if (entry.isIntersecting) {

              entry.target.classList.add("in");

              obs.unobserve(
                entry.target
              );

            }

          });

        },

        {
          threshold: 0.08,
        }

      );


    items.forEach((el) =>
      observer.observe(el)
    );

  };


})();