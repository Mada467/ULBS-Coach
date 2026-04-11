const API_URL = 'http://127.0.0.1:5000';
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