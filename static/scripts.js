// Highlight current selected nav link
document.addEventListener("DOMContentLoaded", function () {
    let links = document.querySelectorAll(".nav-link");
    links.forEach(function(link) {
        if (link.href === window.location.href) {
            link.classList.add("active");
        }
    });
});
