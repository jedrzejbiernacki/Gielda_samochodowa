document.addEventListener('DOMContentLoaded', function () {
    // 1. Kaskadowe wybieranie modeli dla wybranej marki
    const markaSelect = document.getElementById('id_marka');
    const modelSelect = document.getElementById('id_model_pojazdu');

    if (markaSelect && modelSelect) {
        markaSelect.addEventListener('change', function () {
            const markaId = this.value;
            modelSelect.innerHTML = '<option value="">Ładowanie modeli...</option>';

            if (!markaId) {
                modelSelect.innerHTML = '<option value="">Wszystkie modele</option>';
                return;
            }

            fetch(`/api/modele/?marka_id=${encodeURIComponent(markaId)}`)
                .then(response => response.json())
                .then(data => {
                    modelSelect.innerHTML = '<option value="">Wszystkie modele</option>';
                    if (data.modele && data.modele.length > 0) {
                        data.modele.forEach(model => {
                            const option = document.createElement('option');
                            option.value = model.id;
                            option.textContent = model.nazwa;
                            modelSelect.appendChild(option);
                        });
                    }
                })
                .catch(err => {
                    console.error('Błąd pobierania modeli:', err);
                    modelSelect.innerHTML = '<option value="">Błąd wczytywania</option>';
                });
        });
    }

    // 2. Galeria miniatur na stronie ogłoszenia
    const mainImg = document.getElementById('glowne-zdjecie-podglad');
    const thumbs = document.querySelectorAll('.gallery-thumb');

    thumbs.forEach(thumb => {
        thumb.addEventListener('click', function () {
            if (mainImg) {
                mainImg.src = this.getAttribute('data-full');
            }
            thumbs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });
});
