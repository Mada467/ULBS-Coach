/* ==========================================
   ULBS Coach v2.0 — Frontend JavaScript
   ========================================== */

const API_URL = 'http://localhost:5000';

// ===== STATE GLOBAL =====
let state = {
  materie: 'POO',
  nota: '7-8',
  cartonaseData: [],
  currentCartonasIndex: 0,
  raspunsActual: null,
  quiz: {
    intrebari: [],
    indexCurent: 0,
    scorTotal: 0,
    numar: 0,
    materie: 'POO',
    topic: '',
    tip: 'teorie',
    startTime: null,
    raspunsuri: [],
    timerInterval: null,
    timpRamas: 120
  }
};

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
  initNotaPills();
  initTextareas();
  initUploadDragDrop();
  loadStatistici();
  loadQuizIstoric();
  loadStreak();
  selectMaterie('POO');
});

// ===== TEMA =====
function toggleTheme() {
  document.body.classList.toggle('dark');
  const isDark = document.body.classList.contains('dark');
  document.getElementById('theme-icon').textContent = isDark ? '☀️' : '🌙';
  localStorage.setItem('ulbs-theme', isDark ? 'dark' : 'light');
}

(function initTheme() {
  if (localStorage.getItem('ulbs-theme') === 'dark') {
    document.body.classList.add('dark');
    const icon = document.getElementById('theme-icon');
    if (icon) icon.textContent = '☀️';
  }
})();

// ===== TABS =====
function switchTab(tabName) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

  const content = document.getElementById(`tab-${tabName}`);
  const btn = document.querySelector(`[data-tab="${tabName}"]`);

  if (content) content.classList.add('active');
  if (btn) btn.classList.add('active');

  if (tabName === 'statistici') {
    loadStatistici();
    loadQuizIstoricFull();
  }
  if (tabName === 'salvate') loadSalvate();
  if (tabName === 'upload') loadCarti();
}

// ===== SELECTIE MATERIE =====
function selectMaterie(materie) {
  state.materie = materie;

  // Update carduri
  document.querySelectorAll('.materie-card').forEach(c => c.classList.remove('active'));
  const card = document.querySelector(`.materie-card[data-materie="${materie}"]`);
  if (card) card.classList.add('active');

  // Update checkmarks
  document.querySelectorAll('.materie-check').forEach(c => c.style.display = 'none');
  const check = document.getElementById(`check-${materie}`);
  if (check) check.style.display = 'flex';

  // Update bara
  const info = {
    POO: { icon: '💻', nume: 'Programare Orientata pe Obiecte' },
    SO:  { icon: '🖥️', nume: 'Sisteme de Operare' }
  };
  const m = info[materie] || { icon: '📚', nume: materie };
  document.getElementById('materie-bar-icon').textContent = m.icon;
  document.getElementById('materie-bar-nume').textContent = m.nume;

  // Quick buttons
  document.getElementById('quick-POO').style.display = materie === 'POO' ? 'flex' : 'none';
  document.getElementById('quick-SO').style.display  = materie === 'SO'  ? 'flex' : 'none';

  // Placeholder textarea
  const placeholders = {
    POO: 'Scrie intrebarea ta despre POO... Ex: Ce este mostenirea?',
    SO:  'Scrie intrebarea ta despre SO... Ex: Ce este un deadlock?'
  };
  const ta = document.getElementById('intrebare-input');
  if (ta) ta.placeholder = placeholders[materie] || 'Scrie intrebarea ta...';

  // Ascunde raspuns anterior
  const rc = document.getElementById('raspuns-card');
  if (rc) rc.style.display = 'none';
}

// ===== NOTA PILLS =====
function initNotaPills() {
  document.querySelectorAll('.nota-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nota-pill').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      state.nota = btn.dataset.nota;
    });
  });
}

// ===== TEXTAREAS =====
function initTextareas() {
  const ta = document.getElementById('intrebare-input');
  if (ta) {
    ta.addEventListener('input', () => {
      const len = ta.value.length;
      const cc = document.getElementById('char-count');
      if (cc) {
        cc.textContent = `${len} / 1000`;
        cc.style.color = len > 900 ? 'var(--error)' : '';
      }
    });
    ta.addEventListener('keydown', e => {
      if (e.key === 'Enter' && e.ctrlKey) intreaba();
    });
  }

  const qta = document.getElementById('quiz-raspuns-input');
  if (qta) {
    qta.addEventListener('input', () => {
      const len = qta.value.length;
      const cc = document.getElementById('quiz-char-count');
      if (cc) cc.textContent = `${len} / 1500`;
    });
  }
}

