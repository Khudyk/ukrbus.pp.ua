function reindexStops() {
    document.querySelectorAll('.stop-row').forEach((row, index) => {
        const label = row.querySelector('.order-label');
        if (label) label.innerText = index + 1;
        const input = row.querySelector('input[name*="order"]');
        if (input) input.value = index;
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const tableBody = document.getElementById('sortable-stops');
    const addBtn = document.getElementById('add-stop-btn');
    const totalForms = document.getElementById('id_stops-TOTAL_FORMS');

    if (addBtn && tableBody && totalForms) {
        addBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const rows = document.querySelectorAll('.stop-row');
            if (rows.length === 0) return;

            const currentCount = parseInt(totalForms.value);
            const newRow = rows[0].cloneNode(true);

            // Очищення та оновлення індексів
            newRow.innerHTML = newRow.innerHTML.replace(/stops-\d+-/g, `stops-${currentCount}-`);
            newRow.querySelectorAll('input, select').forEach(input => {
                input.value = '';
                if (input.type === 'checkbox') input.checked = false;
                input.classList.remove('is-invalid'); // Видаляємо помилки
            });

            // Видаляємо ID, щоб не перезаписати існуючий запис
            const idField = newRow.querySelector('input[name*="-id"]');
            if (idField) idField.value = '';

            tableBody.appendChild(newRow);
            totalForms.value = currentCount + 1;
            reindexStops();
        });
    }

    if (tableBody && typeof Sortable !== 'undefined') {
        new Sortable(tableBody, { handle: '.drag-handle', animation: 150, onEnd: reindexStops });
    }
});