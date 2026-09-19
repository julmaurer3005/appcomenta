/**
 * InstaSorteio Android - Controller Principal da Aplicação
 */

document.addEventListener('DOMContentLoaded', () => {
  let wakeLock = null;

  // DOM
  const appStatusPill = document.getElementById('appStatusPill');
  const appStatusText = document.getElementById('appStatusText');
  const postUrlInput = document.getElementById('postUrlInput');
  const btnPasteUrl = document.getElementById('btnPasteUrl');
  const chunkValue = document.getElementById('chunkValue');
  const btnDecChunk = document.getElementById('btnDecChunk');
  const btnIncChunk = document.getElementById('btnIncChunk');
  const calcSummary = document.getElementById('calcSummary');

  const btnStartBot = document.getElementById('btnStartBot');
  const btnStopBot = document.getElementById('btnStopBot');
  const liveStatus = document.getElementById('liveStatus');
  const livePercent = document.getElementById('livePercent');
  const progressBarFill = document.getElementById('progressBarFill');

  const metricPosted = document.getElementById('metricPosted');
  const metricErrors = document.getElementById('metricErrors');
  const metricPending = document.getElementById('metricPending');

  const miniConsole = document.getElementById('miniConsole');
  const fullConsole = document.getElementById('fullConsole');
  const btnClearLogs = document.getElementById('btnClearLogs');
  const btnGoLogs = document.getElementById('btnGoLogs');

  // Anti-Ban DOM
  const inputDelayMin = document.getElementById('inputDelayMin');
  const inputDelayMax = document.getElementById('inputDelayMax');
  const inputBatchSize = document.getElementById('inputBatchSize');
  const inputBatchPause = document.getElementById('inputBatchPause');
  const chkFrases = document.getElementById('chkFrases');
  const chkEmojis = document.getElementById('chkEmojis');
  const chkWakeLock = document.getElementById('chkWakeLock');
  const btnSaveConfig = document.getElementById('btnSaveConfig');

  // Users DOM
  const usersBadge = document.getElementById('usersBadge');
  const txtUsersArea = document.getElementById('txtUsersArea');
  const fileInputUsers = document.getElementById('fileInputUsers');
  const btnBrowseFile = document.getElementById('btnBrowseFile');
  const btnClearUsers = document.getElementById('btnClearUsers');
  const btnSaveUsers = document.getElementById('btnSaveUsers');

  // Instagram Webview DOM
  const instaIframe = document.getElementById('instaIframe');
  const btnRefreshInsta = document.getElementById('btnRefreshInsta');
  const toast = document.getElementById('toast');

  // ==================== TOAST ====================
  function showToast(text, duration = 3000) {
    toast.textContent = text;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), duration);
  }

  // ==================== TABS ====================
  const tabItems = document.querySelectorAll('.tab-item');
  const tabPanes = document.querySelectorAll('.tab-pane');

  function switchTab(tabId) {
    tabItems.forEach(t => t.classList.toggle('active', t.dataset.tab === tabId));
    tabPanes.forEach(p => p.classList.toggle('active', p.id === tabId));
  }

  tabItems.forEach(t => t.addEventListener('click', () => switchTab(t.dataset.tab)));
  if (btnGoLogs) btnGoLogs.addEventListener('click', () => switchTab('tab-logs'));

  // ==================== WAKE LOCK (KEEP CPU/SCREEN AWAKE) ====================
  async function requestWakeLock() {
    if (!chkWakeLock.checked) return;
    try {
      if ('wakeLock' in navigator) {
        wakeLock = await navigator.wakeLock.request('screen');
        wakeLock.addEventListener('release', () => {
          wakeLock = null;
        });
      }
    } catch (err) {
      console.warn('WakeLock not available:', err);
    }
  }

  function releaseWakeLock() {
    if (wakeLock) {
      wakeLock.release().catch(() => {});
      wakeLock = null;
    }
  }

  // ==================== CONFIGURAÇÕES (LOCALSTORAGE) ====================
  const CONFIG_KEY = 'instasorteio_config';

  function loadSavedConfig() {
    const saved = localStorage.getItem(CONFIG_KEY);
    let cfg = {};
    if (saved) {
      try { cfg = JSON.parse(saved); } catch (e) {}
    }

    if (cfg.url_post) postUrlInput.value = cfg.url_post;
    chunkValue.textContent = cfg.usuarios_por_comentario || 3;
    inputDelayMin.value = cfg.delay_min_segundos || 45;
    inputDelayMax.value = cfg.delay_max_segundos || 85;
    inputBatchSize.value = cfg.comentarios_por_lote || 5;
    inputBatchPause.value = cfg.pausa_lote_segundos || 180;
    chkFrases.checked = cfg.adicionar_frase_aleatoria !== false;
    chkEmojis.checked = cfg.adicionar_emoji_aleatorio !== false;
    chkWakeLock.checked = cfg.wake_lock !== false;

    updateSummary();
  }

  function getAppConfig() {
    return {
      url_post: postUrlInput.value.trim(),
      usuarios_por_comentario: parseInt(chunkValue.textContent, 10) || 3,
      delay_min_segundos: parseInt(inputDelayMin.value, 10) || 45,
      delay_max_segundos: parseInt(inputDelayMax.value, 10) || 85,
      comentarios_por_lote: parseInt(inputBatchSize.value, 10) || 5,
      pausa_lote_segundos: parseInt(inputBatchPause.value, 10) || 180,
      adicionar_frase_aleatoria: chkFrases.checked,
      adicionar_emoji_aleatorio: chkEmojis.checked,
      wake_lock: chkWakeLock.checked
    };
  }

  function saveConfig() {
    const cfg = getAppConfig();
    localStorage.setItem(CONFIG_KEY, JSON.stringify(cfg));
    showToast('✅ Configurações salvas com sucesso!');
  }

  btnSaveConfig.addEventListener('click', saveConfig);

  // ==================== USUÁRIOS ====================
  function loadUsers() {
    const raw = window.UserManager.loadRawUsers();
    txtUsersArea.value = raw;
    const clean = window.UserManager.getCleanUsers();
    usersBadge.textContent = `${clean.length} amigos`;
    updateSummary();
  }

  function saveUsers() {
    const raw = txtUsersArea.value;
    window.UserManager.saveRawUsers(raw);
    const clean = window.UserManager.getCleanUsers();
    usersBadge.textContent = `${clean.length} amigos`;
    updateSummary();
    showToast(`✅ Lista salva! ${clean.length} amigos detectados.`);
  }

  btnSaveUsers.addEventListener('click', saveUsers);

  btnClearUsers.addEventListener('click', () => {
    if (confirm('Deseja limpar todo o texto da lista de amigos?')) {
      txtUsersArea.value = '';
      window.UserManager.saveRawUsers('');
      loadUsers();
    }
  });

  // Importar arquivo .txt do celular
  btnBrowseFile.addEventListener('click', () => fileInputUsers.click());
  fileInputUsers.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        txtUsersArea.value = evt.target.result;
        saveUsers();
      };
      reader.readAsText(file);
    }
  });

  function updateSummary() {
    const clean = window.UserManager.getCleanUsers();
    const chunk = parseInt(chunkValue.textContent, 10) || 3;
    if (clean.length > 0) {
      const total = Math.ceil(clean.length / chunk);
      calcSummary.textContent = `${clean.length} amigos = ~${total} comentários`;
    } else {
      calcSummary.textContent = `0 amigos carregados`;
    }
  }

  // ==================== LOGS & CONSOLE ====================
  function appendLog(text, type = "INFO") {
    const time = new Date().toTimeString().split(' ')[0];
    const p = document.createElement('p');
    p.className = `console-line ${type}`;
    p.textContent = `[${time}] ${text}`;

    fullConsole.appendChild(p);
    fullConsole.scrollTop = fullConsole.scrollHeight;

    // Mini console
    miniConsole.appendChild(p.cloneNode(true));
    while (miniConsole.children.length > 5) {
      miniConsole.removeChild(miniConsole.firstChild);
    }
    miniConsole.scrollTop = miniConsole.scrollHeight;
  }

  btnClearLogs.addEventListener('click', () => {
    fullConsole.innerHTML = '';
    miniConsole.innerHTML = '<p class="console-line info">Logs limpos.</p>';
  });

  // ==================== CONTROLES DE INTERFACE ====================
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

  btnDecChunk.addEventListener('click', () => {
    let val = parseInt(chunkValue.textContent, 10);
    if (val > 1) {
      chunkValue.textContent = val - 1;
      updateSummary();
    }
  });

  btnIncChunk.addEventListener('click', () => {
    let val = parseInt(chunkValue.textContent, 10);
    if (val < 10) {
      chunkValue.textContent = val + 1;
      updateSummary();
    }
  });

  btnRefreshInsta.addEventListener('click', () => {
    instaIframe.src = 'https://www.instagram.com/';
    showToast('🔄 Recarregando Instagram...');
  });

  // ==================== INTEGRAÇÃO DO MOTOR ANDROID ====================
  window.InstagramBotEngine.onLog = (text, type) => appendLog(text, type);

  window.InstagramBotEngine.onStatusChange = (msg) => {
    liveStatus.textContent = `Status: ${msg}`;
    if (window.InstagramBotEngine.isRunning) {
      appStatusPill.classList.add('running');
      appStatusText.textContent = 'Rodando';
    } else {
      appStatusPill.classList.remove('running');
      appStatusText.textContent = 'Pronto';
    }
  };

  window.InstagramBotEngine.onProgress = (current, total, posted, errors) => {
    const pct = total > 0 ? Math.round((current / total) * 100) : 0;
    livePercent.textContent = `${pct}%`;
    progressBarFill.style.width = `${pct}%`;

    metricPosted.textContent = posted;
    metricErrors.textContent = errors;
    metricPending.textContent = Math.max(0, total - current);
  };

  btnStartBot.addEventListener('click', async () => {
    const url = postUrlInput.value.trim();
    if (!url || !url.includes('instagram.com/')) {
      showToast('⚠️ Cole o link do post do Instagram primeiro!');
      postUrlInput.focus();
      return;
    }

    const cleanUsers = window.UserManager.getCleanUsers();
    if (cleanUsers.length === 0) {
      showToast('⚠️ Adicione sua lista de amigos na aba "Lista @"!');
      switchTab('tab-users');
      return;
    }

    saveConfig();
    const config = getAppConfig();

    btnStartBot.disabled = true;
    btnStopBot.disabled = false;

    // Ativar WakeLock no Android
    await requestWakeLock();

    // Iniciar navegação no iframe se necessário
    try {
      instaIframe.src = url;
    } catch (e) {}

    await window.InstagramBotEngine.start(config, cleanUsers, instaIframe);

    btnStartBot.disabled = false;
    btnStopBot.disabled = true;
    releaseWakeLock();
  });

  btnStopBot.addEventListener('click', () => {
    if (confirm('Deseja realmente pausar o bot? O progresso foi salvo.')) {
      window.InstagramBotEngine.stop();
      btnStopBot.disabled = true;
      releaseWakeLock();
    }
  });

  // ==================== INICIALIZAÇÃO ====================
  loadSavedConfig();
  loadUsers();
});