function setIntrebare(text) {
  const ta = document.getElementById('intrebare-input');
  if (ta) {
    ta.value = text;
    const cc = document.getElementById('char-count');
    if (cc) cc.textContent = `${text.length} / 1000`;
    ta.focus();
  }
}

// ===== INTREABA AI =====
async function intreaba() {
  const intrebare = document.getElementById('intrebare-input').value.trim();
  if (!intrebare) { showToast('Scrie o intrebare mai intai!', 'error'); return; }
  if (intrebare.length > 1000) { showToast('Intrebarea e prea lunga!', 'error'); return; }

  setLoadingBtn('intreaba-btn', 'btn-text', 'btn-spinner', true);

  try {
    const endpoint = state.materie === 'SO' ? '/api/so/intreaba' : '/api/intreaba';
    const res = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ intrebare, nivel_nota: state.nota })
    });

    const data = await res.json();

    if (data.raspuns) {
      state.raspunsActual = { intrebare, raspuns: data.raspuns };
      showRaspuns(data.raspuns, intrebare);
      incrementStreak();
      loadStatistici();
      showToast('Raspuns generat!', 'success');
    } else if (data.error === 'intrebare_nepermisa') {
      showMesajEtica(data.motiv);
      showToast('Intrebare nepermisa!', 'error');
    } else {
      showToast(data.error || 'Eroare la generare!', 'error');
    }
  } catch (err) {
    showToast('Serverul nu raspunde. Verifica daca backend-ul ruleaza!', 'error');
    console.error(err);
  }

  setLoadingBtn('intreaba-btn', 'btn-text', 'btn-spinner', false);
}

function showRaspuns(raspuns, intrebare) {
  const card = document.getElementById('raspuns-card');
  const text = document.getElementById('raspuns-text');
  const badge = document.getElementById('raspuns-nivel-tag');
  const sursa = document.getElementById('raspuns-sursa');

  text.innerHTML = formatText(raspuns);
  badge.textContent = `Nota ${state.nota}`;

  const surse = {
    POO: '📖 Sursa: Breazu Macarie — Programare OO',
    SO:  '📖 Sursa: Silberschatz — Operating System Concepts'
  };
  sursa.textContent = surse[state.materie] || '📖 ULBS Coach AI';

  card.style.display = 'block';
  card.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showMesajEtica(motiv) {
  const card = document.getElementById('raspuns-card');
  const text = document.getElementById('raspuns-text');
  text.innerHTML = `
    <div style="text-align:center;padding:1.5rem">
      <div style="font-size:2.5rem;margin-bottom:0.8rem">⚠️</div>
      <h3 style="color:var(--error);margin-bottom:0.5rem">Intrebare nepermisa</h3>
      <p style="color:var(--text-3);font-size:14px">${motiv || 'Aceasta intrebare nu este adecvata pentru contextul educational.'}</p>
    </div>
  `;
  card.style.display = 'block';
}

function newIntrebare() {
  document.getElementById('raspuns-card').style.display = 'none';
  document.getElementById('intrebare-input').value = '';
  document.getElementById('char-count').textContent = '0 / 1000';
  state.raspunsActual = null;
  document.getElementById('intrebare-input').focus();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function copyRaspuns() {
  const text = document.getElementById('raspuns-text').textContent;
  navigator.clipboard.writeText(text).then(() => showToast('Copiat!', 'success'));
}

async function salveazaRaspunsActual() {
  if (!state.raspunsActual) {
    showToast('Nu exista raspuns de salvat!', 'error');
    return;
  }
  await salveazaIntrebareAPI(
    state.materie,
    state.raspunsActual.intrebare,
    state.raspunsActual.raspuns,
    'mediu'
  );
}

// ===== CARTONASE =====
async function genereazaCartonase() {
  const topic = document.getElementById('topic-input').value.trim();
  const numar = parseInt(document.getElementById('numar-cartonase').value);

  if (!topic) { showToast('Scrie un topic mai intai!', 'error'); return; }

  const btn = document.getElementById('genereaza-btn');
  btn.disabled = true;
  btn.textContent = '⏳ Se genereaza...';

  try {
    const res = await fetch(`${API_URL}/api/cartonase`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, numar, materie: state.materie, tip: 'teorie' })
    });

    const data = await res.json();

    if (data.cartonase && data.cartonase.length > 0) {
      state.cartonaseData = data.cartonase;
      afiseazaCartonase(data.cartonase);
      showToast(`${data.cartonase.length} cartonase generate pentru ${state.materie}!`, 'success');
    } else {
      showToast(data.error || 'Eroare la generare!', 'error');
    }
  } catch (err) {
    showToast('Serverul nu raspunde!', 'error');
    console.error(err);
  }

  btn.disabled = false;
  btn.textContent = '🃏 Genereaza Cartonase';
}

