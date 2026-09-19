/**
 * Gerenciador de Usuários e Histórico para o App Android
 */

class UserManager {
  constructor() {
    this.storageKey = 'instasorteio_users_raw';
    this.historyKey = 'instasorteio_history_comments';
  }

  // Carrega o texto bruto dos usuários salvo localmente no celular
  loadRawUsers() {
    return localStorage.getItem(this.storageKey) || '';
  }

  // Salva o texto bruto dos usuários no armazenamento interno do Android
  saveRawUsers(text) {
    localStorage.setItem(this.storageKey, text);
  }

  // Processa e limpa a lista de usuários com deduplicação
  getCleanUsers() {
    const raw = this.loadRawUsers();
    if (!raw.trim()) return [];

    // Extrai palavras iniciadas com @
    let handles = raw.match(/@([a-zA-Z0-9._]+)/g);
    
    // Se não tiver @, pega palavras isoladas
    if (!handles) {
      const words = raw.match(/[a-zA-Z0-9._]+/g) || [];
      handles = words.filter(w => w.length > 2).map(w => `@${w}`);
    }

    const seen = new Set();
    const cleanList = [];

    for (let h of handles) {
      const formatted = h.toLowerCase().trim();
      if (!seen.has(formatted)) {
        seen.add(formatted);
        cleanList.push(formatted);
      }
    }

    return cleanList;
  }

  // Divide a lista em grupos (chunks) de tamanho N
  chunkUsers(usersList, chunkSize) {
    const chunks = [];
    for (let i = 0; i < usersList.length; i += chunkSize) {
      chunks.append = chunks.push(usersList.slice(i, i + chunkSize));
    }
    return chunks;
  }

  // Carrega histórico de comentários já postados
  loadHistory() {
    try {
      const historyStr = localStorage.getItem(this.historyKey);
      return historyStr ? JSON.parse(historyStr) : [];
    } catch (e) {
      return [];
    }
  }

  // Registra um novo comentário postado com data e hora
  recordHistory(commentText) {
    const history = this.loadHistory();
    const entry = {
      timestamp: new Date().toISOString(),
      text: commentText
    };
    history.push(entry);
    localStorage.setItem(this.historyKey, JSON.stringify(history));
  }

  // Limpa o histórico de comentários
  clearHistory() {
    localStorage.removeItem(this.historyKey);
  }
}

window.UserManager = new UserManager();
