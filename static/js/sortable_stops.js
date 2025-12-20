function reindexStops() {
    const rows = document.querySelectorAll('.stop-row');
    rows.forEach((row, index) => {
        const orderText = row.querySelector('.order-text');
        if (orderText) orderText.innerText = index + 1;

        const orderInput = row.querySelector('input[name*="order"]');
        if (orderInput) {
            orderInput.value = index;
            orderInput.removeAttribute('disabled');
        }
    });
}

const initStopsModule = () => {
    const tableBody = document.getElementById('sortable-stops');
    const addBtn = document.getElementById('add-stop-btn');
    const totalForms = document.querySelector('input[name="stops-TOTAL_FORMS"]');
    const mainForm = document.querySelector('form');

    if (tableBody && typeof Sortable !== 'undefined') {
        new Sortable(tableBody, { handle: '.drag-handle', animation: 150, onEnd: reindexStops });
    }

    if (addBtn) {
        addBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const rows = document.querySelectorAll('.stop-row');
            const currentTotal = parseInt(totalForms.value);
            if (rows.length === 0) return;

            const newRow = rows[0].cloneNode(true);
            newRow.innerHTML = newRow.innerHTML.replace(/stops-\d+-/g, `stops-${currentTotal}-`);

            newRow.querySelectorAll('input, select').forEach(f => {
                if (f.name.includes('-id')) f.value = '';
                else if (f.name.includes('-order')) f.value = currentTotal;
                else f.value = '';
            });

            tableBody.appendChild(newRow);
            totalForms.value = currentTotal + 1;
            reindexStops();
        });
    }

    if (mainForm) {
        mainForm.addEventListener('submit', reindexStops);
    }
};

document.addEventListener('DOMContentLoaded', initStopsModule);
const mainForm = document.querySelector('form');
if (mainForm) {
    mainForm.addEventListener('submit', function() {
        reindexStops(); // Ця функція проставляє 0, 1, 2 в інпути order
    });
}