function afiseazaCartonase(cartonase) {
  const container = document.getElementById('cartonase-container');
  container.innerHTML = cartonase.map((c, i) => `
    <div class="cartonas" id="cartonas-${i}">
      <div class="cartonas-front" onclick="toggleCartonas(${i})">
        <span class="cartonas-nr">${i + 1}</span>
        <span class="cartonas-intrebare">${escapeHtml(c.intrebare)}</span>
        <span class="dif-tag dif-${c.dificultate}">${c.dificultate}</span>
        <button class="btn-ghost" onclick="event.stopPropagation();openModal(${i})" title="Raspuns complet" style="padding:4px 8px;font-size:11px">👁️</button>
        <span class="cartonas-arrow">▶</span>
      </div>
      <div class="cartonas-back">${formatText(c.raspuns)}</div>
    </div>
  `).join('');

  document.getElementById('tab-cartonase').scrollIntoView({ behavior: 'smooth' });
}

function toggleCartonas(index) {
  const el = document.getElementById(`cartonas-${index}`);
  if (el) el.classList.toggle('open');
}

// ===== MODAL =====
let currentCartonasIndex = 0;

function openModal(index) {
  currentCartonasIndex = index;
  const c = state.cartonaseData[index];
  if (!c) return;

  document.getElementById('modal-intrebare').textContent = c.intrebare;

  const dif = document.getElementById('modal-dif-tag');
  dif.textContent = c.dificultate;
  dif.className = `dif-tag dif-${c.dificultate}`;

  document.getElementById('modal-body').innerHTML = formatText(c.raspuns);
  document.getElementById('modal-overlay').classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('active');
  document.body.style.overflow = '';
}

function salveazaCartonas(index) {
  const c = state.cartonaseData[index];
  if (!c) return;
  salveazaIntrebareAPI(state.materie, c.intrebare, c.raspuns, c.dificultate);
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});

// ===== QUIZ =====
async function startQuiz() {
  const topic = document.getElementById('quiz-topic-input').value.trim();
  const numar = parseInt(document.getElementById('quiz-numar').value);
  const tip   = document.getElementById('quiz-tip').value;

  if (!topic) { showToast('Scrie un topic mai intai!', 'error'); return; }

  const btn = document.getElementById('start-quiz-btn');
  btn.disabled = true;
  btn.textContent = '⏳ Se genereaza...';

  try {
    const res = await fetch(`${API_URL}/api/cartonase`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, numar, materie: state.materie, tip })
    });

    const data = await res.json();

    if (data.cartonase && data.cartonase.length > 0) {
      state.quiz = {
        intrebari: data.cartonase,
        indexCurent: 0,
        scorTotal: 0,
        numar: data.cartonase.length,
        materie: state.materie,
        topic,
        tip,
        startTime: Date.now(),
        raspunsuri: [],
        timerInterval: null,
        timpRamas: 120
      };

      document.getElementById('quiz-start-screen').style.display = 'none';
      document.getElementById('quiz-activ').style.display = 'block';
      document.getElementById('quiz-feedback-screen').style.display = 'none';
      document.getElementById('quiz-rezultat').style.display = 'none';
      document.getElementById('quiz-materie-tag').textContent = state.materie;

      afiseazaIntrebareQuiz();
      showToast('Quiz generat! Succes! 🎯', 'success');
    } else {
      showToast(data.error || 'Eroare la generare quiz!', 'error');
    }
  } catch (err) {
    showToast('Serverul nu raspunde!', 'error');
    console.error(err);
  }

  btn.disabled = false;
  btn.textContent = '🎯 Incepe Quiz';
}

