function reindexStops() {
    const rows = document.querySelectorAll('#sortable-stops .stop-row');
    rows.forEach((row, index) => {
        // Оновлюємо текст (1, 2, 3...)
        const displayNum = row.querySelector('.order-text');
        if (displayNum) displayNum.innerText = index + 1;

        // Оновлюємо значення в прихованому інпуті для Django
        const orderInput = row.querySelector('input[name$="-order"]');
        if (orderInput) {
            orderInput.value = index + 1;
        }
    });
}

function initRouteForm() {
    const addBtn = document.getElementById('add-stop-btn');
    const tableBody = document.getElementById('sortable-stops');
    const totalForms = document.getElementById('id_stops-TOTAL_FORMS');
    const template = document.getElementById('empty-form-template');

    if (addBtn && !addBtn.getAttribute('data-listened')) {
        addBtn.setAttribute('data-listened', 'true');
        addBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const currentCount = parseInt(totalForms.value);
            const html = template.innerHTML.replace(/__prefix__/g, currentCount);
            tableBody.insertAdjacentHTML('beforeend', html);
            totalForms.value = currentCount + 1;
            reindexStops();
        });
    }

    if (tableBody && typeof Sortable !== 'undefined') {
        new Sortable(tableBody, { 
            handle: '.drag-handle', 
            animation: 150, 
            onEnd: reindexStops 
        });
    }
}

// Запуск
document.addEventListener('DOMContentLoaded', initRouteForm);