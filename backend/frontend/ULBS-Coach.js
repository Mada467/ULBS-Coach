const API_URL = 'http://localhost:5000';
let notaSelectata = '7-8';

document.addEventListener('DOMContentLoaded', () => {
    initNotaButtons();
    initTextarea();
    loadStatistici();
});

function initNotaButtons() {
    document.querySelectorAll('.nota-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.nota-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            notaSelectata = btn.dataset.nota;
        });
    });
}

function initTextarea() {
    const textarea = document.getElementById('intrebare-input');
    const charCount = document.getElementById('char-count');
    textarea.addEventListener('input', () => {
        const len = textarea.value.length;
        charCount.textContent = `${len} / 500`;
        if (len > 450) charCount.style.color = '#e94560';
        else charCount.style.color = '';
    });

    textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) intreaba();
    });
}

function setIntrebare(text) {
    document.getElementById('intrebare-input').value = text;
    document.getElementById('char-count').textContent = `${text.length} / 500`;
    document.getElementById('intrebare-input').focus();
}

async function intreaba() {
    const intrebare = document.getElementById('intrebare-input').value.trim();
    if (!intrebare) {
        showToast('Scrie o intrebare mai intai!', 'error');
        return;
    }
    if (intrebare.length > 500) {
        showToast('Intrebarea este prea lunga!', 'error');
        return;
    }

    setLoading(true);

    try {
        const response = await fetch(`${API_URL}/api/intreaba`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ intrebare, nivel_nota: notaSelectata })
        });

        const data = await response.json();

       if (data.raspuns) {
            showRaspuns(data.raspuns, intrebare);
            loadStatistici();
            showToast('Raspuns generat cu succes!', 'success');
        } else if (data.error === 'intrebare_nepermisa') {
            showToast('Intrebare nepermisa!', 'error');
            showMesajEtica(data.motiv);
        } else {
            showToast('Eroare la generarea raspunsului!', 'error');
        }
    } catch (err) {
        showToast('Serverul nu raspunde. Verifica daca backend-ul ruleaza!', 'error');
    }

    setLoading(false);
}

