(function () {
  "use strict";

  var READING_PASSWORD = "111111";
  var form = document.querySelector("[data-reading-mask]");

  if (!form) {
    return;
  }

  var input = form.querySelector("input[type='password']");
  var error = form.querySelector(".reading-mask-error");
  var protectedSections = document.querySelectorAll("[data-protected-content]");

  form.addEventListener("submit", function (event) {
    event.preventDefault();

    if (input.value !== READING_PASSWORD) {
      error.hidden = false;
      input.setAttribute("aria-invalid", "true");
      input.select();
      return;
    }

    protectedSections.forEach(function (section) {
      section.hidden = false;
    });
    form.hidden = true;
  });

  input.addEventListener("input", function () {
    if (!error.hidden) {
      error.hidden = true;
      input.removeAttribute("aria-invalid");
    }
  });
}());
