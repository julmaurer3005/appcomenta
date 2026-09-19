"""
Interface Gráfica Amigável (GUI) para o Bot de Comentários no Instagram
Desenvolvido em Tkinter com suporte a seleção de arquivos, configuração dinâmica e anti-ban.
"""

import os
import sys
import re
import json
import time
import random
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# Configurar encoding UTF-8 no Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CONFIG_FILE = "config.json"
SESSION_DIR = ".sessao_instagram"
HISTORY_FILE = "historico_comentarios.txt"


class InstagramBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Bot de Sorteios Instagram - Fácil & Seguro")
        self.root.geometry("760x780")
        self.root.minsize(700, 720)
        self.root.configure(bg="#0f172a")

        self.is_running = False
        self.stop_requested = False
        self.worker_thread = None

        self.users_list = []
        self.pending_chunks = []
        self.total_posted = 0
        self.total_errors = 0

        self._setup_styles()
        self._load_saved_config()
        self._create_widgets()
        self._load_users_from_file(self.file_path_var.get())

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Configurações de cores modernas (Dark Slate & Vibrant Blue)
        self.bg_color = "#0f172a"
        self.card_bg = "#1e293b"
        self.card_border = "#334155"
        self.text_primary = "#f8fafc"
        self.text_secondary = "#94a3b8"
        self.accent_color = "#3b82f6"
        self.success_color = "#10b981"
        self.danger_color = "#ef4444"
        self.warning_color = "#f59e0b"

        self.style.configure(".", background=self.bg_color, foreground=self.text_primary, font=("Segoe UI", 10))
        self.style.configure("Card.TFrame", background=self.card_bg, relief="flat")
        self.style.configure("CardHeader.TLabel", background=self.card_bg, foreground=self.accent_color, font=("Segoe UI", 11, "bold"))
        self.style.configure("CardLabel.TLabel", background=self.card_bg, foreground=self.text_primary, font=("Segoe UI", 10))
        self.style.configure("CardSubLabel.TLabel", background=self.card_bg, foreground=self.text_secondary, font=("Segoe UI", 9))
        self.style.configure("StatNum.TLabel", background=self.card_bg, foreground=self.success_color, font=("Segoe UI", 16, "bold"))

        # Estilo do Progressbar
        self.style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor="#334155",
            background=self.success_color,
            thickness=16
        )

    def _load_saved_config(self):
        self.config = {
            "url_post": "https://www.instagram.com/p/",
            "usuarios_por_comentario": 3,
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
            "emojis": ["🍀", "🤞", "✨", "🔥", "🙌", "🎯", "⭐", "🎉"],
            "arquivo_usuarios": "usuarios.txt"
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.config.update(saved)
            except Exception:
                pass

    def _save_config(self):
        try:
            self.config["url_post"] = self.url_var.get().strip()
            self.config["usuarios_por_comentario"] = int(self.chunk_size_var.get())
            self.config["delay_min_segundos"] = int(self.delay_min_var.get())
            self.config["delay_max_segundos"] = int(self.delay_max_var.get())
            self.config["comentarios_por_lote"] = int(self.batch_size_var.get())
            self.config["pausa_lote_segundos"] = int(self.batch_pause_var.get())
            self.config["adicionar_frase_aleatoria"] = bool(self.frase_var.get())
            self.config["adicionar_emoji_aleatorio"] = bool(self.emoji_var.get())
            self.config["arquivo_usuarios"] = self.file_path_var.get().strip()
            
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _create_widgets(self):
        main_container = tk.Frame(self.root, bg=self.bg_color, padx=16, pady=16)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 1. Cabeçalho
        header_frame = tk.Frame(main_container, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 12))

        title_lbl = tk.Label(
            header_frame,
            text="🤖 Bot de Sorteios do Instagram",
            font=("Segoe UI", 16, "bold"),
            bg=self.bg_color,
            fg="#60a5fa"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            header_frame,
            text="Marque amigos automaticamente em posts de sorteio com segurança anti-bloqueio.",
            font=("Segoe UI", 9),
            bg=self.bg_color,
            fg=self.text_secondary
        )
        sub_lbl.pack(anchor="w")

        # 2. Card de Configurações do Sorteio
        config_card = tk.Frame(main_container, bg=self.card_bg, padx=16, pady=14, highlightbackground=self.card_border, highlightthickness=1)
        config_card.pack(fill=tk.X, pady=(0, 12))

        tk.Label(config_card, text="🎯 1. Configurações do Sorteio", font=("Segoe UI", 11, "bold"), bg=self.card_bg, fg=self.accent_color).pack(anchor="w", pady=(0, 10))

        # Campo URL do Post
        url_frame = tk.Frame(config_card, bg=self.card_bg)
        url_frame.pack(fill=tk.X, pady=3)

        tk.Label(url_frame, text="Link do Post do Sorteio:", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.text_primary).pack(anchor="w")
        url_input_frame = tk.Frame(url_frame, bg=self.card_bg)
        url_input_frame.pack(fill=tk.X, pady=(2, 0))

        self.url_var = tk.StringVar(value=self.config.get("url_post", ""))
        self.url_entry = tk.Entry(
            url_input_frame,
            textvariable=self.url_var,
            font=("Segoe UI", 10),
            bg="#0f172a",
            fg=self.text_primary,
            insertbackground=self.text_primary,
            relief="flat",
            highlightbackground=self.card_border,
            highlightthickness=1
        )
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 6))

        paste_btn = tk.Button(
            url_input_frame,
            text="📋 Colar",
            font=("Segoe UI", 9),
            bg="#334155",
            fg=self.text_primary,
            activebackground="#475569",
            activeforeground=self.text_primary,
            relief="flat",
            cursor="hand2",
            command=self._paste_clipboard
        )
        paste_btn.pack(side=tk.RIGHT, ipadx=8, ipady=3)

        # Seleção de Arquivo e Quantidade de @
        row2_frame = tk.Frame(config_card, bg=self.card_bg)
        row2_frame.pack(fill=tk.X, pady=(10, 0))

        # Arquivo de Usuários
        file_col = tk.Frame(row2_frame, bg=self.card_bg)
        file_col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        tk.Label(file_col, text="Lista de Usuários (.txt):", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.text_primary).pack(anchor="w")
        file_input_frame = tk.Frame(file_col, bg=self.card_bg)
        file_input_frame.pack(fill=tk.X, pady=(2, 0))

        self.file_path_var = tk.StringVar(value=self.config.get("arquivo_usuarios", "usuarios.txt"))
        self.file_entry = tk.Entry(
            file_input_frame,
            textvariable=self.file_path_var,
            font=("Segoe UI", 9),
            bg="#0f172a",
            fg=self.text_primary,
            insertbackground=self.text_primary,
            relief="flat",
            highlightbackground=self.card_border,
            highlightthickness=1
        )
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 6))

        browse_btn = tk.Button(
            file_input_frame,
            text="📁 Escolher...",
            font=("Segoe UI", 9),
            bg="#334155",
            fg=self.text_primary,
            activebackground="#475569",
            activeforeground=self.text_primary,
            relief="flat",
            cursor="hand2",
            command=self._choose_file
        )
        browse_btn.pack(side=tk.RIGHT, ipadx=6, ipady=3)

        # Quantidade de amigos por comentário
        chunk_col = tk.Frame(row2_frame, bg=self.card_bg)
        chunk_col.pack(side=tk.RIGHT, padx=(8, 0))

        tk.Label(chunk_col, text="Amigos por Comentário:", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.text_primary).pack(anchor="w")
        
        self.chunk_size_var = tk.IntVar(value=self.config.get("usuarios_por_comentario", 3))
        chunk_spin = tk.Spinbox(
            chunk_col,
            from_=1,
            to=10,
            textvariable=self.chunk_size_var,
            font=("Segoe UI", 10, "bold"),
            bg="#0f172a",
            fg="#38bdf8",
            buttonbackground="#334155",
            relief="flat",
            width=8,
            command=self._on_chunk_change
        )
        chunk_spin.pack(fill=tk.X, pady=(2, 0), ipady=3)

        # Resumo de Usuários
        self.users_summary_lbl = tk.Label(
            config_card,
            text="Carregando lista de usuários...",
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg=self.success_color
        )
        self.users_summary_lbl.pack(anchor="w", pady=(8, 0))

        # 3. Card Anti-Bloqueio (Delays e Segurança)
        safety_card = tk.Frame(main_container, bg=self.card_bg, padx=16, pady=12, highlightbackground=self.card_border, highlightthickness=1)
        safety_card.pack(fill=tk.X, pady=(0, 12))

        tk.Label(safety_card, text="🛡️ 2. Segurança Anti-Bloqueio (Recomendado manter padrão)", font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg="#fbbf24").pack(anchor="w", pady=(0, 8))

        safety_grid = tk.Frame(safety_card, bg=self.card_bg)
        safety_grid.pack(fill=tk.X)

        # Delay Mínimo
        tk.Label(safety_grid, text="Espera Mínima (s):", font=("Segoe UI", 8), bg=self.card_bg, fg=self.text_secondary).grid(row=0, column=0, sticky="w", padx=4)
        self.delay_min_var = tk.IntVar(value=self.config.get("delay_min_segundos", 45))
        tk.Spinbox(safety_grid, from_=20, to=300, textvariable=self.delay_min_var, font=("Segoe UI", 9), bg="#0f172a", fg=self.text_primary, width=6).grid(row=1, column=0, padx=4, pady=2)

        # Delay Máximo
        tk.Label(safety_grid, text="Espera Máxima (s):", font=("Segoe UI", 8), bg=self.card_bg, fg=self.text_secondary).grid(row=0, column=1, sticky="w", padx=4)
        self.delay_max_var = tk.IntVar(value=self.config.get("delay_max_segundos", 85))
        tk.Spinbox(safety_grid, from_=30, to=500, textvariable=self.delay_max_var, font=("Segoe UI", 9), bg="#0f172a", fg=self.text_primary, width=6).grid(row=1, column=1, padx=4, pady=2)

        # Comentários por Lote
        tk.Label(safety_grid, text="Comentários por Lote:", font=("Segoe UI", 8), bg=self.card_bg, fg=self.text_secondary).grid(row=0, column=2, sticky="w", padx=4)
        self.batch_size_var = tk.IntVar(value=self.config.get("comentarios_por_lote", 5))
        tk.Spinbox(safety_grid, from_=1, to=50, textvariable=self.batch_size_var, font=("Segoe UI", 9), bg="#0f172a", fg=self.text_primary, width=6).grid(row=1, column=2, padx=4, pady=2)

        # Descanso do Lote
        tk.Label(safety_grid, text="Descanso do Lote (s):", font=("Segoe UI", 8), bg=self.card_bg, fg=self.text_secondary).grid(row=0, column=3, sticky="w", padx=4)
        self.batch_pause_var = tk.IntVar(value=self.config.get("pausa_lote_segundos", 180))
        tk.Spinbox(safety_grid, from_=60, to=1200, textvariable=self.batch_pause_var, font=("Segoe UI", 9), bg="#0f172a", fg=self.text_primary, width=7).grid(row=1, column=3, padx=4, pady=2)

        # Checkbox Frases Curtas
        self.frase_var = tk.BooleanVar(value=self.config.get("adicionar_frase_aleatoria", True))
        frase_check = tk.Checkbutton(
            safety_grid,
            text="Adicionar frases curtas aleatórias (ex: Boa sorte, Torcendo, Sorteia eu!)",
            variable=self.frase_var,
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg=self.text_primary,
            activebackground=self.card_bg,
            activeforeground=self.text_primary,
            selectcolor="#0f172a"
        )
        frase_check.grid(row=2, column=0, columnspan=4, sticky="w", pady=(8, 0))

        # Checkbox Emojis
        self.emoji_var = tk.BooleanVar(value=self.config.get("adicionar_emoji_aleatorio", True))
        emoji_check = tk.Checkbutton(
            safety_grid,
            text="Adicionar emojis aleatórios (🍀, 🤞, ✨, 🔥, 🙌...)",
            variable=self.emoji_var,
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg=self.text_primary,
            activebackground=self.card_bg,
            activeforeground=self.text_primary,
            selectcolor="#0f172a"
        )
        emoji_check.grid(row=3, column=0, columnspan=4, sticky="w", pady=(4, 0))

        # 4. Botões de Controle e Ação
        btn_frame = tk.Frame(main_container, bg=self.bg_color)
        btn_frame.pack(fill=tk.X, pady=(0, 12))

        self.start_btn = tk.Button(
            btn_frame,
            text="▶ INICIAR BOT",
            font=("Segoe UI", 12, "bold"),
            bg="#16a34a",
            fg="#ffffff",
            activebackground="#15803d",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            command=self._start_bot
        )
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 6))

        self.stop_btn = tk.Button(
            btn_frame,
            text="⏹ PARAR",
            font=("Segoe UI", 12, "bold"),
            bg="#dc2626",
            fg="#ffffff",
            activebackground="#b91c1c",
            activeforeground="#ffffff",
            relief="flat",
            state=tk.DISABLED,
            cursor="hand2",
            command=self._stop_bot
        )
        self.stop_btn.pack(side=tk.RIGHT, ipady=8, ipadx=24)

        # 5. Card de Progresso e Métricas
        prog_card = tk.Frame(main_container, bg=self.card_bg, padx=16, pady=12, highlightbackground=self.card_border, highlightthickness=1)
        prog_card.pack(fill=tk.X, pady=(0, 10))

        # Status e porcentagem
        status_row = tk.Frame(prog_card, bg=self.card_bg)
        status_row.pack(fill=tk.X, pady=(0, 4))

        self.status_lbl = tk.Label(status_row, text="Status: Pronto", font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=self.accent_color)
        self.status_lbl.pack(side=tk.LEFT)

        self.percent_lbl = tk.Label(status_row, text="0%", font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=self.text_primary)
        self.percent_lbl.pack(side=tk.RIGHT)

        # Barra de Progresso
        self.progress_bar = ttk.Progressbar(prog_card, orient="horizontal", mode="determinate", style="Custom.Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, pady=(0, 8))

        # Métricas em 3 caixas
        metrics_row = tk.Frame(prog_card, bg=self.card_bg)
        metrics_row.pack(fill=tk.X)

        # Enviados
        box1 = tk.Frame(metrics_row, bg="#0f172a", padx=8, pady=4, highlightbackground=self.card_border, highlightthickness=1)
        box1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        tk.Label(box1, text="Enviados", font=("Segoe UI", 8), bg="#0f172a", fg=self.text_secondary).pack()
        self.stat_posted_lbl = tk.Label(box1, text="0", font=("Segoe UI", 13, "bold"), bg="#0f172a", fg=self.success_color)
        self.stat_posted_lbl.pack()

        # Erros
        box2 = tk.Frame(metrics_row, bg="#0f172a", padx=8, pady=4, highlightbackground=self.card_border, highlightthickness=1)
        box2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Label(box2, text="Falhas", font=("Segoe UI", 8), bg="#0f172a", fg=self.text_secondary).pack()
        self.stat_errors_lbl = tk.Label(box2, text="0", font=("Segoe UI", 13, "bold"), bg="#0f172a", fg=self.danger_color)
        self.stat_errors_lbl.pack()

        # Restantes
        box3 = tk.Frame(metrics_row, bg="#0f172a", padx=8, pady=4, highlightbackground=self.card_border, highlightthickness=1)
        box3.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
        tk.Label(box3, text="Pendentes", font=("Segoe UI", 8), bg="#0f172a", fg=self.text_secondary).pack()
        self.stat_pending_lbl = tk.Label(box3, text="0", font=("Segoe UI", 13, "bold"), bg="#0f172a", fg="#38bdf8")
        self.stat_pending_lbl.pack()

        # 6. Log de Atividades
        log_frame = tk.Frame(main_container, bg=self.card_bg, padx=12, pady=10, highlightbackground=self.card_border, highlightthickness=1)
        log_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(log_frame, text="📜 Histórico e Logs em Tempo Real:", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.text_secondary).pack(anchor="w", pady=(0, 4))

        self.log_text = tk.Text(
            log_frame,
            bg="#0b0f19",
            fg="#e2e8f0",
            font=("Consolas", 9),
            relief="flat",
            wrap="word",
            state=tk.NORMAL
        )
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Tags de cores para o log
        self.log_text.tag_config("SUCCESS", foreground="#34d399")
        self.log_text.tag_config("ERROR", foreground="#f87171")
        self.log_text.tag_config("WARN", foreground="#fbbf24")
        self.log_text.tag_config("INFO", foreground="#60a5fa")

        self._log("Interface iniciada com sucesso. Pronto para configurar!", "INFO")

    def _log(self, text, tag="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {text}\n"
        self.root.after(0, self._append_log, formatted, tag)

    def _append_log(self, formatted_text, tag):
        self.log_text.insert(tk.END, formatted_text, tag)
        self.log_text.see(tk.END)

    def _paste_clipboard(self):
        try:
            clipboard_text = self.root.clipboard_get().strip()
            if clipboard_text:
                self.url_var.set(clipboard_text)
                self._log(f"Link colado da área de transferência: {clipboard_text}", "INFO")
        except Exception:
            pass

    def _choose_file(self):
        filename = filedialog.askopenfilename(
            title="Selecione o arquivo com a lista de usuários",
            filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)
            self._load_users_from_file(filename)

    def _on_chunk_change(self):
        self._load_users_from_file(self.file_path_var.get())

    def _load_users_from_file(self, filepath):
        if not os.path.exists(filepath):
            self.users_summary_lbl.config(text=f"❌ Arquivo '{os.path.basename(filepath)}' não encontrado.", fg=self.danger_color)
            self.users_list = []
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            raw_handles = re.findall(r'@([a-zA-Z0-9._]+)', content)
            if not raw_handles:
                words = re.findall(r'[a-zA-Z0-9._]+', content)
                raw_handles = [w for w in words if len(w) > 2]

            seen = set()
            self.users_list = []
            for user in raw_handles:
                handle = f"@{user.strip().lower()}"
                if handle not in seen:
                    seen.add(handle)
                    self.users_list.append(handle)

            chunk_size = self.chunk_size_var.get()
            total_chunks = (len(self.users_list) + chunk_size - 1) // chunk_size if chunk_size > 0 else 0

            # Carregar histórico para ver quantos faltam
            history = set()
            if os.path.exists(HISTORY_FILE):
                try:
                    with open(HISTORY_FILE, "r", encoding="utf-8") as hf:
                        history = {line.strip() for line in hf}
                except Exception:
                    pass

            self.users_summary_lbl.config(
                text=f"✓ {len(self.users_list)} usuários únicos carregados  •  {total_chunks} comentários previstos ({chunk_size} por comentário)",
                fg=self.success_color
            )
            self.stat_pending_lbl.config(text=str(total_chunks))
        except Exception as e:
            self.users_summary_lbl.config(text=f"Erro ao ler arquivo: {e}", fg=self.danger_color)

    def _start_bot(self):
        url = self.url_var.get().strip()
        if not url or "instagram.com/p/" not in url:
            messagebox.showwarning("Atenção", "Por favor, insira um link válido de post do Instagram (ex: https://www.instagram.com/p/...).")
            self.url_entry.focus()
            return

        if not self.users_list:
            messagebox.showerror("Erro", "Nenhum usuário foi encontrado na lista de usuários selecionada.")
            return

        self._save_config()

        self.is_running = True
        self.stop_requested = False
        self.start_btn.config(state=tk.DISABLED, bg="#334155")
        self.stop_btn.config(state=tk.NORMAL, bg="#dc2626")

        self.worker_thread = threading.Thread(target=self._bot_worker, daemon=True)
        self.worker_thread.start()

    def _stop_bot(self):
        if self.is_running:
            self.stop_requested = True
            self._log("Solicitação de parada recebida. Finalizando comentário atual...", "WARN")
            self.status_lbl.config(text="Status: Parando...", fg=self.warning_color)

    def _bot_worker(self):
        from playwright.sync_api import sync_playwright

        self._log("🚀 Iniciando motor do bot com Playwright...", "INFO")
        self.root.after(0, lambda: self.status_lbl.config(text="Status: Abrindo Navegador...", fg=self.accent_color))

        chunk_size = self.chunk_size_var.get()
        chunks = [self.users_list[i:i + chunk_size] for i in range(0, len(self.users_list), chunk_size)]

        # Carregar histórico existente
        history = set()
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = {line.strip() for line in f}
            except Exception:
                pass

        pending_chunks = []
        for c in chunks:
            base = " ".join(c)
            if not any(base in h for h in history):
                pending_chunks.append(c)

        total_pending = len(pending_chunks)
        self._log(f"Comentários pendentes para esta execução: {total_pending}", "INFO")

        if total_pending == 0:
            self._log("🎉 Todos os usuários da lista já foram comentados!", "SUCCESS")
            self._finish_worker()
            return

        self.root.after(0, lambda: self.stat_pending_lbl.config(text=str(total_pending)))

        os.makedirs(SESSION_DIR, exist_ok=True)

        try:
            with sync_playwright() as p:
                browser_context = p.chromium.launch_persistent_context(
                    user_data_dir=os.path.abspath(SESSION_DIR),
                    headless=False,
                    viewport={"width": 1280, "height": 800},
                    args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    locale="pt-BR"
                )

                # Camuflagem Ultra Stealth (Anti-Detecção)
                browser_context.add_init_script("""
                (() => {
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
                    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                    Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
                })();
                """)

                page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()

                # 1. Login
                self._log("Verificando sessão do Instagram...", "INFO")
                page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
                time.sleep(3)

                is_logged_in = False
                try:
                    nav_selectors = ["svg[aria-label='Página inicial']", "svg[aria-label='Home']", "svg[aria-label='Pesquisa']", "svg[aria-label='Direct']"]
                    for sel in nav_selectors:
                        if page.locator(sel).first.is_visible(timeout=3000):
                            is_logged_in = True
                            break
                except Exception:
                    pass

                if not is_logged_in:
                    self._log("🔐 Login necessário: Faça login no navegador aberto.", "WARN")
                    self.root.after(0, lambda: self.status_lbl.config(text="Status: Aguardando Login...", fg=self.warning_color))
                    messagebox.showinfo(
                        "Login no Instagram Necessário",
                        "Faça login na sua conta do Instagram na janela do navegador que se abriu.\n\nDepois de logado e na página inicial do Instagram, clique em OK nesta mensagem para continuar!"
                    )

                # 2. Navegar para o Post
                post_url = self.url_var.get().strip()
                self._log(f"Acessando o post do sorteio: {post_url}", "INFO")
                self.root.after(0, lambda: self.status_lbl.config(text="Status: Carregando Post...", fg=self.accent_color))
                page.goto(post_url, wait_until="domcontentloaded")
                time.sleep(4)

                # Fechar popups
                for txt in ["Agora não", "Not Now", "Cancelar", "Recusar", "Depois"]:
                    try:
                        btn = page.locator(f"button:has-text('{txt}')").first
                        if btn.is_visible(timeout=1000):
                            btn.click()
                    except Exception:
                        pass

                # 3. Execução dos Comentários
                session_posted = 0
                session_errors = 0
                frases = self.config.get("frases", [
                    "Boa sorte!", "Tomara que eu ganhe!", "Sorteia eu!",
                    "Dedos cruzados!", "Tô na torcida!", "Já é meu!",
                    "Quero muito ganhar!", "Vem sorte!", "Na torcida aqui!",
                    "Bora ganhar!", "Agora vai!", "Fé no prêmio!",
                    "Se Deus quiser!", "Confiante!", "Essa vitória é nossa!"
                ])
                emojis = self.config.get("emojis", ["🍀", "🤞", "✨", "🔥", "🙌", "🎯", "⭐", "🎉"])
                use_frase = self.frase_var.get()
                use_emoji = self.emoji_var.get()
                batch_size = self.batch_size_var.get()
                batch_pause = self.batch_pause_var.get()
                delay_min = self.delay_min_var.get()
                delay_max = self.delay_max_var.get()

                for idx, chunk in enumerate(pending_chunks, 1):
                    if self.stop_requested:
                        self._log("🛑 Execução pausada pelo usuário.", "WARN")
                        break

                    parts = list(chunk)
                    if use_frase and frases:
                        parts.append(random.choice(frases))
                    if use_emoji and emojis:
                        parts.append(random.choice(emojis))
                    comment_text = " ".join(parts)

                    self._log(f"[{idx}/{total_pending}] Digitando: {comment_text}", "INFO")
                    self.root.after(0, lambda i=idx, t=total_pending: self.status_lbl.config(text=f"Status: Postando {i} de {t}...", fg=self.accent_color))

                    # Localizar campo
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
                        self._log("❌ Campo de comentário não encontrado na página. Rolando...", "ERROR")
                        session_errors += 1
                        page.mouse.wheel(0, 300)
                        time.sleep(2)
                        continue

                    # Digitação e envio
                    try:
                        box = page.locator(comment_box).first
                        box.click()
                        time.sleep(0.4)

                        for ch in comment_text:
                            page.keyboard.type(ch)
                            time.sleep(random.uniform(0.15, 0.30))
                            # Pausa adicional ao terminar de digitar cada @usuario / palavra (~0.5s)
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
                            "div[role='button']:has-text('Publicar')",
                            "div[role='button']:has-text('Post')"
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
                            # Tentar JS
                            try:
                                page.evaluate("""() => {
                                    const all = document.querySelectorAll('div[role="button"], button');
                                    for (const b of all) {
                                        const txt = (b.innerText || b.textContent || '').trim().toLowerCase();
                                        if (txt === 'publicar' || txt === 'post' || txt === 'postar') {
                                            b.click();
                                            return true;
                                        }
                                    }
                                    return false;
                                }""")
                            except Exception:
                                pass

                        time.sleep(3.5)

                        # Validar se esvaziou
                        val = ""
                        try:
                            val = box.input_value(timeout=1500).strip()
                        except Exception:
                            pass

                        if val:
                            box.focus()
                            page.keyboard.press("Enter")
                            time.sleep(2.5)
                            try:
                                val = box.input_value(timeout=1000).strip()
                            except Exception:
                                pass

                        if not val:
                            # Sucesso confirmado
                            session_posted += 1
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                                f.write(f"[{timestamp}] - Comentário: {comment_text}\n")
                            self._log(f"✓ Comentário {idx} enviado com sucesso!", "SUCCESS")
                        else:
                            session_errors += 1
                            self._log(f"✗ Não foi possível confirmar o envio do comentário {idx}.", "ERROR")

                    except Exception as e:
                        session_errors += 1
                        self._log(f"Erro no comentário {idx}: {e}", "ERROR")

                    # Atualizar interface
                    pct = (idx / total_pending) * 100
                    rem = total_pending - idx
                    self.root.after(0, lambda p=pct, s=session_posted, er=session_errors, r=rem: self._update_metrics(p, s, er, r))

                    # Pausas de segurança
                    if idx < total_pending and not self.stop_requested:
                        if session_posted > 0 and (session_posted % batch_size == 0):
                            self._log(f"☕ Pausa de descanso do lote ({batch_size} comentários). Aguardando {batch_pause}s...", "WARN")
                            for s in range(batch_pause, 0, -1):
                                if self.stop_requested:
                                    break
                                self.root.after(0, lambda sec=s: self.status_lbl.config(text=f"Status: Descanso Lote ({sec}s restantes)...", fg=self.warning_color))
                                time.sleep(1)
                        else:
                            delay = random.randint(delay_min, delay_max)
                            self._log(f"⏳ Intervalo de segurança: aguardando {delay}s...", "INFO")
                            for s in range(delay, 0, -1):
                                if self.stop_requested:
                                    break
                                self.root.after(0, lambda sec=s: self.status_lbl.config(text=f"Status: Próximo em {sec}s...", fg=self.accent_color))
                                time.sleep(1)

                self._log(f"🎉 Processamento finalizado! Total enviados nesta sessão: {session_posted}", "SUCCESS")
                browser_context.close()

        except Exception as e:
            self._log(f"Erro fatal: {e}", "ERROR")

        self._finish_worker()

    def _update_metrics(self, pct, posted, errors, remaining):
        self.progress_bar["value"] = pct
        self.percent_lbl.config(text=f"{pct:.1f}%")
        self.stat_posted_lbl.config(text=str(posted))
        self.stat_errors_lbl.config(text=str(errors))
        self.stat_pending_lbl.config(text=str(remaining))

    def _finish_worker(self):
        self.is_running = False
        self.stop_requested = False
        self.root.after(0, self._reset_buttons)

    def _reset_buttons(self):
        self.start_btn.config(state=tk.NORMAL, bg="#16a34a")
        self.stop_btn.config(state=tk.DISABLED, bg="#334155")
        self.status_lbl.config(text="Status: Concluído", fg=self.success_color)


def main():
    root = tk.Tk()
    app = InstagramBotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
