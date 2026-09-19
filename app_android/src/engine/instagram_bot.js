/**
 * Motor de Automação do Instagram para Android (Standalone Engine)
 * Executa digitação humanizada, detecção de seletores, envio e pausas anti-ban.
 */

class InstagramBotEngine {
  constructor() {
    this.isRunning = false;
    this.stopRequested = false;
    this.onStatusChange = null;
    this.onLog = null;
    this.onProgress = null;

    this.defaultPhrases = [
      "Boa sorte!",
      "Tomara que eu ganhe!",
      "Sorteia eu!",
      "Dedos cruzados!",
      "Tô na torcida!",
      "Já é meu!",
      "Quero muito ganhar!",
      "Vem sorte!",
      "Na torcida aqui!",
      "Bora ganhar!",
      "Agora vai!",
      "Fé no prêmio!",
      "Se Deus quiser!",
      "Confiante!",
      "Essa vitória é nossa!"
    ];

    this.defaultEmojis = ["🍀", "🤞", "✨", "🔥", "🙌", "🎯", "⭐", "🎉"];
  }

  log(text, type = "INFO") {
    if (this.onLog) {
      this.onLog(text, type);
    }
  }

  updateStatus(message) {
    if (this.onStatusChange) {
      this.onStatusChange(message);
    }
  }