function afiseazaIntrebareQuiz() {
  const q = state.quiz;
  const idx = q.indexCurent;
  const intrebare = q.intrebari[idx];

  document.getElementById('quiz-progress-text').textContent = `Intrebarea ${idx + 1} din ${q.numar}`;
  document.getElementById('quiz-progress-fill').style.width = `${(idx / q.numar) * 100}%`;
  document.getElementById('quiz-question-number').textContent = String(idx + 1).padStart(2, '0');
  document.getElementById('quiz-question-dif').textContent = intrebare.dificultate;
  document.getElementById('quiz-intrebare').textContent = intrebare.intrebare;
  document.getElementById('quiz-raspuns-input').value = '';
  document.getElementById('quiz-char-count').textContent = '0 / 1500';

  // Timer
  startTimer();
}

function startTimer() {
  stopTimer();
  state.quiz.timpRamas = 120;
  updateTimerDisplay();

  state.quiz.timerInterval = setInterval(() => {
    state.quiz.timpRamas--;
    updateTimerDisplay();

    const timerEl = document.getElementById('quiz-timer');
    if (state.quiz.timpRamas <= 20) {
      timerEl.classList.add('urgent');
    } else {
      timerEl.classList.remove('urgent');
    }

    if (state.quiz.timpRamas <= 0) {
      stopTimer();
      showToast('Timpul a expirat! Raspunsul a fost trimis automat.', 'info');
      submitRaspuns();
    }
  }, 1000);
}

function stopTimer() {
  if (state.quiz.timerInterval) {
    clearInterval(state.quiz.timerInterval);
    state.quiz.timerInterval = null;
  }
}

