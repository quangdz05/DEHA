document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("cancelBookingForm");
    var codeTarget = document.getElementById("cancelBookingCode");

    document.querySelectorAll(".js-cancel-booking").forEach(function (button) {
        button.addEventListener("click", function () {
            if (form) form.action = button.dataset.action;
            if (codeTarget) codeTarget.textContent = button.dataset.code || "";
        });
    });
});
