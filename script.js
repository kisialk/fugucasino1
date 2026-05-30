(function () {
  "use strict";

  var header = document.querySelector(".site-header");
  var toggle = document.querySelector(".nav-toggle");
  var panel = document.querySelector(".header-mobile-panel");

  if (!header || !toggle || !panel) {
    return;
  }

  function setOpen(open) {
    header.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function isOpen() {
    return header.classList.contains("is-open");
  }

  toggle.addEventListener("click", function (e) {
    e.stopPropagation();
    setOpen(!isOpen());
  });

  document.addEventListener("click", function (e) {
    if (!isOpen()) {
      return;
    }
    if (!header.contains(e.target)) {
      setOpen(false);
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      setOpen(false);
    }
  });

  panel.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () {
      setOpen(false);
    });
  });
})();