function updateTimerDisplay() {
  const min = Math.floor(state.quiz.timpRamas / 60);
  const sec = state.quiz.timpRamas % 60;
  const display = document.getElementById('timer-display');
  if (display) display.textContent = `${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

async function submitRaspuns() {
  stopTimer();

  const raspunsStudent = document.getElementById('quiz-raspuns-input').value.trim();
  const intrebareCurenta = state.quiz.intrebari[state.quiz.indexCurent];

  setLoadingBtn('quiz-submit-btn', 'quiz-btn-text', 'quiz-btn-spinner', true);

  try {
    const res = await fetch(`${API_URL}/api/quiz/evalueaza`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        intrebare: intrebareCurenta.intrebare,
        raspuns_student: raspunsStudent || '(fara raspuns)',
        raspuns_corect: intrebareCurenta.raspuns,
        materie: state.quiz.materie
      })
    });

    const data = await res.json();

    if (data.nota !== undefined) {
      state.quiz.scorTotal += data.nota;
      state.quiz.raspunsuri.push({
        intrebare: intrebareCurenta.intrebare,
        raspuns_student: raspunsStudent,
        raspuns_corect: intrebareCurenta.raspuns,
        nota: data.nota,
        feedback: data.feedback || ''
      });

      afiseazaFeedbackQuiz(data, intrebareCurenta.raspuns);
    } else {
      showToast('Eroare la evaluare!', 'error');
    }
  } catch (err) {
    showToast('Serverul nu raspunde!', 'error');
    console.error(err);
  }

  setLoadingBtn('quiz-submit-btn', 'quiz-btn-text', 'quiz-btn-spinner', false);
}

function afiseazaFeedbackQuiz(rezultat, raspunsCorect) {
  const esteCorect = rezultat.nota >= 6;
  const clasa = esteCorect ? 'corect' : 'gresit';
  const emoji = esteCorect ? '✅' : '❌';

  document.getElementById('feedback-card-content').innerHTML = `
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:1.2rem">
      <div class="feedback-nota-display">${rezultat.nota}/10</div>
      <div>
        <div style="font-size:1.4rem">${emoji}</div>
        <div style="font-size:12px;color:var(--text-3)">${esteCorect ? 'Raspuns corect!' : 'Mai studiaza!'}</div>
      </div>
    </div>
    <div class="feedback-section">
      <h4>💬 Feedback</h4>
      <p>${escapeHtml(rezultat.feedback || 'Continua sa studiezi!')}</p>
    </div>
    ${rezultat.explicatie ? `
    <div class="feedback-section">
      <h4>📖 Explicatie</h4>
      <p>${escapeHtml(rezultat.explicatie)}</p>
    </div>
    ` : ''}
    <div class="raspuns-corect-box">
      <label>✓ Raspuns de referinta</label>
      <p>${escapeHtml(raspunsCorect)}</p>
    </div>
  `;

  const feedbackCard = document.getElementById('feedback-card-content');
  feedbackCard.className = `card feedback-card ${clasa}`;

  const esteUltima = state.quiz.indexCurent === state.quiz.numar - 1;
  document.getElementById('quiz-next-btn').textContent =
    esteUltima ? '🏆 Vezi Rezultatul Final' : 'Urmatoarea →';

  document.getElementById('quiz-activ').style.display = 'none';
  document.getElementById('quiz-feedback-screen').style.display = 'block';
}

function nextIntrebare() {
  state.quiz.indexCurent++;

  if (state.quiz.indexCurent >= state.quiz.numar) {
    afiseazaRezultatFinal();
  } else {
    document.getElementById('quiz-feedback-screen').style.display = 'none';
    document.getElementById('quiz-activ').style.display = 'block';
    afiseazaIntrebareQuiz();
  }
}

async function afiseazaRezultatFinal() {
  stopTimer();

  const q = state.quiz;
  const notaMedie = +(q.scorTotal / q.numar).toFixed(1);
  const timpTotal = Math.round((Date.now() - q.startTime) / 1000);
  const corecte  = q.raspunsuri.filter(r => r.nota >= 6).length;
  const gresite  = q.numar - corecte;

  let emoji = '📚', mesaj = '';
  if (notaMedie >= 9)      { emoji = '🏆'; mesaj = 'Exceptional! Esti mai mult decat pregatit pentru examen!'; }
  else if (notaMedie >= 7) { emoji = '🎯'; mesaj = 'Foarte bine! Cu putin efort in plus, esti gata!'; }
  else if (notaMedie >= 5) { emoji = '📖'; mesaj = 'Ok! Continua sa studiezi si vei reusi!'; }
  else                      { emoji = '💪'; mesaj = 'Nu te descuraja! Practica face perfectul.'; }

  document.getElementById('rezultat-emoji').textContent = emoji;
  document.getElementById('rezultat-nota').textContent  = `${notaMedie}/10`;
  document.getElementById('rezultat-mesaj').textContent = mesaj;
  document.getElementById('rez-corecte').textContent = corecte;
  document.getElementById('rez-gresite').textContent = gresite;
  document.getElementById('rez-timp').textContent    = `${timpTotal}s`;

  // Ce trebuie sa inveti (intrebarile gresite)
  const greseliItems = q.raspunsuri.filter(r => r.nota < 6);
  if (greseliItems.length > 0) {
    const ceInvataEl = document.getElementById('ce-invata-section');
    const lista = document.getElementById('ce-invata-lista');
    lista.innerHTML = greseliItems.map(g => `
      <div class="ce-invata-item">
        <strong>Q:</strong> ${escapeHtml(g.intrebare.substring(0, 80))}...
        <span style="color:var(--error);margin-left:8px">Nota: ${g.nota}/10</span>
      </div>
    `).join('');
    ceInvataEl.style.display = 'block';
  }

  document.getElementById('quiz-progress-fill').style.width = '100%';
  document.getElementById('quiz-activ').style.display        = 'none';
  document.getElementById('quiz-feedback-screen').style.display = 'none';
  document.getElementById('quiz-rezultat').style.display     = 'flex';
  document.getElementById('quiz-rezultat').style.flexDirection = 'column';
  document.getElementById('quiz-rezultat').style.gap = '1rem';

  // Salveaza sesiunea in DB
  try {
    await fetch(`${API_URL}/api/quiz/sesiune`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        materie: q.materie,
        topic: q.topic,
        tip: q.tip,
        numar_intrebari: q.numar,
        scor_final: q.scorTotal,
        nota_finala: notaMedie,
        raspunsuri: q.raspunsuri
      })
    });
  } catch (err) {
    console.error('Eroare salvare sesiune:', err);
  }

  loadStatistici();
}

function resetQuiz() {
  stopTimer();
  state.quiz = {
    intrebari: [], indexCurent: 0, scorTotal: 0,
    numar: 0, materie: state.materie, topic: '', tip: 'teorie',
    startTime: null, raspunsuri: [], timerInterval: null, timpRamas: 120
  };

  document.getElementById('quiz-start-screen').style.display  = 'block';
  document.getElementById('quiz-activ').style.display          = 'none';
  document.getElementById('quiz-feedback-screen').style.display = 'none';
  document.getElementById('quiz-rezultat').style.display        = 'none';
  document.getElementById('quiz-topic-input').value = '';
  document.getElementById('quiz-progress-fill').style.width = '0%';
  document.getElementById('timer-display').textContent = '02:00';

  loadQuizIstoric();
}

function salveazaIntrebareaQuiz() {
  const q = state.quiz;
  const raspuns = q.raspunsuri[q.indexCurent - 1];
  if (!raspuns) return;
  salveazaIntrebareAPI(q.materie, raspuns.intrebare, raspuns.raspuns_corect, 'mediu');
}

// ===== STATISTICI =====
async function loadStatistici() {
  try {
    const res = await fetch(`${API_URL}/api/statistici`);
    const data = await res.json();

    const total = data.length;
    const azi = data.filter(item => {
      return new Date(item.data).toDateString() === new Date().toDateString();
    }).length;

    // Hero stats
    updateEl('hero-total', total);
    updateEl('hero-streak', getStreak());

    // Statistici tab
    updateEl('stat-total', total);
    updateEl('stat-azi', azi);

    if (data.length > 0) {
      const noteCounts = {};
      const materieCounts = {};

      data.forEach(item => {
        noteCounts[item.nota] = (noteCounts[item.nota] || 0) + 1;
        const m = item.materie || 'POO';
        materieCounts[m] = (materieCounts[m] || 0) + 1;
      });

      const notaPref = Object.keys(noteCounts).reduce((a, b) =>
        noteCounts[a] > noteCounts[b] ? a : b
      );
      updateEl('stat-nivel', notaPref);

      // Grafic materii
      const chart = document.getElementById('materie-chart');
      if (chart) {
        const max = Math.max(...Object.values(materieCounts));
        chart.innerHTML = Object.entries(materieCounts).map(([materie, count]) => `
          <div class="chart-row">
            <span class="chart-label">${materie}</span>
            <div class="chart-bar-bg">
              <div class="chart-bar-fill" style="width:${(count / max * 100)}%"></div>
            </div>
            <span class="chart-count">${count}</span>
          </div>
        `).join('');
      }
    } else {
      updateEl('stat-nivel', '—');
      const chart = document.getElementById('materie-chart');
      if (chart) chart.innerHTML = '<p style="color:var(--text-4);font-size:13px;text-align:center;padding:1rem">Nu ai intrebari inca.</p>';
    }

    // Lista istoric
    const lista = document.getElementById('statistici-lista');
    if (lista) {
      if (data.length === 0) {
        lista.innerHTML = '<div class="empty-state"><span>📝</span><p>Nu ai intrebari inca.<br/>Incepe sa inveti!</p></div>';
      } else {
        lista.innerHTML = data.slice(0, 15).map(item => `
          <div class="istoric-item">
            <span class="istoric-intrebare">${escapeHtml(item.intrebare)}</span>
            <span class="istoric-materie">${item.materie || 'POO'}</span>
            <span class="istoric-nota">Nota ${item.nota}</span>
            <span class="istoric-data">${formatData(item.data)}</span>
          </div>
        `).join('');
      }
    }

  } catch (err) {
    console.error('Eroare statistici:', err);
  }
}

async function loadQuizIstoric() {
  try {
    const res = await fetch(`${API_URL}/api/statistici/quiz?limit=5`);
    const data = await res.json();

    updateEl('hero-quiz', data.length);
    updateEl('stat-streak-big', `${getStreak()}🔥`);

    const lista = document.getElementById('quiz-istoric-lista');
    if (!lista) return;

    if (data.length === 0) {
      lista.innerHTML = '<p style="color:var(--text-4);font-size:13px">Nicio sesiune de quiz inca.</p>';
    } else {
      lista.innerHTML = data.map(s => `
        <div class="quiz-sesiune-item">
          <div>
            <strong style="font-size:13px">${escapeHtml(s.topic)}</strong>
            <div style="font-size:11px;color:var(--text-3)">${s.materie} · ${s.tip} · ${s.numar_intrebari} intrebari · ${formatData(s.data)}</div>
          </div>
          <span class="quiz-sesiune-nota">${s.nota}/10</span>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('Eroare quiz istoric:', err);
  }
}

