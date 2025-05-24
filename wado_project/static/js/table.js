document.addEventListener('DOMContentLoaded', function () {
    const rows = document.querySelectorAll('.clickable-row');

    rows.forEach(row => {
        row.addEventListener('mouseenter', function () {
            this.style.backgroundColor = '#333';
        });

        row.addEventListener('mouseleave', function () {
            this.style.backgroundColor = '';
        });

        row.addEventListener('click', function () {
            const url = this.getAttribute('data-url');
            if (url) window.location.href = url;
        });
    });
});