/**
 * InstaSorteio Mobile - Frontend Logic & Real-time State Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  // State
  let config = {};
  let usersCount = 0;
  let isRunning = false;
  let pollInterval = null;
  let deferredInstallPrompt = null;

  // DOM Elements
  const statusBadge = document.getElementById('statusBadge');
  const statusBadgeText = document.getElementById('statusBadgeText');
  const postUrlInput = document.getElementById('postUrlInput');
  const btnPasteUrl = document.getElementById('btnPasteUrl');
  const chunkVal = document.getElementById('chunkVal');
  const btnDecChunk = document.getElementById('btnDecChunk');
  const btnIncChunk = document.getElementById('btnIncChunk');
  const calcSummary = document.getElementById('calcSummary');
  const btnStartBot = document.getElementById('btnStartBot');
  const btnStopBot = document.getElementById('btnStopBot');
  const liveStatusText = document.getElementById('liveStatusText');
  const livePercentText = document.getElementById('livePercentText');
  const progressFill = document.getElementById('progressFill');
  const commentPreview = document.getElementById('commentPreview');
  const previewText = document.getElementById('previewText');
  const metricPosted = document.getElementById('metricPosted');
  const metricErrors = document.getElementById('metricErrors');
  const metricPending = document.getElementById('metricPending');
  const miniLogBox = document.getElementById('miniLogBox');
  const fullLogBox = document.getElementById('fullLogBox');
  const btnClearLogs = document.getElementById('btnClearLogs');
  const btnGoToLogs = document.getElementById('btnGoToLogs');

  // Settings DOM
  const delayMinInput = document.getElementById('delayMinInput');
  const delayMaxInput = document.getElementById('delayMaxInput');
  const batchSizeInput = document.getElementById('batchSizeInput');
  const batchPauseInput = document.getElementById('batchPauseInput');
  const toggleFrases = document.getElementById('toggleFrases');
  const toggleEmojis = document.getElementById('toggleEmojis');
  const toggleVisible = document.getElementById('toggleVisible');
  const btnSaveConfig = document.getElementById('btnSaveConfig');

  // Users DOM
  const usersCountBadge = document.getElementById('usersCountBadge');
  const usersTextArea = document.getElementById('usersTextArea');
  const btnClearUsers = document.getElementById('btnClearUsers');
  const btnSaveUsers = document.getElementById('btnSaveUsers');

  // PWA & Toast DOM
  const installBanner = document.getElementById('installBanner');
  const btnInstallApp = document.getElementById('btnInstallApp');
  const appToast = document.getElementById('appToast');

  // ==================== TOAST NOTIFICATION ====================
  function showToast(msg, duration = 3000) {
    appToast.textContent = msg;
    appToast.classList.add('show');
    setTimeout(() => {
      appToast.classList.remove('show');
    }, duration);
  }

  // ==================== NAVIGATION TABS ====================
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  function switchTab(tabId) {
    tabButtons.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabId);
    });
    tabContents.forEach(content => {
      content.classList.toggle('active', content.id === tabId);
    });
  }

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  if (btnGoToLogs) {
    btnGoToLogs.addEventListener('click', () => switchTab('tab-logs'));
  }

  // ==================== API CALLS ====================

  // Carregar Configurações
  async function loadConfig() {
    try {
      const res = await fetch('/api/config');
      config = await res.json();
      
      if (config.url_post && config.url_post !== 'https://www.instagram.com/p/') {
        postUrlInput.value = config.url_post;
      }
      chunkVal.textContent = config.usuarios_por_comentario || 3;
      delayMinInput.value = config.delay_min_segundos || 45;
      delayMaxInput.value = config.delay_max_segundos || 85;
      batchSizeInput.value = config.comentarios_por_lote || 5;
      batchPauseInput.value = config.pausa_lote_segundos || 180;
      toggleFrases.checked = config.adicionar_frase_aleatoria !== false;
      toggleEmojis.checked = config.adicionar_emoji_aleatorio !== false;
      toggleVisible.checked = !!config.modo_visivel;

      updateCalcSummary();
    } catch (e) {
      console.error('Erro ao carregar config:', e);
    }
  }

  // Salvar Configurações
  async function saveConfig() {
    const updated = {
      url_post: postUrlInput.value.trim(),
      usuarios_por_comentario: parseInt(chunkVal.textContent, 10),
      delay_min_segundos: parseInt(delayMinInput.value, 10) || 45,
      delay_max_segundos: parseInt(delayMaxInput.value, 10) || 85,
      comentarios_por_lote: parseInt(batchSizeInput.value, 10) || 5,
      pausa_lote_segundos: parseInt(batchPauseInput.value, 10) || 180,
      adicionar_frase_aleatoria: toggleFrases.checked,
      adicionar_emoji_aleatorio: toggleEmojis.checked,
      modo_visivel: toggleVisible.checked
    };

    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updated)
      });
      const data = await res.json();
      if (data.success) {
        config = data.config;
        showToast('✅ Configurações salvas com sucesso!');
      } else {
        showToast('❌ Erro ao salvar configurações.');
      }
    } catch (e) {
      showToast('❌ Erro de conexão ao salvar.');
    }
  }

  // Carregar Usuários
  async function loadUsers() {
    try {
      const res = await fetch('/api/users');
      const data = await res.json();
      usersTextArea.value = data.content || '';
      usersCount = data.total || 0;
      usersCountBadge.textContent = `${usersCount} amigos`;
      updateCalcSummary();
    } catch (e) {
      console.error('Erro ao carregar usuários:', e);
    }
  }

  // Salvar Usuários
  async function saveUsers() {
    const content = usersTextArea.value;
    try {
      const res = await fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      });
      const data = await res.json();
      if (data.success) {
        usersCount = data.total_users;
        usersCountBadge.textContent = `${usersCount} amigos`;
        updateCalcSummary();
        showToast(`✅ Lista salva! ${usersCount} amigos detectados.`);
      } else {
        showToast('❌ Erro ao salvar lista de usuários.');
      }
    } catch (e) {
      showToast('❌ Erro de conexão ao salvar usuários.');
    }
  }

  // Atualizar Resumo de Cálculo
  function updateCalcSummary() {
    const chunk = parseInt(chunkVal.textContent, 10) || 3;
    if (usersCount > 0) {
      const totalComments = Math.ceil(usersCount / chunk);
      calcSummary.textContent = `📊 ${usersCount} amigos = ~${totalComments} comentários (${chunk} amigos cada)`;
    } else {
      calcSummary.textContent = `⚠️ Adicione nomes na aba 'Lista @'`;
    }
  }

  // Atualizar Status do Bot
  async function checkStatus() {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();

      isRunning = data.is_running;
      btnStartBot.disabled = isRunning;
      btnStopBot.disabled = !isRunning;

      // Status Badge
      statusBadge.classList.remove('running', 'stopped');
      if (isRunning) {
        statusBadge.classList.add('running');
        statusBadgeText.textContent = 'Rodando';
      } else {
        statusBadgeText.textContent = 'Pronto';
      }

      // Progress & Text
      liveStatusText.textContent = `Status: ${data.status_message || 'Pronto'}`;
      livePercentText.textContent = `${data.percent}%`;
      progressFill.style.width = `${data.percent}%`;

      metricPosted.textContent = data.posted || 0;
      metricErrors.textContent = data.errors || 0;
      metricPending.textContent = data.pending || 0;

      if (data.current_comment) {
        commentPreview.style.display = 'block';
        previewText.textContent = data.current_comment;
      } else {
        commentPreview.style.display = 'none';
      }

    } catch (e) {
      statusBadgeText.textContent = 'Desconectado';
    }
  }

  // ==================== INICIAR / PARAR BOT ====================

  btnStartBot.addEventListener('click', async () => {
    const url = postUrlInput.value.trim();
    if (!url || !url.includes('instagram.com/')) {
      showToast('⚠️ Cole o link do post do Instagram primeiro!');
      postUrlInput.focus();
      return;
    }

    if (usersCount === 0) {
      showToast('⚠️ A lista de usuários está vazia! Adicione amigos na aba "Lista @".');
      switchTab('tab-users');
      return;
    }

    // Salva URL e configurações antes de iniciar
    await saveConfig();

    try {
      btnStartBot.disabled = true;
      const res = await fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url_post: url })
      });
      const data = await res.json();
      if (data.success) {
        showToast('🚀 Bot iniciado com sucesso!');
        checkStatus();
      } else {
        showToast(`❌ ${data.message || 'Falha ao iniciar'}`);
      }
    } catch (e) {
      showToast('❌ Erro de conexão ao iniciar bot.');
    }
  });

  btnStopBot.addEventListener('click', async () => {
    if (!confirm('Deseja realmente pausar o bot? O progresso ficará salvo.')) return;
    try {
      btnStopBot.disabled = true;
      const res = await fetch('/api/stop', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        showToast('⏹️ Parada solicitada. Aguardando...');
      }
    } catch (e) {
      showToast('❌ Erro de conexão ao parar bot.');
    }
  });

  // ==================== EVENTOS DA INTERFACE ====================

  // Botão Colar Link
  btnPasteUrl.addEventListener('click', async () => {
    try {
      if (navigator.clipboard && navigator.clipboard.readText) {
        const text = await navigator.clipboard.readText();
        if (text && text.trim()) {
          postUrlInput.value = text.trim();
          showToast('📋 Link colado da área de transferência!');
          return;
        }
      }
      postUrlInput.focus();
      showToast('💡 Pressione e segure o campo para colar.');
    } catch (e) {
      postUrlInput.focus();
      showToast('💡 Pressione e segure o campo para colar.');
    }
  });

  // Contador de Chunks
  btnDecChunk.addEventListener('click', () => {
    let val = parseInt(chunkVal.textContent, 10);
    if (val > 1) {
      chunkVal.textContent = val - 1;
      updateCalcSummary();
    }
  });

  btnIncChunk.addEventListener('click', () => {
    let val = parseInt(chunkVal.textContent, 10);
    if (val < 10) {
      chunkVal.textContent = val + 1;
      updateCalcSummary();
    }
  });

  // Salvar Config
  btnSaveConfig.addEventListener('click', saveConfig);

  // Salvar Usuários
  btnSaveUsers.addEventListener('click', saveUsers);

  // Limpar Usuários
  btnClearUsers.addEventListener('click', () => {
    if (confirm('Tem certeza que deseja limpar todo o texto da lista?')) {
      usersTextArea.value = '';
      usersCount = 0;
      usersCountBadge.textContent = '0 amigos';
      updateCalcSummary();
    }
  });

  // Limpar Logs
  btnClearLogs.addEventListener('click', () => {
    fullLogBox.innerHTML = '';
    miniLogBox.innerHTML = '<p class="log-line info">Logs limpos.</p>';
  });

  // ==================== REAL-TIME LOGS (SSE) ====================

  function appendLogEntry(entry) {
    const p = document.createElement('p');
    p.className = `log-line ${entry.tag || 'INFO'}`;
    p.textContent = `[${entry.timestamp}] ${entry.text}`;

    fullLogBox.appendChild(p);
    fullLogBox.scrollTop = fullLogBox.scrollHeight;

    // Mini log box
    miniLogBox.appendChild(p.cloneNode(true));
    while (miniLogBox.children.length > 5) {
      miniLogBox.removeChild(miniLogBox.firstChild);
    }
    miniLogBox.scrollTop = miniLogBox.scrollHeight;
  }

  function startLogStream() {
    try {
      const evtSource = new EventSource('/api/logs/stream');
      evtSource.onmessage = (e) => {
        try {
          const entry = JSON.parse(e.data);
          appendLogEntry(entry);
        } catch (err) {}
      };
      evtSource.onerror = () => {
        evtSource.close();
        setTimeout(startLogStream, 4000);
      };
    } catch (e) {
      console.warn('SSE not supported or failed, using fallback.');
    }
  }

  // ==================== PWA INSTALLATION ====================

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;
    installBanner.style.display = 'flex';
  });

  btnInstallApp.addEventListener('click', async () => {
    if (deferredInstallPrompt) {
      deferredInstallPrompt.prompt();
      const { outcome } = await deferredInstallPrompt.userChoice;
      if (outcome === 'accepted') {
        showToast('🎉 Aplicativo adicionado com sucesso!');
      }
      deferredInstallPrompt = null;
      installBanner.style.display = 'none';
    }
  });

  // Registrar Service Worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(err => {
      console.log('SW reg error:', err);
    });
  }

  // ==================== INICIALIZAÇÃO ====================
  loadConfig();
  loadUsers();
  checkStatus();
  startLogStream();

  // Polling de status a cada 1.5s
  pollInterval = setInterval(checkStatus, 1500);
});