async function loadQuizIstoricFull() {
  try {
    const res = await fetch(`${API_URL}/api/statistici/quiz?limit=20`);
    const data = await res.json();

    const lista = document.getElementById('quiz-istoric-full');
    if (!lista) return;

    if (data.length === 0) {
      lista.innerHTML = '<div class="empty-state"><span>🎯</span><p>Nu ai sesiuni de quiz inca.</p></div>';
    } else {
      lista.innerHTML = data.map(s => `
        <div class="quiz-sesiune-item">
          <div>
            <strong style="font-size:13px">${escapeHtml(s.topic)}</strong>
            <div style="font-size:11px;color:var(--text-3)">${s.materie} · ${s.tip} · ${s.numar_intrebari} intrebari · ${formatData(s.data)}</div>
          </div>
          <span class="quiz-sesiune-nota">${s.nota}/10</span>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error(err);
  }
}

// ===== SALVATE =====
async function salveazaIntrebareAPI(materie, intrebare, raspuns, dificultate) {
  try {
    const res = await fetch(`${API_URL}/api/bookmark`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ materie, intrebare, raspuns, dificultate })
    });
    const data = await res.json();
    if (data.success) {
      showToast('Intrebare salvata! 🔖', 'success');
    }
  } catch (err) {
    showToast('Eroare la salvare!', 'error');
  }
}

async function loadSalvate() {
  const materie = document.getElementById('filter-materie-salvate')?.value || '';
  try {
    const url = materie ? `${API_URL}/api/bookmarks?materie=${materie}` : `${API_URL}/api/bookmarks`;
    const res = await fetch(url);
    const data = await res.json();

    const lista = document.getElementById('salvate-lista');
    if (!lista) return;

    if (data.length === 0) {
      lista.innerHTML = '<div class="empty-state"><span>🔖</span><p>Nu ai intrebari salvate inca.<br/>Apasa 🔖 pe orice raspuns pentru a-l salva.</p></div>';
    } else {
      lista.innerHTML = data.map(item => `
        <div class="salvata-item" onclick="showSalvataModal('${escapeAttr(item.intrebare)}', '${escapeAttr(item.raspuns || '')}')">
          <h4>${escapeHtml(item.intrebare)}</h4>
          <p>${escapeHtml((item.raspuns || '').substring(0, 120))}...</p>
          <div style="display:flex;gap:8px;margin-top:6px">
            <span class="dif-tag dif-${item.dificultate || 'mediu'}">${item.dificultate || 'mediu'}</span>
            <span style="font-size:11px;color:var(--text-4)">${item.materie}</span>
            <span style="font-size:11px;color:var(--text-4)">${formatData(item.created_at)}</span>
          </div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error(err);
  }
}

function showSalvataModal(intrebare, raspuns) {
  document.getElementById('modal-intrebare').textContent = intrebare;
  document.getElementById('modal-dif-tag').textContent = '';
  document.getElementById('modal-body').innerHTML = formatText(raspuns || 'Nu exista raspuns salvat.');
  document.getElementById('modal-overlay').classList.add('active');
  document.body.style.overflow = 'hidden';
}

// ===== UPLOAD PDF =====
let selectedPdfFile = null;

function initUploadDragDrop() {
  const area = document.getElementById('upload-area');
  if (!area) return;

  area.addEventListener('dragover', e => {
    e.preventDefault();
    area.classList.add('dragover');
  });
  area.addEventListener('dragleave', () => area.classList.remove('dragover'));
  area.addEventListener('drop', e => {
    e.preventDefault();
    area.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.pdf')) {
      handlePdfFile(file);
    } else {
      showToast('Doar fisiere PDF!', 'error');
    }
  });
}

function handlePdfSelect(event) {
  const file = event.target.files[0];
  if (file) handlePdfFile(file);
}

function handlePdfFile(file) {
  selectedPdfFile = file;
  const preview = document.getElementById('upload-preview');
  const filename = document.getElementById('upload-filename');
  if (preview) preview.style.display = 'flex';
  if (filename) filename.textContent = `📄 ${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`;
  showToast(`Fisier selectat: ${file.name}`, 'info');
}

function clearUpload() {
  selectedPdfFile = null;
  document.getElementById('pdf-input').value = '';
  const preview = document.getElementById('upload-preview');
  if (preview) preview.style.display = 'none';
}

async function uploadPdf() {
  if (!selectedPdfFile) { showToast('Selecteaza un PDF mai intai!', 'error'); return; }

  const materie = document.getElementById('upload-materie').value.trim();
  const profesor = document.getElementById('upload-profesor').value.trim();

  if (!materie) { showToast('Scrie numele materiei!', 'error'); return; }

  const btn = document.getElementById('upload-btn');
  const btnText = document.getElementById('upload-btn-text');
  const btnSpinner = document.getElementById('upload-btn-spinner');

  btn.disabled = true;
  btnText.style.display = 'none';
  btnSpinner.style.display = 'inline';

  try {
    const formData = new FormData();
    formData.append('pdf', selectedPdfFile);
    formData.append('materie_nume', materie);
    formData.append('profesor', profesor);

    const res = await fetch(`${API_URL}/api/upload-pdf`, {
      method: 'POST',
      body: formData
    });

    const data = await res.json();

    if (data.success) {
      showToast(`✅ PDF procesat! ${data.caractere} caractere extrase.`, 'success');
      clearUpload();
      document.getElementById('upload-materie').value = '';
      document.getElementById('upload-profesor').value = '';
      loadCarti();
    } else {
      showToast(data.error || 'Eroare la procesare!', 'error');
    }
  } catch (err) {
    showToast('Eroare la upload!', 'error');
    console.error(err);
  }

  btn.disabled = false;
  btnText.style.display = 'inline';
  btnSpinner.style.display = 'none';
}

async function loadCarti() {
  try {
    const res = await fetch(`${API_URL}/api/carti`);
    const data = await res.json();

    const lista = document.getElementById('carti-lista');
    if (!lista) return;

    if (data.length === 0) {
      lista.innerHTML = '<div class="empty-state"><span>📚</span><p>Nu ai uploadat nicio carte inca.</p></div>';
    } else {
      lista.innerHTML = data.map(c => `
        <div class="carte-item">
          <div class="carte-info">
            <h4>📚 ${escapeHtml(c.materie_nume)}</h4>
            <p>${escapeHtml(c.profesor || 'Profesor necunoscut')} · ${(c.size_chars / 1000).toFixed(0)}k caractere · ${formatData(c.created_at)}</p>
          </div>
          <span class="tag-new">✓ Activ</span>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error(err);
  }
}

// ===== STREAK =====
function getStreak() {
  return parseInt(localStorage.getItem('ulbs-streak') || '0');
}

function incrementStreak() {
  const today = new Date().toDateString();
  const lastDay = localStorage.getItem('ulbs-streak-day');
  let streak = getStreak();

  if (lastDay === today) return; // Deja incrementat azi

  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);

  if (lastDay === yesterday.toDateString()) {
    streak++;
  } else if (!lastDay) {
    streak = 1;
  } else {
    streak = 1; // S-a rupt streak-ul
  }

  localStorage.setItem('ulbs-streak', streak);
  localStorage.setItem('ulbs-streak-day', today);
  loadStreak();
}

function loadStreak() {
  const streak = getStreak();
  updateEl('streak-count', streak);
  updateEl('hero-streak', streak);
  updateEl('stat-streak-big', `${streak}🔥`);
}

// ===== HELPERS =====
function formatText(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/```(\w+)?\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n\n/g, '</p><p style="margin-top:0.6rem">')
    .replace(/\n/g, '<br>');
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function escapeAttr(str) {
  if (!str) return '';
  return String(str).replace(/'/g, '&#39;').replace(/"/g, '&quot;').substring(0, 200);
}

function formatData(dataStr) {
  if (!dataStr) return '';
  const d = new Date(dataStr);
  return d.toLocaleDateString('ro-RO', {
    day: '2-digit', month: '2-digit', year: '2-digit',
    hour: '2-digit', minute: '2-digit'
  });
}

function updateEl(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function setLoadingBtn(btnId, textId, spinnerId, loading) {
  const btn    = document.getElementById(btnId);
  const text   = document.getElementById(textId);
  const spinner = document.getElementById(spinnerId);
  if (btn)    btn.disabled       = loading;
  if (text)   text.style.display = loading ? 'none'   : 'inline';
  if (spinner) spinner.style.display = loading ? 'inline' : 'none';
}

function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}