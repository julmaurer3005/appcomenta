"""
Bot de Comentários no Instagram para Sorteios
Desenvolvido com Playwright e suporte a anti-bloqueio (anti-ban).
"""

import os
import sys
import re
import json
import time
import random
from datetime import datetime
from colorama import init, Fore, Style

# Configurar stdout para UTF-8 no Windows para evitar erros de caractere
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Inicializar colorama para cores no terminal Windows
init(autoreset=True)

CONFIG_FILE = "config.json"
USERS_FILE = "usuarios.txt"
HISTORY_FILE = "historico_comentarios.txt"
SESSION_DIR = ".sessao_instagram"

DEFAULT_CONFIG = {
    "url_post": "https://www.instagram.com/p/SEU_POST_AQUI/",
    "usuarios_por_comentario": 2,
    "delay_min_segundos": 45,
    "delay_max_segundos": 85,
    "comentarios_por_lote": 5,
    "pausa_lote_segundos": 180,
    "limite_maximo_comentarios": 0,
    "adicionar_frase_aleatoria": True,
    "frases": [
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
    ],
    "adicionar_emoji_aleatorio": True,
    "emojis": ["🍀", "🤞", "✨", "🔥", "🙌", "🎯", "⭐", "🎉"]
}


def print_banner():
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)
    print(Fore.CYAN + Style.BRIGHT + "   🤖 BOT DE COMENTÁRIOS NO INSTAGRAM (SORTEIOS) 🤖")
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)
    print(Fore.YELLOW + "  • Proteção anti-bloqueio ativada")
    print(Fore.YELLOW + "  • Sessão persistente (login salvo)")
    print(Fore.YELLOW + "  • Agrupamento flexível de usuários (1, 2, 3...)")
    print(Fore.CYAN + Style.BRIGHT + "=" * 60 + "\n")


def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Preenche chaves faltantes caso o arquivo esteja incompleto
            for key, val in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = val
            return config
    except Exception as e:
        print(Fore.RED + f"Erro ao ler {CONFIG_FILE}: {e}. Usando padrões.")
        return DEFAULT_CONFIG.copy()


def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(Fore.RED + f"Erro ao salvar {CONFIG_FILE}: {e}")


def load_users(filepath=USERS_FILE):
    if not os.path.exists(filepath):
        print(Fore.RED + f"❌ Arquivo '{filepath}' não foi encontrado na pasta raiz!")
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Encontra todos os nomes de usuário (@nome ou apenas palavras isoladas que parecem usuários)
    raw_handles = re.findall(r'@([a-zA-Z0-9._]+)', content)

    # Se o arquivo não tiver @, tentar extrair palavras simples separadas por espaços/linhas
    if not raw_handles:
        words = re.findall(r'[a-zA-Z0-9._]+', content)
        raw_handles = [w for w in words if len(w) > 2]

    # Limpeza e deduplicação mantendo a ordem original
    seen = set()
    cleaned_users = []
    for user in raw_handles:
        handle = f"@{user.strip().lower()}"
        if handle not in seen:
            seen.add(handle)
            cleaned_users.append(handle)

    return cleaned_users


def chunk_users(users_list, chunk_size):
    """Divide a lista de usuários em grupos de tamanho chunk_size (1, 2, 3, etc.)."""
    chunks = []
    for i in range(0, len(users_list), chunk_size):
        chunks.append(users_list[i:i + chunk_size])
    return chunks


def load_history():
    """Carrega o histórico de comentários já postados para não repetir."""
    if not os.path.exists(HISTORY_FILE):
        return set()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        posted = set()
        for line in lines:
            if " - Comentário: " in line:
                comment_text = line.split(" - Comentário: ")[1].strip()
                posted.add(comment_text)
            else:
                posted.add(line.strip())
        return posted
    except Exception:
        return set()