function showRaspuns(raspuns, intrebare) {
    const card = document.getElementById('raspuns-card');
    const text = document.getElementById('raspuns-text');
    const badge = document.getElementById('raspuns-nivel-badge');

    text.innerHTML = raspuns
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
    badge.textContent = `Nota ${notaSelectata}`;
    card.style.display = 'block';

    card.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
function showMesajEtica(motiv) {
    const card = document.getElementById('raspuns-card');
    const text = document.getElementById('raspuns-text');
    const badge = document.getElementById('raspuns-nivel-badge');

    badge.textContent = 'Intrebare nepermisa';
    badge.style.background = 'rgba(233,69,96,0.15)';
    badge.style.color = '#e94560';
    badge.style.border = '1px solid rgba(233,69,96,0.3)';

    text.innerHTML = `
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 2rem; margin-bottom: 1rem;">⚠️</div>
            <h3 style="color: var(--highlight); margin-bottom: 0.5rem;">Intrebare nepermisa!</h3>
            <p style="color: var(--text-muted); font-size: 14px;">${motiv}</p>
            <p style="color: var(--text-muted); font-size: 13px; margin-top: 1rem;">
                Te rugam sa pui intrebari legate de <strong style="color: var(--text)">Programare Orientata pe Obiecte</strong>.
            </p>
        </div>
    `;

    card.style.display = 'block';
    card.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function newIntrebare() {
    document.getElementById('raspuns-card').style.display = 'none';
    document.getElementById('intrebare-input').value = '';
    document.getElementById('char-count').textContent = '0 / 500';
    document.getElementById('intrebare-input').focus();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function copyRaspuns() {
    const text = document.getElementById('raspuns-text').textContent;
    navigator.clipboard.writeText(text).then(() => {
        showToast('Raspuns copiat!', 'success');
    });
}

async function loadStatistici() {
    try {
        const response = await fetch(`${API_URL}/api/statistici`);
        const data = await response.json();

        document.getElementById('total-intrebari').textContent = data.length;

        const azi = data.filter(item => {
            const itemDate = new Date(item.data).toDateString();
            return itemDate === new Date().toDateString();
        });
        document.getElementById('azi-intrebari').textContent = azi.length;

        if (data.length > 0) {
            const noteCounts = {};
            data.forEach(item => {
                noteCounts[item.nota] = (noteCounts[item.nota] || 0) + 1;
            });
            const notaPref = Object.keys(noteCounts).reduce((a, b) =>
                noteCounts[a] > noteCounts[b] ? a : b
            );
            document.getElementById('nota-preferata').textContent = notaPref;
        }

        const lista = document.getElementById('istoricul');
        if (data.length === 0) {
            lista.innerHTML = '<p style="color: var(--text-muted); font-size: 13px; text-align: center; padding: 1rem;">Nu ai intrebari inca. Incepe sa inveti!</p>';
            return;
        }

        lista.innerHTML = data.map(item => `
            <div class="istoric-item">
                <span class="istoric-intrebare">${item.intrebare}</span>
                <span class="istoric-nota">Nota ${item.nota}</span>
                <span class="istoric-data">${formatData(item.data)}</span>
            </div>
        `).join('');

    } catch (err) {
        console.error('Eroare la statistici:', err);
    }
}

function formatData(dataStr) {
    const d = new Date(dataStr);
    return d.toLocaleDateString('ro-RO', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function setLoading(active) {
    const btn = document.getElementById('intreaba-btn');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');

    btn.disabled = active;
    btnText.style.display = active ? 'none' : 'inline';
    btnSpinner.style.display = active ? 'inline' : 'none';
}

function showToast(message, type = 'success') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: ${type === 'success' ? 'rgba(0,212,170,0.15)' : 'rgba(233,69,96,0.15)'};
        border: 1px solid ${type === 'success' ? 'rgba(0,212,170,0.3)' : 'rgba(233,69,96,0.3)'};
        color: ${type === 'success' ? '#00d4aa' : '#e94560'};
        padding: 12px 20px;
        border-radius: 10px;
        font-size: 14px;
        z-index: 1000;
        animation: fadeIn 0.3s ease;
        backdrop-filter: blur(10px);
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

async function genereazaCartonase() {
    const topic = document.getElementById('topic-input').value.trim();
    const numar = document.getElementById('numar-cartonase').value;

    if (!topic) {
        showToast('Scrie un topic mai intai!', 'error');
        return;
    }

    const btn = document.getElementById('genereaza-btn');
    btn.disabled = true;
    btn.textContent = 'Se genereaza...';

    try {
        const response = await fetch(`${API_URL}/api/cartonase`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, numar: parseInt(numar) })
        });

        const data = await response.json();

        if (data.cartonase) {
            afiseazaCartonase(data.cartonase);
            showToast(`${data.cartonase.length} cartonase generate!`, 'success');
        } else {
            showToast('Eroare la generare!', 'error');
        }
    } catch (err) {
        showToast('Serverul nu raspunde!', 'error');
    }

    btn.disabled = false;
    btn.textContent = 'Genereaza';
}

function afiseazaCartonase(cartonase) {
    const container = document.getElementById('cartonase-container');

    window.cartonaseData = cartonase;

    container.innerHTML = cartonase.map((c, i) => `
        <div class="cartonas" id="cartonas-${i}" onclick="openModal(${i})">
            <div class="cartonas-front">
                <span class="cartonas-intrebare">${i+1}. ${c.intrebare}</span>
                <span class="cartonas-dificultate dificultate-${c.dificultate}">${c.dificultate}</span>
                <span class="cartonas-arrow">▶</span>
            </div>
        </div>
    `).join('');

    document.getElementById('cartonase-card').scrollIntoView({ behavior: 'smooth' });
}

function openModal(index) {
    const c = window.cartonaseData[index];

    document.getElementById('modal-intrebare').textContent = c.intrebare;

    const badge = document.getElementById('modal-dificultate-badge');
    badge.textContent = c.dificultate;
    badge.className = `cartonas-dificultate dificultate-${c.dificultate}`;

    const body = document.getElementById('modal-body');
    let raspuns = c.raspuns
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/```(\w+)?\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');

    body.innerHTML = '<p>' + raspuns + '</p>';

    document.getElementById('modal-overlay').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
    document.body.style.overflow = '';
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
});
let quizData = {
    intrebari: [],
    indexCurent: 0,
    scorTotal: 0,
    numarIntrebari: 0
};

async function startQuiz() {
    const topic = document.getElementById('quiz-topic-input').value.trim();
    const numar = parseInt(document.getElementById('quiz-numar').value);

    if (!topic) {
        showToast('Scrie un topic mai intai!', 'error');
        return;
    }

    const btn = document.getElementById('start-quiz-btn');
    btn.disabled = true;
    btn.textContent = 'Se genereaza...';

    try {
        const response = await fetch(`${API_URL}/api/cartonase`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, numar })
        });

        const data = await response.json();

        if (data.cartonase) {
            quizData.intrebari = data.cartonase;
            quizData.indexCurent = 0;
            quizData.scorTotal = 0;
            quizData.numarIntrebari = data.cartonase.length;

            document.getElementById('quiz-start').style.display = 'none';
            document.getElementById('quiz-container').style.display = 'block';
            document.getElementById('quiz-feedback').style.display = 'none';
            document.getElementById('quiz-rezultat-final').style.display = 'none';

            afiseazaIntrebare();
            showToast('Quiz generat! Succes!', 'success');
        } else {
            showToast('Eroare la generare!', 'error');
        }
    } catch (err) {
        showToast('Serverul nu raspunde!', 'error');
    }

    btn.disabled = false;
    btn.textContent = 'Incepe Quiz';
}

function afiseazaIntrebare() {
    const idx = quizData.indexCurent;
    const total = quizData.numarIntrebari;
    const intrebare = quizData.intrebari[idx];

    document.getElementById('quiz-progress-text').textContent = `Intrebarea ${idx + 1} din ${total}`;
    document.getElementById('quiz-progress-fill').style.width = `${((idx) / total) * 100}%`;
    document.getElementById('quiz-intrebare').textContent = intrebare.intrebare;
    document.getElementById('quiz-raspuns-input').value = '';
    document.getElementById('quiz-char-count').textContent = '0 / 1000';

    document.getElementById('quiz-container').style.display = 'block';
    document.getElementById('quiz-feedback').style.display = 'none';
}

async function submitRaspuns() {
    const raspunsStudent = document.getElementById('quiz-raspuns-input').value.trim();

    if (!raspunsStudent) {
        showToast('Scrie un raspuns mai intai!', 'error');
        return;
    }

    const btn = document.getElementById('quiz-submit-btn');
    btn.disabled = true;
    btn.textContent = 'Se evalueaza...';

    const intrebareCurenta = quizData.intrebari[quizData.indexCurent];

    try {
        const response = await fetch(`${API_URL}/api/quiz/evalueaza`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                intrebare: intrebareCurenta.intrebare,
                raspuns_student: raspunsStudent,
                raspuns_corect: intrebareCurenta.raspuns
            })
        });

        const data = await response.json();

        if (data.nota !== undefined) {
            quizData.scorTotal += data.nota;
            afiseazaFeedback(data, intrebareCurenta.raspuns);
        } else {
            showToast('Eroare la evaluare!', 'error');
        }
    } catch (err) {
        showToast('Serverul nu raspunde!', 'error');
    }

    btn.disabled = false;
    btn.textContent = 'Trimite Raspuns';
}

function afiseazaFeedback(rezultat, raspunsCorect) {
    const esteCorect = rezultat.nota >= 6;
    const clasa = esteCorect ? 'feedback-corect' : 'feedback-gresit';

    document.getElementById('quiz-feedback-content').innerHTML = `
        <div class="${clasa}" style="padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
            <div class="feedback-nota">${rezultat.nota}/10</div>
            <p><strong>Feedback:</strong> ${rezultat.feedback}</p>
        </div>
        <div style="background: rgba(0,212,170,0.05); border: 1px solid rgba(0,212,170,0.2); border-radius: 10px; padding: 1rem;">
            <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 0.5rem;">RASPUNS CORECT:</p>
            <p style="font-size: 14px; color: var(--text);">${raspunsCorect}</p>
        </div>
    `;

    const esteUltima = quizData.indexCurent === quizData.numarIntrebari - 1;
    const nextBtn = document.getElementById('quiz-next-btn');
    nextBtn.textContent = esteUltima ? 'Vezi Rezultatul Final' : 'Urmatoarea Intrebare';

    document.getElementById('quiz-container').style.display = 'none';
    document.getElementById('quiz-feedback').style.display = 'block';
}

function nextIntrebare() {
    quizData.indexCurent++;

    if (quizData.indexCurent >= quizData.numarIntrebari) {
        afiseazaRezultatFinal();
    } else {
        afiseazaIntrebare();
        document.getElementById('quiz-feedback').style.display = 'none';
        document.getElementById('quiz-container').style.display = 'block';
    }
}

function afiseazaRezultatFinal() {
    const scorMediu = Math.round(quizData.scorTotal / quizData.numarIntrebari);
    let mesaj = '';

    if (scorMediu >= 9) mesaj = 'Exceptional! Esti pregatit pentru examen!';
    else if (scorMediu >= 7) mesaj = 'Foarte bine! Mai studiaza putin si esti gata!';
    else if (scorMediu >= 5) mesaj = 'Bine! Continua sa studiezi!';
    else mesaj = 'Mai ai de invatat. Nu te descuraja!';

    document.getElementById('quiz-scor-mare').textContent = `${scorMediu}/10`;
    document.getElementById('quiz-mesaj-final').textContent = mesaj;

    document.getElementById('quiz-feedback').style.display = 'none';
    document.getElementById('quiz-container').style.display = 'none';
    document.getElementById('quiz-rezultat-final').style.display = 'flex';

    document.getElementById('quiz-progress-fill').style.width = '100%';
}

function resetQuiz() {
    quizData = { intrebari: [], indexCurent: 0, scorTotal: 0, numarIntrebari: 0 };
    document.getElementById('quiz-start').style.display = 'block';
    document.getElementById('quiz-container').style.display = 'none';
    document.getElementById('quiz-feedback').style.display = 'none';
    document.getElementById('quiz-rezultat-final').style.display = 'none';
    document.getElementById('quiz-topic-input').value = '';
    document.getElementById('quiz-progress-fill').style.width = '0%';
}

document.getElementById('quiz-raspuns-input') && document.getElementById('quiz-raspuns-input').addEventListener('input', () => {
    const len = document.getElementById('quiz-raspuns-input').value.length;
    document.getElementById('quiz-char-count').textContent = `${len} / 1000`;
});