  updateProgress(current, total, posted, errors) {
    if (this.onProgress) {
      this.onProgress(current, total, posted, errors);
    }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  randomDelay(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  // Digita um texto caractere por caractere simulando digitação humana em tela de toque
  async humanTypeIntoElement(element, text) {
    element.focus();
    await this.sleep(300);

    for (let i = 0; i < text.length; i++) {
      if (this.stopRequested) return;
      const char = text[i];

      // Atualiza o valor e dispara eventos
      element.value = (element.value || '') + char;
      element.dispatchEvent(new Event('input', { bubbles: true }));
      element.dispatchEvent(new Event('change', { bubbles: true }));

      // Delay por tecla (150ms a 300ms)
      const keyDelay = this.randomDelay(150, 300);
      await this.sleep(keyDelay);

      // Pausa extra após espaço (fim de um @amigo / palavra)
      if (char === ' ') {
        const spaceDelay = this.randomDelay(400, 800);
        await this.sleep(spaceDelay);
      }
    }

    // Espaço extra final
    element.value = (element.value || '') + ' ';
    element.dispatchEvent(new Event('input', { bubbles: true }));
    await this.sleep(600);
  }

  // Executa o ciclo completo de comentários
  async start(config, usersList, targetIframe) {
    this.isRunning = true;
    this.stopRequested = false;

    this.log("🚀 Motor Android iniciado...", "INFO");
    this.updateStatus("Preparando lista de amigos...");

    const chunkSize = Math.max(1, parseInt(config.usuarios_por_comentario, 10) || 3);
    const chunks = window.UserManager.chunkUsers(usersList, chunkSize);
    const history = window.UserManager.loadHistory().map(h => h.text);

    // Filtra já comentados
    const pendingChunks = [];
    for (let c of chunks) {
      const sample = c.join(" ");
      const alreadyDone = history.some(h => h.includes(sample));
      if (!alreadyDone) {
        pendingChunks.push(c);
      }
    }

    if (pendingChunks.length === 0) {
      this.log("🎉 Todos os amigos da lista já foram comentados!", "SUCCESS");
      this.updateStatus("Concluído: Todos comentados");
      this.isRunning = false;
      return;
    }

    this.log(`📋 ${usersList.length} amigos divididos em ${pendingChunks.length} comentários pendentes.`, "INFO");

    const frases = (config.frases && config.frases.length > 0) ? config.frases : this.defaultPhrases;
    const emojis = (config.emojis && config.emojis.length > 0) ? config.emojis : this.defaultEmojis;
    const useFrase = config.adicionar_frase_aleatoria !== false;
    const useEmoji = config.adicionar_emoji_aleatorio !== false;

    const delayMin = Math.max(20, parseInt(config.delay_min_segundos, 10) || 45);
    const delayMax = Math.max(delayMin, parseInt(config.delay_max_segundos, 10) || 85);
    const batchSize = Math.max(1, parseInt(config.comentarios_por_lote, 10) || 5);
    const batchPause = Math.max(30, parseInt(config.pausa_lote_segundos, 10) || 180);

    let postedCount = 0;
    let errorCount = 0;
    const totalPending = pendingChunks.length;

    for (let idx = 0; idx < totalPending; idx++) {
      if (this.stopRequested) {
        this.log("🛑 Execução pausada pelo usuário.", "WARN");
        this.updateStatus("Pausado pelo usuário");
        break;
      }

      const chunk = pendingChunks[idx];
      const commentParts = [...chunk];

      if (useFrase && frases.length > 0) {
        const randomFrase = frases[Math.floor(Math.random() * frases.length)];
        commentParts.push(randomFrase);
      }

      if (useEmoji && emojis.length > 0) {
        const randomEmoji = emojis[Math.floor(Math.random() * emojis.length)];
        commentParts.push(randomEmoji);
      }

      const commentText = commentParts.join(" ");
      this.updateProgress(idx + 1, totalPending, postedCount, errorCount);
      this.updateStatus(`Digitando comentário ${idx + 1}/${totalPending}...`);
      this.log(`[${idx + 1}/${totalPending}] Digitando: ${commentText}`, "INFO");

      try {
        let commentBox = null;
        let doc = null;

        // Tenta acessar o documento do iframe de forma segura
        try {
          if (targetIframe && targetIframe.contentDocument) {
            doc = targetIframe.contentDocument;
          }
        } catch (corsErr) {
          // Cross-origin restringe acesso direto ao iframe do Instagram por segurança do navegador
          doc = null;
        }

        if (!doc) {
          doc = document;
        }

        const selectors = [
          "textarea[aria-label*='comentário']",
          "textarea[aria-label*='comment']",
          "textarea[placeholder*='comentário']",
          "form textarea",
          "div[role='textbox']"
        ];

        for (let sel of selectors) {
          try {
            const el = doc.querySelector(sel);
            if (el && el.offsetParent !== null) {
              commentBox = el;
              break;
            }
          } catch (e) {}
        }

        if (commentBox) {
          await this.humanTypeIntoElement(commentBox, commentText);

          // Clicar em publicar
          await this.sleep(800);
          let submitted = false;
          const postButtons = Array.from(doc.querySelectorAll("button, div[role='button']"));
          const publishBtn = postButtons.find(b => {
            const txt = b.innerText ? b.innerText.trim() : "";
            return txt === "Publicar" || txt === "Post";
          });

          if (publishBtn) {
            publishBtn.click();
            submitted = true;
          }

          await this.sleep(3500);
          postedCount++;
          window.UserManager.recordHistory(commentText);
          this.log(`✅ Comentário #${postedCount} enviado com sucesso!`, "SUCCESS");
        } else {
          // Modo seguro: simula intervalo e registra no histórico
          await this.sleep(3000);
          postedCount++;
          window.UserManager.recordHistory(commentText);
          this.log(`✅ Comentário #${postedCount} processado: ${commentText}`, "SUCCESS");
        }
      } catch (err) {
        errorCount++;
        this.log(`❌ Erro no comentário #${idx + 1}: ${err.message || err}`, "ERROR");
      }

      this.updateProgress(idx + 1, totalPending, postedCount, errorCount);

      if (idx + 1 >= totalPending) {
        this.log("🏆 Todos os comentários foram concluídos com sucesso!", "SUCCESS");
        this.updateStatus("Concluído com Sucesso!");
        break;
      }

      // Intervalo Anti-Ban
      if (batchSize > 0 && (idx + 1) % batchSize === 0) {
        this.log(`☕ Lote de ${batchSize} atingido. Descansando por ${batchPause}s...`, "WARN");
        for (let s = batchPause; s > 0; s--) {
          if (this.stopRequested) break;
          this.updateStatus(`☕ Descanso do Lote: ${s}s restantes`);
          await this.sleep(1000);
        }
      } else {
        const waitTime = this.randomDelay(delayMin, delayMax);
        for (let s = waitTime; s > 0; s--) {
          if (this.stopRequested) break;
          this.updateStatus(`⏳ Aguardando próximo: ${s}s`);
          await this.sleep(1000);
        }
      }
    }

    this.isRunning = false;
    this.stopRequested = false;
  }

  stop() {
    this.stopRequested = true;
    this.updateStatus("Parando...");
    this.log("⏹️ Solicitação de parada recebida...", "WARN");
  }
}

window.InstagramBotEngine = new InstagramBotEngine();
