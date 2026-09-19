# 📋 Plano de Projeto: Plataforma Web de Sorteios para Instagram (Estilo Simpliers)

> **Documento de Especificação Técnica e Roteiro de Implementação**  
> **Referência Visual e Funcional:** [Simpliers Instagram](https://simpliers.com/pt/sorteio/instagram)  
> **Data de Criação:** 19/09/2026  
> **Status:** Pronto para Execução Futura

---

## 🎯 1. Visão Geral do Projeto

O objetivo deste projeto é construir uma **aplicação web completa, moderna e autônoma para realização de sorteios no Instagram**, inspirada nas melhores funcionalidades do Simpliers e AppSorteos, porém **sem custos por sorteio, sem limites de comentários e com controle total das regras e dados**.

A plataforma permitirá colar o link de qualquer publicação pública ou restrita, extrair todos os comentários em alta velocidade, configurar regras básicas e avançadas de premiação e executar uma animação visual rica (estilo roleta/show de TV) para transmissões ao vivo e comprovação de idoneidade.

---

## 🏗️ 2. Arquitetura da Aplicação

```
┌────────────────────────────────────────────────────────────────────────┐
│                        INTERFACE WEB (FRONTEND)                        │
│  - Tema Dark Mode Premium (Cores grafite, neon e degradê)              │
│  - Inputs dinâmicos com contadores (+ / -) e toggles modernos          │
│  - Barra de progresso de extração em tempo real (Server-Sent Events)    │
│  - Animação de Roleta, Revelação com Confetes e Certificado Digital    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Requisições HTTP / WebSockets / SSE
┌───────────────────────────────────▼────────────────────────────────────┐
│                         BACKEND (PYTHON / FLASK)                       │
│                                                                        │
│  ┌───────────────────────┐  ┌───────────────────┐  ┌────────────────┐ │
│  │   Motor de Extração   │  │  Motor de Sorteio │  │ Gerenciador de │ │
│  │    (API / Playwright) │  │  (Filtros/Regras) │  │   Histórico    │ │
│  └───────────┬───────────┘  └─────────┬─────────┘  └────────┬───────┘ │
└──────────────┼────────────────────────┼─────────────────────┼─────────┘
               │                        │                     │
┌──────────────▼────────────────────────▼─────────────────────▼─────────┐
│                          BANCO DE DADOS & CACHE                        │
│  - SQLite / JSON local para comentários do post e histórico de sorteios│
│  - Sessão persistente do Instagram (.sessao_instagram)                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 3. Stack Tecnológica Recomendada

* **Frontend:**
  * **HTML5 Semântico & CSS3 Moderno:** Paleta de cores dark mode customizada, tipografia moderna (Google Fonts Inter/Outfit), glassmorphism e responsividade completa.
  * **JavaScript (ES6+):** Manipulação de DOM reativa, animações de suspense, biblioteca `canvas-confetti` para celebração.
* **Backend:**
  * **Python (Flask ou FastAPI):** Servidor leve, modular e de rápida inicialização.
  * **Playwright + Requests:** Automação stealth com interceptação de pacotes de rede e consumo de APIs GraphQL do Instagram.
  * **SQLite / SQLAlchemy:** Armazenamento local rápido de posts, listas de comentários e histórico de certificados.

---

## 🧩 4. Especificação Detalhada das Funcionalidades

### 4.1. Cabeçalho e Painel Superior
* **Sorteios Anteriores:** Menu dropdown listando os últimos sorteios com data, título, quantidade de participantes e link para reabrir o certificado de auditoria.
* **Guia / Como Usar:** Modal explicativo ensinando o passo a passo para quem vai transmitir o sorteio ao vivo.

---

### 4.2. Entrada do Post e Importação
* **Input com Ícone do Instagram:** Campo com máscara e validação de URL do Instagram (`/p/ID/`, `/reel/ID/`).
* **Botão de Colar Rápido:** Acessa a área de transferência do navegador em 1 clique.
* **Modo Alternativo (Upload Manual):** Opção de subir arquivo `.json`, `.csv` ou `.txt` com comentários para sorteios locais/offline sem necessidade de raspar o Instagram na hora.

---

### 4.3. Configurações Básicas do Sorteio
* **Nome do Sorteio:** Ex: *"Sorteio de 1 Ano - Loja X"*.
* **Número de Vencedores:** Seletor com botões `[-]` e `[+]` (padrão: 1).
* **Número de Substitutos / Suplentes:** Seletor de suplentes sorteados em caso de desclassificação (padrão: 0 ou 1).
* **Tags Mínimas por Comentário:** Exige quantidade mínima de `@amigos` marcados (ex: 1, 2, 3 ou 0 para livre).

---

### 4.4. Regras Avançadas & Filtros de Integridade
* **Contas Obrigatórias a Seguir:** Campo com tags dinâmicas para adicionar os perfis que o vencedor obrigatoriamente deve seguir (com botão "Obter contas").
* **Modo de Chances:**
  * `[Opção A]` **Proporcional:** Cada comentário válido equivale a 1 chance no pote (quanto mais comentar, mais chances).
  * `[Opção B]` **Usuário Único:** Cada pessoa concorre apenas 1 vez, independente de quantos comentários fez.
* **Filtros de Perfil do Vencedor:**
  * `[Toggle]` Deve ter foto de perfil.
  * `[Toggle]` Deve ter nome preenchido.
  * `[Toggle]` Deve ter biografia.
  * `[Contador]` Contagem mínima de publicações.
  * `[Contador]` Contagem mínima de seguidores.
* **Filtros de Conteúdo do Comentário:**
  * Filtro de hashtags ou palavras-chave obrigatórias (ex: `#sorteio`, `eu quero`).
  * Bloqueio de menções repetidas dos mesmos amigos.
  * Bloqueio de menções a contas comerciais ou verificadas.

---

### 4.5. Motor de Extração em Tempo Real
1. **API GraphQL Paginada:** Requisições sequenciais usando ponteiros `end_cursor` coletando lotes de 50 comentários por pacote.
2. **Interceptação Playwright (Fallback Seguro):** Caso o post tenha restrição de idade ou captcha, navega usando `.sessao_instagram` e captura as respostas JSON direto do tráfego de rede.
3. **Barra de Progresso ao Vivo:** Feedback visual em tempo real para o usuário na tela:
   * Total de comentários identificados.
   * Quantidade extraída até o momento (`Ex: 45.200 / 88.500 - 51%`).
   * Tempo estimado restante.

---

### 4.6. Tela do Sorteio (O Show da Live)
* **Contagem Regressiva de Suspense:** Timer animado `3... 2... 1...`.
* **Animação da Roleta / Efeito Slot Machine:** Os nomes dos concorrentes passam rapidamente na tela diminuindo a velocidade até travar no vencedor.
* **Celebração:** Explosão de confetes e destaque com avatar do perfil, nome de usuário, data/hora e o texto exato do comentário premiado.
* **Área dos Suplentes:** Lista ordenada dos substitutos sorteados logo abaixo.
* **Certificado de Auditoria:**
  * Código Hash de integridade único.
  * Resumo dos parâmetros aplicados no sorteio.
  * Botão de "Copiar Link do Certificado" / "Salvar Imagem para o Story".

---

## 📁 5. Estrutura de Diretórios Recomendada

```
sorteador_instagram/
│
├── app.py                      # Servidor Flask principal e rotas
├── config.py                   # Configurações do servidor e paths
├── requirements.txt            # Dependências Python (Flask, Playwright, etc.)
│
├── services/
│   ├── __init__.py
│   ├── extractor.py            # Motor de extração GraphQL e interceptação Playwright
│   ├── raffle_engine.py        # Algoritmo de sorteio, aplicação de regras e filtros
│   ├── validator.py            # Validação de regras (@menções, perfil, palavras)
│   └── certificate.py          # Geração do comprovante/certificado digital
│
├── database/
│   ├── __init__.py
│   ├── db.py                   # Conexão SQLite
│   └── models.py               # Modelos: Sorteio, Comentario, Participante
│
├── static/
│   ├── css/
│   │   ├── style.css           # Estilos principais Dark Mode estilo Simpliers
│   │   ├── animations.css      # Animações de roleta, confetes e loaders
│   │   └── components.css      # Botões +/-, switches, cards e modals
│   ├── js/
│   │   ├── main.js             # Lógica da interface e binding de eventos
│   │   ├── extractor_stream.js # Escuta de progresso via Server-Sent Events
│   │   ├── roulette.js         # Animação da roleta de sorteio
│   │   └── confetti.browser.min.js
│   └── assets/
│       └── logo.png
│
└── templates/
    ├── index.html              # Tela inicial de configuração do sorteio
    ├── extracting.html         # Tela de progresso da coleta de comentários
    ├── live_draw.html          # Tela do sorteio ao vivo (roleta e show)
    ├── certificate.html        # Página pública do certificado de resultado
    └── history.html            # Histórico de sorteios realizados
```

---

## 🚀 6. Roteiro Passo a Passo para Execução (Fases)

### **Fase 1: Motor de Extração e Validação (Backend Base)**
- [ ] Criar o script `services/extractor.py` com suporte a paginação de comentários via API GraphQL do Instagram.
- [ ] Integrar fallback com Playwright usando `.sessao_instagram` para posts com restrição de login.
- [ ] Implementar regex de captura de menções (`@usuario`) e limpeza de dados.

### **Fase 2: Motor de Sorteio Criptográfico e Filtros**
- [ ] Criar `services/raffle_engine.py` com algoritmo baseado em `secrets.SystemRandom`.
- [ ] Implementar os filtros de tags mínimas, comentários únicos vs chances proporcionais e palavras-chave.
- [ ] Suporte a seleção de $N$ titulares e $M$ suplentes.

### **Fase 3: Interface Web Dark Mode (Frontend Simpliers Style)**
- [ ] Construir `templates/index.html` com os controles de Vencedores, Suplentes, Tags e Regras Avançadas.
- [ ] Criar o sistema de botões numéricos com incremento/decremento suave (`+` / `-`).
- [ ] Criar o sistema de toggles customizados para as regras de perfil.

### **Fase 4: Animações de Sorteio e Certificado Digital**
- [ ] Desenvolver o componente visual de roleta (`roulette.js`) com efeito de desaceleração.
- [ ] Integrar efeito de confetes e cartão de exibição do vencedor.
- [ ] Gerar página do certificado auditável com código único.

### **Fase 5: Testes Integrados e Empacotamento**
- [ ] Testar com publicações pequenas (< 100 comentários) e publicações grandes (> 50.000 comentários).
- [ ] Criar executável ou script `.bat` de 1 clique para iniciar o servidor localmente no navegador.

---

## 📄 7. Notas para Implementação Futura

> [!TIP]
> **Compatibilidade Offline:** O recurso de upload de arquivos JSON/CSV garante que mesmo se o Instagram passar por instabilidades ou aplicar bloqueios temporários de IP, os sorteios sempre poderão ser realizados carregando listas exportadas.

> [!IMPORTANT]
> **Preservação de Sessão:** A pasta `.sessao_instagram` já existente no diretório de trabalho pode ser reaproveitada diretamente para alimentar o extrator sem necessidade de fazer login novamente.

---
*Plano elaborado com sucesso para futura execução técnica.*
