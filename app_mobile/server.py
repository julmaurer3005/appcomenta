"""
Servidor Web Backend para o App Mobile (PWA) de Sorteios do Instagram
Permite controlar o bot pelo celular (Android/iOS) via navegador ou PWA instalado.
"""

import os
import sys
import re
import json
import time
import socket
import random
import threading
from queue import Queue
from datetime import datetime
from colorama import init, Fore, Style
from flask import Flask, request, jsonify, send_from_directory, Response

# Configurar UTF-8 no Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

init(autoreset=True)

# Diretórios base (apontam para a raiz do projeto)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
USERS_FILE = os.path.join(BASE_DIR, "usuarios.txt")
HISTORY_FILE = os.path.join(BASE_DIR, "historico_comentarios.txt")
SESSION_DIR = os.path.join(BASE_DIR, ".sessao_instagram")

app = Flask(__name__, static_folder=STATIC_DIR)

# Estado Global do Bot
class BotManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.is_running = False
        self.stop_requested = False
        self.worker_thread = None
        self.status_message = "Pronto para iniciar"
        self.total_posted = 0
        self.total_errors = 0
        self.total_pending = 0
        self.current_idx = 0
        self.current_comment = ""
        self.logs = []
        self.log_subscribers = []
        self.max_logs = 200

    def add_log(self, text, tag="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = {"timestamp": timestamp, "text": text, "tag": tag}
        with self.lock:
            self.logs.append(entry)
            if len(self.logs) > self.max_logs:
                self.logs.pop(0)
        # Notificar SSE subscribers
        dead_queues = []
        for q in self.log_subscribers:
            try:
                q.put_nowait(entry)
            except Exception:
                dead_queues.append(q)
        for q in dead_queues:
            if q in self.log_subscribers:
                self.log_subscribers.remove(q)

    def get_status(self):
        with self.lock:
            percent = 0.0
            if self.total_pending > 0:
                percent = round((self.current_idx / self.total_pending) * 100, 1)
            elif self.total_posted > 0:
                percent = 100.0

            return {
                "is_running": self.is_running,
                "status_message": self.status_message,
                "posted": self.total_posted,
                "errors": self.total_errors,
                "pending": max(0, self.total_pending - self.current_idx),
                "total": self.total_pending,
                "current_idx": self.current_idx,
                "percent": percent,
                "current_comment": self.current_comment
            }

manager = BotManager()


def load_config():
    default_config = {
        "url_post": "https://www.instagram.com/p/",
        "usuarios_por_comentario": 3,
        "delay_min_segundos": 45,
        "delay_max_segundos": 85,
        "comentarios_por_lote": 5,
        "pausa_lote_segundos": 180,
        "limite_maximo_comentarios": 0,
        "adicionar_frase_aleatoria": True,
        "frases": [
            "Boa sorte!", "Tomara que eu ganhe!", "Sorteia eu!",
            "Dedos cruzados!", "Tô na torcida!", "Já é meu!",
            "Quero muito ganhar!", "Vem sorte!", "Na torcida aqui!",
            "Bora ganhar!", "Agora vai!", "Fé no prêmio!",
            "Se Deus quiser!", "Confiante!", "Essa vitória é nossa!"
        ],
        "adicionar_emoji_aleatorio": True,
        "emojis": ["🍀", "🤞", "✨", "🔥", "🙌", "🎯", "⭐", "🎉"],
        "arquivo_usuarios": "usuarios.txt",
        "modo_visivel": False
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default_config.update(saved)
        except Exception:
            pass
    return default_config


def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        manager.add_log(f"Erro ao salvar config: {e}", "ERROR")
        return False


def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        raw = re.findall(r'@([a-zA-Z0-9._]+)', content)
        if not raw:
            words = re.findall(r'[a-zA-Z0-9._]+', content)
            raw = [w for w in words if len(w) > 2]
        seen = set()
        cleaned = []
        for u in raw:
            h = f"@{u.strip().lower()}"
            if h not in seen:
                seen.add(h)
                cleaned.append(h)
        return cleaned
    except Exception as e:
        manager.add_log(f"Erro ao ler usuários: {e}", "ERROR")
        return []


def chunk_list(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return set()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        posted = set()
        for line in lines:
            if " - Comentário: " in line:
                posted.add(line.split(" - Comentário: ")[1].strip())
            else:
                posted.add(line.strip())
        return posted
    except Exception:
        return set()


def record_history(comment_text):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] - Comentário: {comment_text}\n")
    except Exception:
        pass


def run_bot_worker(config):
    manager.add_log("🚀 Iniciando motor de automação Playwright...", "INFO")
    manager.status_message = "Carregando usuários e navegador..."

    users = load_users()
    if not users:
        manager.add_log("❌ Nenhum usuário válido encontrado no arquivo 'usuarios.txt'!", "ERROR")
        manager.status_message = "Erro: Sem usuários"
        manager.is_running = False
        return

    chunk_size = max(1, int(config.get("usuarios_por_comentario", 3)))
    all_chunks = chunk_list(users, chunk_size)
    history = load_history()

    pending_chunks = []
    for c in all_chunks:
        sample = " ".join(c)
        # Se algum comentário similar já foi feito, pula
        already_done = any(sample in h for h in history)
        if not already_done:
            pending_chunks.append(c)

    if not pending_chunks:
        manager.add_log("🎉 Todos os usuários da lista já foram comentados!", "SUCCESS")
        manager.status_message = "Concluído: Todos já comentados"
        manager.is_running = False
        return

    manager.total_pending = len(pending_chunks)
    manager.current_idx = 0
    manager.total_posted = 0
    manager.total_errors = 0
    manager.add_log(f"📋 {len(users)} usuários carregados em {len(pending_chunks)} comentários pendentes.", "INFO")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        manager.add_log("❌ Playwright não instalado. Execute: pip install playwright && playwright install", "ERROR")
        manager.status_message = "Erro: Playwright ausente"
        manager.is_running = False
        return

    os.makedirs(SESSION_DIR, exist_ok=True)
    headless_mode = not bool(config.get("modo_visivel", False))

    with sync_playwright() as p:
        try:
            manager.add_log(f"🌐 Abrindo navegador Chromium ({'em segundo plano' if headless_mode else 'visível'})...", "INFO")
            context = p.chromium.launch_persistent_context(
                SESSION_DIR,
                headless=headless_mode,
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="pt-BR"
            )
            page = context.pages[0] if context.pages else context.new_page()

            url_post = config.get("url_post", "").strip()
            if not url_post or "instagram.com" not in url_post:
                manager.add_log("❌ URL do post inválida!", "ERROR")
                manager.status_message = "Erro: URL inválida"
                context.close()
                manager.is_running = False
                return

            manager.add_log(f"🎯 Acessando post: {url_post}", "INFO")
            manager.status_message = "Acessando post do sorteio..."
            page.goto(url_post, wait_until="domcontentloaded", timeout=45000)
            time.sleep(3.5)

            # Fechar popups
            for btn_txt in ["Agora não", "Not Now", "Recusar", "Decline", "Aceitar todos"]:
                try:
                    btn = page.locator(f"button:has-text('{btn_txt}')").first
                    if btn.is_visible(timeout=1000):
                        btn.click()
                        time.sleep(0.8)
                except Exception:
                    pass

            frases = config.get("frases", ["Boa sorte!", "Sorteia eu!", "Dedos cruzados!"])
            emojis = config.get("emojis", ["🍀", "🤞", "✨", "🔥"])
            use_frase = config.get("adicionar_frase_aleatoria", True)
            use_emoji = config.get("adicionar_emoji_aleatorio", True)
            batch_size = int(config.get("comentarios_por_lote", 5))
            batch_pause = int(config.get("pausa_lote_segundos", 180))
            delay_min = int(config.get("delay_min_segundos", 45))
            delay_max = int(config.get("delay_max_segundos", 85))

            for idx, chunk in enumerate(pending_chunks, 1):
                if manager.stop_requested:
                    manager.add_log("🛑 Execução pausada a pedido do usuário.", "WARN")
                    manager.status_message = "Pausado pelo usuário"
                    break

                manager.current_idx = idx

                parts = list(chunk)
                if use_frase and frases:
                    parts.append(random.choice(frases))
                if use_emoji and emojis:
                    parts.append(random.choice(emojis))
                comment_text = " ".join(parts)
                manager.current_comment = comment_text

                manager.status_message = f"Digitando comentário {idx}/{len(pending_chunks)}..."
                manager.add_log(f"[{idx}/{len(pending_chunks)}] Digitando: {comment_text}", "INFO")

                # Localizar campo de comentário
                comment_box = None
                selectors = [
                    "textarea[aria-label*='comentário']",
                    "textarea[aria-label*='comment']",
                    "textarea[placeholder*='comentário']",
                    "form textarea",
                    "div[role='textbox']"
                ]
                for sel in selectors:
                    try:
                        loc = page.locator(sel).first
                        if loc.is_visible(timeout=2000):
                            comment_box = sel
                            break
                    except Exception:
                        pass

                if not comment_box:
                    try:
                        icon = page.locator("svg[aria-label='Comentar'], svg[aria-label='Comment']").first
                        if icon.is_visible(timeout=2000):
                            icon.click()
                            time.sleep(1.5)
                            for sel in selectors:
                                loc = page.locator(sel).first
                                if loc.is_visible(timeout=1500):
                                    comment_box = sel
                                    break
                    except Exception:
                        pass

                if not comment_box:
                    manager.add_log("❌ Campo de comentário não encontrado. Rolando...", "ERROR")
                    manager.total_errors += 1
                    page.mouse.wheel(0, 300)
                    time.sleep(2)
                    continue

                # Digitação humanizada e envio
                try:
                    box = page.locator(comment_box).first
                    box.click()
                    time.sleep(0.4)

                    for ch in comment_text:
                        page.keyboard.type(ch)
                        time.sleep(random.uniform(0.15, 0.30))
                        if ch == " ":
                            time.sleep(random.uniform(0.4, 0.8))

                    page.keyboard.type(" ")
                    time.sleep(0.8)
                    page.keyboard.press("Escape")
                    time.sleep(0.4)

                    # Disparar eventos no React
                    try:
                        page.evaluate("""(selector) => {
                            const el = document.querySelector(selector);
                            if (el) {
                                el.dispatchEvent(new Event('input', { bubbles: true }));
                                el.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        }""", comment_box)
                    except Exception:
                        pass

                    time.sleep(0.6)

                    # Botão Publicar
                    submitted = False
                    post_selectors = [
                        "form div[role='button']:has-text('Publicar')",
                        "form div[role='button']:has-text('Post')",
                        "form button:has-text('Publicar')",
                        "form button:has-text('Post')",
                        "form button[type='submit']",
                        "div[role='button']:has-text('Publicar')"
                    ]
                    for btn_sel in post_selectors:
                        try:
                            btn = page.locator(btn_sel).first
                            if btn.is_visible(timeout=1000):
                                btn.click(force=True, timeout=2000)
                                submitted = True
                                break
                        except Exception:
                            pass

                    if not submitted:
                        page.keyboard.press("Enter")

                    # Aguardar e validar envio
                    time.sleep(3.5)

                    # Checar bloqueios
                    block_detected = False
                    for block_text in ["Tente novamente mais tarde", "Ação bloqueada", "Limitamos determinados", "Try Again Later", "Action Blocked"]:
                        try:
                            if page.locator(f"text={block_text}").first.is_visible(timeout=500):
                                block_detected = True
                                break
                        except Exception:
                            pass

                    if block_detected:
                        manager.add_log("⚠️ ALERTA: Bloqueio temporário detectado no Instagram! Pausando o robô.", "ERROR")
                        manager.status_message = "Alerta: Bloqueio do Instagram"
                        break

                    manager.total_posted += 1
                    record_history(comment_text)
                    manager.add_log(f"✅ Comentário #{manager.total_posted} postado com sucesso!", "SUCCESS")

                except Exception as e:
                    manager.total_errors += 1
                    manager.add_log(f"❌ Erro ao enviar comentário: {e}", "ERROR")

                # Checar se concluiu
                if idx >= len(pending_chunks):
                    manager.add_log("🏆 Parabéns! Todos os comentários foram concluídos com sucesso!", "SUCCESS")
                    manager.status_message = "Concluído com Sucesso!"
                    break

                # Lote ou intervalo normal
                if batch_size > 0 and idx % batch_size == 0:
                    manager.add_log(f"☕ Lote de {batch_size} comentários atingido. Descansando por {batch_pause}s...", "WARN")
                    for s in range(batch_pause, 0, -1):
                        if manager.stop_requested:
                            break
                        manager.status_message = f"☕ Descanso do Lote: {s}s restantes"
                        time.sleep(1)
                else:
                    delay = random.randint(min(delay_min, delay_max), max(delay_min, delay_max))
                    for s in range(delay, 0, -1):
                        if manager.stop_requested:
                            break
                        manager.status_message = f"⏳ Aguardando próximo: {s}s"
                        time.sleep(1)

            context.close()
        except Exception as e:
            manager.add_log(f"❌ Erro geral no navegador: {e}", "ERROR")
            manager.status_message = f"Erro: {e}"
        finally:
            manager.is_running = False
            manager.stop_requested = False
            if manager.status_message.startswith("Digitando") or manager.status_message.startswith("Aguardando"):
                manager.status_message = "Pronto"
            manager.add_log("⏹️ Sessão finalizada.", "INFO")


# ==================== ROTAS DA API ====================

@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.route("/manifest.json")
def manifest():
    return send_from_directory(STATIC_DIR, "manifest.json")

@app.route("/sw.js")
def service_worker():
    return send_from_directory(STATIC_DIR, "sw.js")

@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify(manager.get_status())

@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        data = request.json or {}
        current = load_config()
        current.update(data)
        if save_config(current):
            return jsonify({"success": True, "config": current})
        return jsonify({"success": False, "error": "Falha ao salvar"}), 500
    return jsonify(load_config())

@app.route("/api/users", methods=["GET", "POST"])
def api_users():
    if request.method == "POST":
        data = request.json or {}
        raw_text = data.get("content", "")
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                f.write(raw_text)
            users = load_users()
            return jsonify({"success": True, "total_users": len(users)})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    content = ""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            pass
    users = load_users()
    return jsonify({"content": content, "users": users, "total": len(users)})

@app.route("/api/start", methods=["POST"])
def api_start():
    if manager.is_running:
        return jsonify({"success": False, "message": "O bot já está em execução!"}), 400

    # Atualizar config se enviada
    req_config = request.json or {}
    config = load_config()
    if req_config:
        config.update(req_config)
        save_config(config)

    manager.is_running = True
    manager.stop_requested = False
    manager.worker_thread = threading.Thread(target=run_bot_worker, args=(config,), daemon=True)
    manager.worker_thread.start()

    return jsonify({"success": True, "message": "Bot iniciado com sucesso!"})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    if not manager.is_running:
        return jsonify({"success": False, "message": "O bot não está em execução."}), 400

    manager.stop_requested = True
    manager.status_message = "Parando..."
    manager.add_log("⏹️ Solicitação de parada recebida...", "WARN")
    return jsonify({"success": True, "message": "Parada solicitada."})

@app.route("/api/logs", methods=["GET"])
def api_logs():
    with manager.lock:
        return jsonify(manager.logs)

@app.route("/api/logs/stream")
def api_logs_stream():
    def event_stream():
        q = Queue()
        manager.log_subscribers.append(q)
        try:
            # Envia os últimos logs primeiro
            with manager.lock:
                for entry in manager.logs[-30:]:
                    yield f"data: {json.dumps(entry)}\n\n"
            while True:
                entry = q.get()
                yield f"data: {json.dumps(entry)}\n\n"
        except GeneratorExit:
            if q in manager.log_subscribers:
                manager.log_subscribers.remove(q)

    return Response(event_stream(), mimetype="text/event-stream")


# ==================== UTILITÁRIOS DE REDE E QR CODE ====================

def get_local_ip():
    """Descobre o IP da máquina na rede local (Wi-Fi/Ethernet)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def print_startup_banner(port):
    local_ip = get_local_ip()
    local_url = f"http://127.0.0.1:{port}"
    mobile_url = f"http://{local_ip}:{port}"

    print(Fore.CYAN + Style.BRIGHT + "\n" + "=" * 62)
    print(Fore.CYAN + Style.BRIGHT + "   📱 INSTAGRAM BOT - APP MOBILE & WEB SERVER (PWA) 📱")
    print(Fore.CYAN + Style.BRIGHT + "=" * 62)
    print(Fore.WHITE + "  Acesse no seu ")
    print(Fore.GREEN + Style.BRIGHT + f"  👉 {mobile_url}")
    print(Fore.WHITE + "\n  No seu computador:")
    print(Fore.BLUE + f"  👉 {local_url}")
    print(Fore.CYAN + "-" * 62)

    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(mobile_url)
        qr.make(fit=True)
        print(Fore.YELLOW + "  📷 Escaneie o QR Code abaixo com a câmera do celular:")
        qr.print_ascii(invert=True)
    except Exception:
        pass

    print(Fore.YELLOW + "  💡 Dica: Conecte o celular no mesmo Wi-Fi do computador.")
    print(Fore.CYAN + "=" * 62 + "\n")


if __name__ == "__main__":
    PORT = 5000
    print_startup_banner(PORT)
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
