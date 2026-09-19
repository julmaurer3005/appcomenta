# 📥 Como Baixar a Lista de Seguidores do Instagram (Formato JSON)

Este guia ensina o passo a passo exato para exportar os seus seguidores diretamente da **Central de Contas do Instagram/Meta** e utilizá-los no Bot de Sorteios.

---

## 📱 Opção 1: Pelo Celular (App do Instagram) - Recomendado

1. Abra o aplicativo do **Instagram** e vá até o seu **Perfil**.
2. Toque no **Menu (☰)** no canto superior direito e selecione **Central de Contas** (ou *Sua atividade* ➔ *Baixar suas informações*).
3. Role até a opção **Suas informações e permissões** e toque em **Baixar suas informações**.
4. Toque em **Baixar ou transferir informações**.
5. Selecione a sua conta do Instagram.
6. Escolha a opção **Algumas das suas informações** *(para baixar rápido e apenas o necessário)*.
7. Na lista, desça até a seção **Conexões** e marque apenas:
   - ☑️ **Seguidores e seguindo** (Followers and following).
8. Toque em **Avançar** e escolha **Baixar no dispositivo**.
9. **⚙️ ATENÇÃO NAS CONFIGURAÇÕES DE DOWNLOAD (MUITO IMPORTANTE):**
   - **Intervalo de datas:** Mude para `Desde o início` *(para exportar todos os seus seguidores)*.
   - **Formato:** Altere de HTML para **`JSON`** *(⚠️ Se deixar em HTML o script não conseguirá ler)*.
   - **Qualidade da mídia:** Média ou Baixa *(só conterá textos)*.
10. Toque em **Criar arquivos** (ou *Solicitar download*).
11. O Instagram enviará uma notificação/e-mail em poucos minutos quando o arquivo estiver pronto para download.
12. Baixe o arquivo compactado (`.zip`).

---

## 💻 Opção 2: Pelo Computador (Navegador Web)

1. Acesse [instagram.com](https://www.instagram.com) e faça login na sua conta.
2. Clique no menu **Mais (☰)** no canto inferior esquerdo e clique em **Configurações**.
3. Clique em **Central de Contas** (Meta) no menu lateral.
4. Vá em **Suas informações e permissões** ➔ **Baixar suas informações**.
5. Clique em **Baixar ou transferir informações** e selecione sua conta.
6. Escolha **Algumas das suas informações** ➔ Marque **Seguidores e seguindo**.
7. Selecione **Baixar no dispositivo**.
8. Defina as opções:
   - **Formato:** `JSON` *(Obrigatório)*
   - **Intervalo de datas:** `Desde o início`
9. Clique em **Criar arquivos** e aguarde o e-mail com o link para baixar o `.zip`.

---

## 📂 Como Colocar o Arquivo na Pasta e Rodar a Extração

1. Abra o arquivo `.zip` que você baixou do Instagram.
2. Navegue pelas pastas internas até encontrar:
   ```
   connections/followers_and_following/
   ```
3. Localize o arquivo chamado:
   - **`followers_1.json`** (contém os perfis que te seguem)  
   *(ou `following.json` se você preferir marcar quem você segue)*.
4. Copie esse arquivo `.json` e cole aqui dentro da pasta **`extrair/`**.
   *(Você pode manter o nome `followers_1.json` ou renomear para `seguidores.json`)*.

---

## 🚀 Como Executar a Limpeza e Extração

Com o arquivo `.json` dentro da pasta `extrair/`:

### No Windows:
* Dê **2 cliques** no arquivo:
  ```cmd
  EXECUTAR_EXTRACAO.bat
  ```

### Ou via Terminal:
```bash
python extrair/extrair_seguidores.py
```

---

## ✨ O que o Script faz automaticamente?

1. 🔍 **Lê o JSON do Instagram**: Reconhece todos os perfis exportados.
2. 🧹 **Remove Duplicatas**: Garante que cada amigo apareça apenas uma vez.
3. 🏢 **Filtro Anti-Empresas/Lojas**: Detecta e remove automaticamente perfis comerciais (lojas, advocacias, pizzarias, barbearias, pets, academias, etc.) para você marcar apenas pessoas reais.
4. 💾 **Gera o `seguidores.txt`** limpo e com arroba (`@usuario`).
5. ⚡ **Atualiza o `usuarios.txt` da raiz** automaticamente, deixando tudo pronto para o seu bot comentar!
