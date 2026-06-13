document.addEventListener("DOMContentLoaded", function () {
    // Auto hide Django messages.
    document.querySelectorAll(".alert").forEach(function (alertEl) {
        setTimeout(function () {
            if (window.bootstrap) {
                bootstrap.Alert.getOrCreateInstance(alertEl).close();
            }
        }, 4000);
    });

    // Smooth scroll for anchor links.
    document.querySelectorAll('a[href^="#"]').forEach(function (link) {
        link.addEventListener("click", function (event) {
            var target = document.querySelector(link.getAttribute("href"));
            if (target) {
                event.preventDefault();
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });

    // Preview uploaded avatar.
    document.querySelectorAll('input[type="file"][data-preview]').forEach(function (input) {
        input.addEventListener("change", function () {
            var preview = document.querySelector(input.dataset.preview);
            var file = input.files && input.files[0];
            if (!preview || !file) return;
            preview.src = URL.createObjectURL(file);
            preview.style.display = "block";
        });
    });
});
