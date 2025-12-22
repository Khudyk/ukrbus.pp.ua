// Функція для перерахунку порядкових номерів
function reindexStops() {
    const rows = document.querySelectorAll('#sortable-stops .stop-row');
    rows.forEach((row, index) => {
        // 1. Оновлюємо візуальний текст (для користувача)
        const displayNum = row.querySelector('.order-text');
        if (displayNum) displayNum.innerText = index + 1;

        // 2. Оновлюємо ПРИХОВАНЕ ПОЛЕ для Django (для сервера)
        // Django генерує name на кшталт "stops-2-order".
        // Ми шукаємо будь-який input, ім'я якого закінчується на "-order"
        const orderInput = row.querySelector('input[name$="-order"]');

        if (orderInput) {
            orderInput.value = index + 1;
            console.log(`Призначено order=${index + 1} для поля ${orderInput.name}`); // Для відладки в консолі
        }
    });
}

// Функція ініціалізації
function initRouteForm() {
    const addBtn = document.getElementById('add-stop-btn');
    const tableBody = document.getElementById('sortable-stops');
    const totalForms = document.getElementById('id_stops-TOTAL_FORMS');
    const template = document.getElementById('empty-form-template');

    // Захист від подвійного натискання та повторної ініціалізації
    if (addBtn && !addBtn.getAttribute('data-listened')) {
        addBtn.setAttribute('data-listened', 'true');
        
        addBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation(); // Зупиняємо розповсюдження події

            const currentCount = parseInt(totalForms.value);
            const html = template.innerHTML.replace(/__prefix__/g, currentCount);
            
            tableBody.insertAdjacentHTML('beforeend', html);
            totalForms.value = currentCount + 1;
            
            reindexStops();
        });
    }

    // Ініціалізація перетягування (SortableJS)
    if (tableBody && typeof Sortable !== 'undefined') {
        new Sortable(tableBody, { 
            handle: '.drag-handle', 
            animation: 150, 
            onEnd: reindexStops 
        });
    }
}

// Запуск при завантаженні
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRouteForm);
} else {
    initRouteForm();
}