def record_history(comment_text):
    """Registra o comentário com data e hora no arquivo de histórico."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] - Comentário: {comment_text}\n")


def render_progress_bar(current, total, success_count=0, error_count=0, width=22):
    """Gera uma barra de progresso visual colorida e compatível."""
    if total == 0:
        percent = 100.0
        filled_len = width
    else:
        percent = (current / total) * 100.0
        filled_len = int(width * current // total)
    
    bar = "=" * filled_len + "-" * (width - filled_len)
    return (
        f"{Fore.CYAN}[{Fore.GREEN}{bar}{Fore.CYAN}] "
        f"{Fore.YELLOW}{percent:5.1f}% "
        f"{Fore.WHITE}({current}/{total}) "
        f"| {Fore.GREEN}✓ {success_count} "
        f"{Fore.RED}✗ {error_count}{Fore.WHITE}"
    )


def countdown(seconds, message="Aguardando", current=0, total=0, success=0, errors=0):
    """Exibe contagem regressiva animada com a barra de progresso integrada."""
    for remaining in range(seconds, 0, -1):
        mins, secs = divmod(remaining, 60)
        time_str = f"{mins:02d}:{secs:02d}" if mins > 0 else f"{secs}s"
        bar_str = render_progress_bar(current, total, success, errors)
        sys.stdout.write(f"\r{bar_str} | {Fore.YELLOW}⏳ {message}: {Fore.CYAN}{time_str}{Style.RESET_ALL}   ")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " " * 85 + "\r")
    sys.stdout.flush()


def human_type(page, selector, text):
    """Digita o texto caractere por caractere com intervalos aleatórios humanizados."""
    page.focus(selector)
    for char in text:
        page.keyboard.type(char)
        time.sleep(random.uniform(0.04, 0.12))


def check_for_blocks(page):
    """Verifica se apareceu algum popup ou mensagem de bloqueio de ação do Instagram."""
    block_patterns = [
        "Tente novamente mais tarde",
        "Ação bloqueada",
        "Limitamos determinados",
        "Try Again Later",
        "Action Blocked",
        "Restringimos determinadas atividades",
        "Sua conta foi temporariamente bloqueada"
    ]
    for pattern in block_patterns:
        try:
            element = page.locator(f"text={pattern}").first
            if element.is_visible(timeout=1000):
                return pattern
        except Exception:
            pass
    return None


def dismiss_common_popups(page):
    """Fecha popups comuns do Instagram como 'Salvar informações de login' e 'Ativar notificações'."""
    popup_button_texts = [
        "Agora não", "Not Now", "Cancelar", "Cancel", 
        "Recusar", "Decline", "Depois", "Later"
    ]
    for text in popup_button_texts:
        try:
            btn = page.locator(f"button:has-text('{text}')").first
            if btn.is_visible(timeout=1000):
                btn.click()
                time.sleep(1)
        except Exception:
            pass


def send_comment_to_instagram(page, comment_box_selector, comment_text):
    """
    Digita e envia o comentário no Instagram, utilizando múltiplos métodos de confirmação
    (Botão Publicar, JavaScript direto e tecla Enter) e valida se a caixa de texto foi esvaziada.
    Retorna (sucesso: bool, mensagem_erro: str ou None).
    """
    try:
        box = page.locator(comment_box_selector).first
        if not box.is_visible(timeout=3000):
            return False, "Campo de comentário não está visível"

        # 1. Clicar no campo
        box.click()
        time.sleep(0.4)

        # 2. Digitação humanizada do comentário
        for char in comment_text:
            page.keyboard.type(char)
            time.sleep(random.uniform(0.15, 0.30))
            # Pausa adicional ao terminar de digitar cada @usuario / palavra (~0.5s)
            if char == " ":
                time.sleep(random.uniform(0.4, 0.8))

        # Importante: Digitar um espaço no final para desativar o dropdown de busca de @usuário
        page.keyboard.type(" ")
        time.sleep(0.8)

        # Fechar qualquer popup de sugestão de @menção sem perder o foco
        page.keyboard.press("Escape")
        time.sleep(0.4)

        # 3. Disparar evento de input/change para garantir que o React ative o botão Publicar
        try:
            page.evaluate("""(selector) => {
                const el = document.querySelector(selector);
                if (el) {
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }""", comment_box_selector)
        except Exception:
            pass

        time.sleep(0.6)

        # 4. Estratégia 1: Clicar no botão 'Publicar' / 'Post'
        post_button_selectors = [
            "form div[role='button']:has-text('Publicar')",
            "form div[role='button']:has-text('Post')",
            "form button:has-text('Publicar')",
            "form button:has-text('Post')",
            "form button[type='submit']",
            "div[role='button']:has-text('Publicar')",
            "div[role='button']:has-text('Post')",
            "button:has-text('Publicar')",
            "button:has-text('Post')"
        ]

        submitted = False
        for btn_sel in post_button_selectors:
            try:
                btn = page.locator(btn_sel).first
                if btn.is_visible(timeout=1000):
                    btn.click(force=True, timeout=2000)
                    submitted = True
                    break
            except Exception:
                pass

        # Estratégia 2: JavaScript click em qualquer botão do formulário
        if not submitted:
            try:
                clicked = page.evaluate("""() => {
                    const forms = document.querySelectorAll('form');
                    for (const form of forms) {
                        const buttons = form.querySelectorAll('div[role="button"], button, div[tabindex="0"]');
                        for (const b of buttons) {
                            const txt = (b.innerText || b.textContent || '').trim().toLowerCase();
                            if (txt === 'publicar' || txt === 'post' || txt === 'postar') {
                                b.click();
                                return true;
                            }
                        }
                    }
                    const allButtons = document.querySelectorAll('div[role="button"], button');
                    for (const b of allButtons) {
                        const txt = (b.innerText || b.textContent || '').trim().toLowerCase();
                        if (txt === 'publicar' || txt === 'post' || txt === 'postar') {
                            b.click();
                            return true;
                        }
                    }
                    return false;
                }""")
                if clicked:
                    submitted = True
            except Exception:
                pass

        # Estratégia 3: Pressionar Enter no campo de comentário
        try:
            box.focus()
            page.keyboard.press("Enter")
            time.sleep(0.5)
            page.keyboard.press("Control+Enter")
        except Exception:
            pass

        # 5. Aguardar processamento e verificar bloqueio
        time.sleep(3.5)

        block_msg = check_for_blocks(page)
        if block_msg:
            return False, f"Bloqueio detectado: {block_msg}"

        # 6. Validação: Checar se a caixa de texto foi limpa (confirmação real de envio)
        try:
            val = box.input_value(timeout=1500).strip()
        except Exception:
            try:
                val = box.inner_text(timeout=1500).strip()
            except Exception:
                val = ""

        # Se ainda sobrou texto, tentar mais uma vez pressionar Enter com foco direto
        if val:
            try:
                box.focus()
                page.keyboard.press("Enter")
                time.sleep(2.5)
                val = box.input_value(timeout=1000).strip()
            except Exception:
                pass

        # Se a caixa foi esvaziada, o comentário foi enviado com sucesso
        if not val:
            return True, None
        else:
            try:
                page.screenshot(path="erro_envio_comentario.png")
            except Exception:
                pass
            return False, "O texto permaneceu no campo de comentário após a tentativa de envio."

    except Exception as e:
        return False, str(e)


def run_bot():
    import argparse
    parser = argparse.ArgumentParser(description="Bot de Comentários no Instagram para Sorteios")
    parser.add_argument("--post", type=str, help="URL do post do sorteio no Instagram")
    parser.add_argument("--users", type=int, help="Quantidade de usuários por comentário (1, 2, 3...)")
    parser.add_argument("--max", type=int, help="Limite máximo de comentários nesta execução")
    parser.add_argument("--delay-min", type=int, help="Delay mínimo em segundos entre comentários")
    parser.add_argument("--delay-max", type=int, help="Delay máximo em segundos entre comentários")
    args = parser.parse_args()

    print_banner()
    config = load_config()

    # Sobrescrever config com argumentos de linha de comando se fornecidos
    if args.post:
        config["url_post"] = args.post
    if args.users:
        config["usuarios_por_comentario"] = args.users
    if args.max is not None:
        config["limite_maximo_comentarios"] = args.max
    if args.delay_min:
        config["delay_min_segundos"] = args.delay_min
    if args.delay_max:
        config["delay_max_segundos"] = args.delay_max

    # Solicitar URL se ainda for a padrão e não foi passada via CLI
    if "SEU_POST_AQUI" in config.get("url_post", "") or not config.get("url_post"):
        print(Fore.MAGENTA + "👉 Cole a URL completa do post do sorteio no Instagram:")
        url_input = input(Fore.WHITE + "URL: ").strip()
        if url_input:
            config["url_post"] = url_input
            save_config(config)
        else:
            print(Fore.RED + "❌ Nenhuma URL fornecida. Encerrando.")
            return

    # Perguntar quantidade de amigos por comentário se não passada por argumento
    if not args.users:
        print(Fore.MAGENTA + f"\n👉 Quantos amigos por comentário você deseja marcar neste sorteio?")
        print(Fore.WHITE + f"(Pressione ENTER para manter o valor atual: {Fore.GREEN}{config['usuarios_por_comentario']}{Fore.WHITE}): ", end="")
        user_chunk_input = input().strip()
        if user_chunk_input.isdigit() and int(user_chunk_input) > 0:
            config["usuarios_por_comentario"] = int(user_chunk_input)
            save_config(config)

    chunk_size = config["usuarios_por_comentario"]
    all_users = load_users()

    if not all_users:
        print(Fore.RED + "❌ Nenhum usuário válido encontrado em 'usuarios.txt'.")
        return

    # Gerar os blocos de comentários
    chunks = chunk_users(all_users, chunk_size)
    history = load_history()

    # Filtrar os comentários que já foram postados
    pending_chunks = []
    for c in chunks:
        comment_base = " ".join(c)
        already_done = any(comment_base in h for h in history)
        if not already_done:
            pending_chunks.append(c)

    print(Fore.GREEN + f"\n📊 Resumo da Lista:")
    print(Fore.WHITE + f"  • Total de usuários únicos: {Fore.CYAN}{len(all_users)}")
    print(Fore.WHITE + f"  • Usuários por comentário: {Fore.CYAN}{chunk_size}")
    print(Fore.WHITE + f"  • Total de comentários possíveis: {Fore.CYAN}{len(chunks)}")
    print(Fore.WHITE + f"  • Comentários já feitos anteriormente: {Fore.YELLOW}{len(chunks) - len(pending_chunks)}")
    print(Fore.WHITE + f"  • Comentários pendentes para esta execução: {Fore.GREEN}{len(pending_chunks)}")
    print(Fore.WHITE + f"  • Post alvo: {Fore.CYAN}{config['url_post']}")
    print(Fore.WHITE + f"  • Intervalo seguro: {Fore.CYAN}{config.get('delay_min_segundos', 45)}s a {config.get('delay_max_segundos', 85)}s")
    print("-" * 60)

    if not pending_chunks:
        print(Fore.GREEN + "🎉 Todos os usuários da lista já foram comentados! Nada pendente.")
        return

    # Confirmação antes de abrir navegador
    input(Fore.YELLOW + "\nPressione ENTER para abrir o navegador e iniciar...")

    from playwright.sync_api import sync_playwright

    os.makedirs(SESSION_DIR, exist_ok=True)

    with sync_playwright() as p:
        print(Fore.BLUE + "\n🌐 Iniciando navegador...")
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=os.path.abspath(SESSION_DIR),
            headless=False,
            viewport={"width": 1280, "height": 800},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="pt-BR"
        )

        page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()

        # 1. Verificar Login
        print(Fore.BLUE + "🔍 Acessando Instagram para verificar autenticação...")
        page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        time.sleep(3)

        dismiss_common_popups(page)

        # Checar se precisa de login
        is_logged_in = False
        try:
            nav_selectors = [
                "svg[aria-label='Página inicial']",
                "svg[aria-label='Home']",
                "svg[aria-label='Pesquisa']",
                "svg[aria-label='Search']",
                "svg[aria-label='Direct']",
                "a[href*='/direct/']"
            ]
            for sel in nav_selectors:
                if page.locator(sel).first.is_visible(timeout=3000):
                    is_logged_in = True
                    break
        except Exception:
            pass

        if not is_logged_in:
            print(Fore.YELLOW + "\n" + "=" * 60)
            print(Fore.YELLOW + "🔐 LOGIN NECESSÁRIO:")
            print(Fore.WHITE + "Faça login na sua conta do Instagram na janela do navegador aberta.")
            print(Fore.WHITE + "(Pode colocar usuário, senha e código 2FA normalmente com total segurança).")
            print(Fore.YELLOW + "=" * 60)
            input(Fore.GREEN + "\nDepois que fizer o login e estiver na tela inicial do Instagram, pressione ENTER aqui no terminal para continuar...")

        # 2. Navegar até o Post do Sorteio
        print(Fore.BLUE + f"\n🎯 Acessando o post do sorteio: {config['url_post']}")
        page.goto(config["url_post"], wait_until="domcontentloaded")
        time.sleep(4)

        dismiss_common_popups(page)

        # 3. Execução dos Comentários
        total_posted_session = 0
        total_errors_session = 0
        total_pending = len(pending_chunks)
        max_comments = config.get("limite_maximo_comentarios", 0)

        for idx, chunk in enumerate(pending_chunks, 1):
            if max_comments > 0 and total_posted_session >= max_comments:
                print(Fore.YELLOW + f"\n🛑 Limite configurado de {max_comments} comentários atingido para esta sessão!")
                break

            # Montagem do comentário
            parts = list(chunk)
            if config.get("adicionar_frase_aleatoria", True) and config.get("frases"):
                parts.append(random.choice(config["frases"]))
            if config.get("adicionar_emoji_aleatorio", True) and config.get("emojis"):
                parts.append(random.choice(config["emojis"]))
            comment_text = " ".join(parts)

            print("\n" + render_progress_bar(idx - 1, total_pending, total_posted_session, total_errors_session))
            print(Fore.CYAN + f"[{idx}/{total_pending}] ✍️ Enviando comentário: {Fore.WHITE}{comment_text}")

            # Localizar campo de comentário
            comment_box = None
            comment_selectors = [
                "textarea[aria-label*='comentário']",
                "textarea[aria-label*='comment']",
                "textarea[placeholder*='comentário']",
                "textarea[placeholder*='comment']",
                "form textarea",
                "div[role='textbox']",
                "div[contenteditable='true']"
            ]

            for selector in comment_selectors:
                try:
                    loc = page.locator(selector).first
                    if loc.is_visible(timeout=2000):
                        comment_box = selector
                        break
                except Exception:
                    pass

            # Se não encontrou de imediato, tenta clicar no ícone de balão de comentário
            if not comment_box:
                try:
                    comment_icon = page.locator("svg[aria-label='Comentar'], svg[aria-label='Comment']").first
                    if comment_icon.is_visible(timeout=2000):
                        comment_icon.click()
                        time.sleep(1.5)
                        for selector in comment_selectors:
                            loc = page.locator(selector).first
                            if loc.is_visible(timeout=1500):
                                comment_box = selector
                                break
                except Exception:
                    pass

            if not comment_box:
                print(Fore.RED + "❌ Não foi possível encontrar o campo de comentário na página. Tentando rolar o post...")
                total_errors_session += 1
                page.mouse.wheel(0, 300)
                time.sleep(2)
                continue

            # Envio com validação real e múltiplos métodos
            success, err_msg = send_comment_to_instagram(page, comment_box, comment_text)

            if not success:
                if err_msg and "Bloqueio detectado" in err_msg:
                    print(Fore.RED + Style.BRIGHT + f"\n⚠️ ALERTA DE SEGURANÇA: {err_msg}!")
                    print(Fore.RED + "Interrompendo a execução imediatamente para proteger a sua conta contra bloqueios temporários.")
                    break
                else:
                    total_errors_session += 1
                    print(Fore.RED + f"❌ Falha ao enviar comentário: {err_msg}")
                    continue

            # Registrar sucesso no histórico
            record_history(comment_text)
            total_posted_session += 1
            print(Fore.GREEN + f"✅ Comentário enviado com sucesso e confirmado! (Total nesta sessão: {total_posted_session})")

            # Se ainda houver comentários pendentes, realizar as pausas
            if idx < total_pending:
                # Pausa por lote a cada N comentários
                batch_size = config.get("comentarios_por_lote", 5)
                if total_posted_session > 0 and (total_posted_session % batch_size == 0):
                    batch_pause = config.get("pausa_lote_segundos", 180)
                    print(Fore.MAGENTA + f"\n☕ Pausa do lote ({batch_size} comentários concluídos).")
                    countdown(
                        batch_pause,
                        "Descanso do lote (anti-ban)",
                        current=idx,
                        total=total_pending,
                        success=total_posted_session,
                        errors=total_errors_session
                    )
                else:
                    # Intervalo aleatório padrão entre comentários
                    min_d = config.get("delay_min_segundos", 45)
                    max_d = config.get("delay_max_segundos", 85)
                    delay = random.randint(min_d, max_d)
                    countdown(
                        delay,
                        "Próximo comentário",
                        current=idx,
                        total=total_pending,
                        success=total_posted_session,
                        errors=total_errors_session
                    )

        print("\n" + render_progress_bar(total_pending, total_pending, total_posted_session, total_errors_session))
        print(Fore.GREEN + Style.BRIGHT + f"\n🎉 Execução concluída! Total de comentários postados: {total_posted_session}")
        browser_context.close()


if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n🛑 Execução interrompida manualmente pelo usuário. O progresso foi salvo!")
    except Exception as e:
        print(Fore.RED + f"\n❌ Ocorreu um erro inesperado: {e}")
