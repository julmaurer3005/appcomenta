# 📱 InstaSorteio Android - Aplicativo Standalone (.APK)

Este projeto contém o aplicativo Android nativo do **InstaSorteio**, permitindo que o bot execute **100% dentro do seu celular Android**, com login seguro do Instagram, digitação humanizada lenta, pausas anti-ban e frases criativas.

---

## 🌟 Funcionalidades do App Android

* **100% no Celular:** Não precisa de computador ligado nem de servidor.
* **Digitação Humanizada:** Intervalos de 150ms a 300ms por caractere e pausa de ~0.5s entre marcações `@amigo`.
* **Frases Criativas & Emojis:** Variação automática com *"Boa sorte!"*, *"Dedos cruzados!"*, *"Sorteia eu!"*, *"Tomara que eu ganhe!"*, etc.
* **Importação de Lista:** Importe qualquer arquivo `.txt` do seu celular com 1 toque.
* **WakeLock (Anti-Suspensão):** Mantém o processamento ativo sem deixar o Android suspender o robô.
* **Login Seguro:** Webview integrado com persistência de sessão e cookies no armazenamento interno do Android.

---

## 📦 Como Obter o Arquivo `.APK` para Instalar no Celular

Existem **2 maneiras simples** de gerar o seu arquivo `.apk`:

### 🚀 Método 1: Compilação Gratuita na Nuvem (Recomendado - Sem instalar nada no PC)

1. Suba esta pasta para um repositório seu no **GitHub** (pode ser privado ou público).
2. O arquivo automático [`.github/workflows/build_apk.yml`](../.github/workflows/build_apk.yml) iniciará a compilação do APK nos servidores do GitHub automaticamente.
3. Acesse a aba **Actions** no seu GitHub, clique na última execução e baixe o arquivo `InstaSorteio-Android-APK.zip`.
4. Extraia o arquivo no seu celular e toque para **Instalar**!

---

### 💻 Método 2: Compilação Local com Android Studio

1. Certifique-se de ter o **Node.js** e o **Android Studio** instalados no computador.
2. Na pasta `app_android/`, dê dois cliques em:
   ```cmd
   build_apk.bat
   ```
3. O Android Studio abrirá com o projeto pronto.
4. No menu superior do Android Studio, clique em:
   `Build` ➔ `Build Bundle(s) / APK(s)` ➔ `Build APK(s)`.
5. Ao concluir, o Android Studio mostrará o botão `locate` com o arquivo `.apk` pronto para passar para o celular via USB ou WhatsApp.

---

## 📱 Como Usar o App no Celular (Passo a Passo)

1. **Abra o App no Android:**
   - Toque no ícone do **InstaSorteio**.
2. **Conectar sua Conta:**
   - Vá na aba **🔐 Instagram** e faça login na sua conta normalmente (o login fica salvo para sempre no celular).
3. **Carregar Lista de Amigos:**
   - Na aba **👥 Lista @**, toque em **"📁 Importar Arquivo .txt"** e selecione o seu arquivo de amigos do celular.
4. **Configurar o Sorteio:**
   - Na aba **🎯 Sorteio**, cole o link do post do Instagram.
   - Escolha quantos amigos marcar por comentário (ex: 2 ou 3).
5. **Iniciar:**
   - Toque no botão grande **"▶ INICIAR NO ANDROID"**.
   - O app começará a comentar com intervalos seguros, mostrando o progresso em tempo real na tela!
