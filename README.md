# 🤖 InstaSorteio - Bot de Comentários no Instagram (PC & Android)

<div align="center">

![Instagram Bot Banner](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Android](https://img.shields.io/badge/Android-APK-3DDC84?style=for-the-badge&logo=android&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-Automated-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI%2FCD-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

**Automação inteligente, humanizada e segura para sorteios do Instagram com suporte para PC, Web App (PWA) e Aplicativo Android (.APK).**

[Recursos](#-recursos-principais) • [Modos de Uso](#-ecossistema-completo) • [Como Usar no Celular](#-app-android-apk) • [Anti-Ban](#-segurança-anti-bloqueio)

</div>

---

## 🌟 Recursos Principais

- ⚡ **Multiplataforma:** Execute diretamente no seu computador (com painel visual ou terminal), controle pelo celular (Web App PWA) ou instale como aplicativo nativo no Android (.APK).
- ✍️ **Digitação 100% Humanizada:**
  - Simula digitação lenta caractere por caractere (150ms a 300ms por tecla).
  - Pausa humanizada extra de **0.4s a 0.8s** ao terminar de digitar cada marcação `@amigo`.
- 💬 **Frases Curtas Criativas Aleatórias:**
  - Alterna automaticamente comentários com frases como: *"Boa sorte!"*, *"Tomara que eu ganhe!"*, *"Sorteia eu!"*, *"Dedos cruzados!"*, *"Tô na torcida!"*, *"Já é meu!"*, *"Fé no prêmio!"*, etc.
- 🍀 **Emojis Variados:** Adiciona emojis aleatórios (*🍀, 🤞, ✨, 🔥, 🙌, 🎯, ⭐, 🎉*) no final de cada comentário para evitar detecção de texto repetitivo.
- 🛡️ **Proteção Anti-Ban Avançada:**
  - Intervalos aleatórios configuráveis (ex: 45s a 85s entre envios).
  - Pausas de descanso programadas por lote (ex: pausa de 3 minutos a cada 5 comentários).
  - Detecção imediata de alertas de bloqueio do Instagram com parada de segurança automática.
- 💾 **Histórico e Retomada Inteligente:** Salva cada comentário postado em `historico_comentarios.txt`. Se você pausar o robô e voltar depois, ele continua exatamente de onde parou sem repetir ninguém!

---

## 🚀 Ecossistema Completo

| Modo | Onde Roda | Como Iniciar | Descrição |
| :--- | :--- | :--- | :--- |
| 📱 **App Android Nativo (.APK)** | Direto no Smartphone | Instalar o arquivo `.apk` | Roda 100% no celular Android via serviço de acessibilidade. |
| 🌐 **Web App Mobile (PWA)** | Celular via Wi-Fi | `INICIAR_APP_MOBILE.bat` | Painel web moderno para controlar o bot do PC pelo celular. |
| 💻 **Painel Visual Desktop (GUI)** | Computador | `INICIAR_BOT.bat` | Interface gráfica moderna com tema escuro para Windows. |
| 📥 **Extrator de Seguidores** | Computador | `extrair/EXECUTAR_EXTRACAO.bat` | Baixa e filtra contas reais, removendo lojas/empresas. |
| ⚡ **Linha de Comando (CLI)** | Terminal | `python bot.py` | Execução rápida direta no terminal. |

---

## 📥 Como Extrair e Filtrar seus Seguidores

Para exportar seus seguidores do Instagram, remover lojas/empresas e deixá-los prontos para o bot:
1. Siga o passo a passo em [extrair/COMO_BAIXAR_SEGUIDORES.md](extrair/COMO_BAIXAR_SEGUIDORES.md).
2. Coloque o arquivo `followers_1.json` baixado na pasta `extrair/`.
3. Dê dois cliques em `extrair/EXECUTAR_EXTRACAO.bat`.
4. A lista `usuarios.txt` será gerada e atualizada automaticamente!

---

## 📱 App Android (.APK)

O projeto conta com uma versão nativa completa na pasta [`app_android_acessibilidade/`](./app_android_acessibilidade/):


### Como Obter o `.APK`:
1. **Compilação Automática na Nuvem:** O repositório possui uma pipeline do **GitHub Actions** em `.github/workflows/build_apk.yml`. Ao fazer qualquer alteração no repositório, o GitHub compila o `.APK` automaticamente!
2. Acesse a aba **Actions** no topo do repositório no GitHub e baixe o arquivo `InstaSorteio-Android-APK.zip`.
3. Extraia e instale no seu celular Android.

---

## 💻 Como Usar no Computador

### 1. Instalação Inicial
Dê dois cliques no arquivo:
```cmd
INSTALAR_PRIMEIRA_VEZ.bat
```
*(Ele instalará o Python, as dependências e o navegador Chromium automaticamente).*

### 2. Executar o Painel Gráfico
Dê dois cliques em:
```cmd
INICIAR_BOT.bat
```
- Cole o link do post do Instagram.
- Escolha a quantidade de amigos por comentário (ex: 1, 2, 3 amigos).
- Clique em **"▶ INICIAR BOT"**.

### 3. Executar o Web App para Celular
Dê dois cliques em:
```cmd
INICIAR_APP_MOBILE.bat
```
- O terminal exibirá um **QR Code**. Aponte a câmera do seu celular conectado ao mesmo Wi-Fi para abrir o painel direto na tela do smartphone!

---

## ⚙️ Arquivo de Configuração (`config.json`)

Você pode personalizar todas as preferências do bot editando o `config.json`:

```json
{
  "url_post": "https://www.instagram.com/p/SEU_POST_AQUI/",
  "usuarios_por_comentario": 3,
  "delay_min_segundos": 45,
  "delay_max_segundos": 85,
  "comentarios_por_lote": 5,
  "pausa_lote_segundos": 180,
  "limite_maximo_comentarios": 0,
  "adicionar_frase_aleatoria": true,
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
  "adicionar_emoji_aleatorio": true,
  "emojis": ["🍀", "🤞", "✨", "🔥", "🙌", "🎯", "⭐", "🎉"],
  "arquivo_usuarios": "usuarios.txt"
}
```

---

## 🛡️ Dicas de Segurança Anti-Bloqueio

1. **Mantenha os tempos recomendados:** Evite tempos menores que 40 segundos entre comentários.
2. **Use lotes de descanso:** Recomendamos pausas de 3 a 5 minutos a cada 5 comentários enviados.
3. **Mantenha frases e emojis ativados:** A variação contínua de texto é a melhor defesa contra os filtros de spam do Instagram.

---

<div align="center">
  Desenvolvido para máxima praticidade e segurança em sorteios do Instagram.
</div>
