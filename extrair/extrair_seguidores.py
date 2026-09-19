"""
Script para Extrair e Limpar Seguidores do Instagram a partir de arquivo JSON exportado.
- Extrai todos os perfis de 'seguidores.json' (ou qualquer arquivo JSON de seguidores/seguindo).
- Remove duplicatas.
- Remove contas comerciais, lojas, empresas e serviços usando filtros inteligentes.
- Salva a lista limpa e pronta para uso no bot de sorteios.
"""

import os
import sys
import json
import re

# Configuração de encoding UTF-8 para Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ARQUIVO_JSON = "seguidores.json"
ARQUIVO_SAIDA = "seguidores.txt"

# Padrões precisos de empresas, lojas, marcas, serviços e páginas comerciais
BUSINESS_PATTERNS = [
    # Automotivo
    r"lavacar", r"lava[._]?car", r"cardetails", r"flashcar", r"autopecas", r"veiculos", 
    r"motors", r"locar", r"estetica[._]?auto", r"carbox", r"centro[._]?automotivo",
    # Advocacia e Finanças
    r"advogados", r"advocacia", r"[_.]adv\b", r"\badv[_.]", r"legis_", r"consorcios", r"seguros", r"investimentos", r"financeiros",
    # Alimentação e Gastronomia
    r"confeitaria", r"patisserie", r"burguer", r"burger", r"lanches", r"delivery", r"\bcafe\b", r"[._]cafe", r"cafe[._]", 
    r"assados", r"pizzaria", r"pizzatti", r"sorveteria", r"churrascaria", r"carnes", r"acai", r"donuts", r"biscoitos", 
    r"cervejaria", r"pampabeer", r"braddockbier", r"kinasbier", r"biersite", r"[._]bier", r"bier[._]", r"bebidas", r"drinks", 
    r"gourmet", r"restaurante", r"\bfood\b", r"panivello", r"panelas",
    # Construção, Móveis e Imóveis
    r"edificacoes", r"construtora", r"engenharia", r"arquitetura", r"arqeng", r"construir", r"esquadrias", 
    r"marmoraria", r"vidros", r"moveis", r"solar", r"imoveis", r"imobiliaria", r"portas", r"blocos", r"pavers", 
    r"marmorari", r"glass", r"homestudio", r"decor[._]", r"[._]decor", r"decoratelie", r"decorart",
    # Saúde, Estética e Beleza
    r"clinica", r"hospitalar", r"odontopet", r"dentista", r"biomedica", r"endocrino", r"massoterapeuta", 
    r"bemviver", r"reluzclinic", r"revitalize", r"otica", r"farmacia", r"dermochic", r"makeup", r"cutelaria", r"cuteleiro",
    # Lojas, Moda e Comércio
    r"lingeries", r"\bloja", r"store", r"modas", r"calcados", r"roupas", r"camisaraiz", r"usecamisa", r"bazar", r"atacadao", 
    r"supermercado", r"brindes", r"artesanatos", r"achadinhos", r"sexshop", r"boutique", r"toyshop",
    # Animais / Pets
    r"petshop", r"petschop", r"petsitter", r"canina", r"educadoracanina", r"dogvibes", r"doggy", r"malinois", r"casapet",
    # Mídia, Fotografia e Notícias
    r"fotografia", r"fotografias", r"studios", r"noticias", r"jovempan", r"marketing", r"films", r"videografia",
    # Fitness e Esportes
    r"academia", r"crossfit", r"fitness", r"jiujitsu", r"sportswear",
    # Outros e Páginas
    r"funeraria", r"rotaryclub", r"bombeiro", r"bombeiros", r"bombeira", r"policial", r"coronel", r"cbmrs", 
    r"hospedagens", r"comunitario", r"shopping"
]


def is_business_account(username):
    """Verifica se um nome de usuário corresponde a padrões de empresas ou serviços."""
    u = username.lower().replace("@", "")
    
    for pattern in BUSINESS_PATTERNS:
        if re.search(pattern, u):
            return True, pattern
            
    # Sufixos comuns de comércio local
    if u.endswith("_rs") or u.endswith(".rs") or u.endswith("_ijui") or u.endswith(".ijui") or u.endswith("ijui"):
        if any(w in u for w in ["bar", "cafe", "auto", "chape", "agro", "pampa", "casa", "danica", "paris", "solmix", "tevah", "dom", "ecocar"]):
            return True, "sufixo comercial local"
            
    return False, None


def extrair_usuarios_do_json(caminho_arquivo):
    """Extrai usernames lidando com múltiplos formatos de exportação do Instagram."""
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        dados = json.load(f)

    itens = []
    if isinstance(dados, list):
        itens = dados
    elif isinstance(dados, dict):
        # Pode estar sob chaves como 'relationships_following', 'followers', etc.
        for chave in ["relationships_following", "relationships_followers", "followers", "following"]:
            if chave in dados and isinstance(dados[chave], list):
                itens = dados[chave]
                break
        if not itens:
            # Pega a primeira lista que encontrar no dicionário
            for v in dados.values():
                if isinstance(v, list):
                    itens = v
                    break

    usuarios_extraidos = []

    for item in itens:
        if isinstance(item, dict):
            # Formato padrão 1: string_list_data -> value
            string_data = item.get("string_list_data", [])
            if string_data and isinstance(string_data, list):
                u = string_data[0].get("value")
                if u:
                    usuarios_extraidos.append(u.strip())
                    continue
            
            # Formato padrão 2: title
            if item.get("title"):
                usuarios_extraidos.append(item.get("title").strip())
                continue

            # Formato padrão 3: extrair do link href
            if string_data and isinstance(string_data, list):
                href = string_data[0].get("href", "")
                if "instagram.com/" in href:
                    extracted = href.split("instagram.com/")[-1].strip("/").strip()
                    if extracted:
                        usuarios_extraidos.append(extracted)
                        continue
        elif isinstance(item, str):
            usuarios_extraidos.append(item.strip())

    return usuarios_extraidos


def main():
    print("=" * 65)
    print("   📥 EXTRATOR E HIGIENIZADOR DE SEGUIDORES DO INSTAGRAM 📥")
    print("=" * 65)

    # Identificar arquivo JSON
    caminho = ARQUIVO_JSON
    if not os.path.exists(caminho):
        # Tenta procurar qualquer arquivo .json na pasta
        arquivos_json = [f for f in os.listdir(".") if f.endswith(".json")]
        if arquivos_json:
            caminho = arquivos_json[0]
            print(f"ℹ️ Usando arquivo encontrado: {caminho}")
        else:
            print(f"❌ Erro: Arquivo '{ARQUIVO_JSON}' não foi encontrado na pasta.")
            return

    print(f"\n1. Lendo e extraindo dados de '{caminho}'...")
    todos_usuarios = extrair_usuarios_do_json(caminho)

    if not todos_usuarios:
        print("❌ Nenhum usuário foi identificado no arquivo JSON.")
        return

    print(f"✓ {len(todos_usuarios)} registros extraídos do JSON.")

    print("\n2. Filtrando duplicatas e contas comerciais/empresas...")
    seen = set()
    limpos = []
    duplicados = []
    empresas = []

    for u in todos_usuarios:
        handle = u.lower().replace("@", "").strip()
        if not handle or len(handle) < 2:
            continue

        formatado = f"@{handle}"

        # Checar duplicatas
        if formatado in seen:
            duplicados.append(formatado)
            continue
        seen.add(formatado)

        # Checar se é empresa
        is_biz, motivo = is_business_account(handle)
        if is_biz:
            empresas.append((formatado, motivo))
            continue

        limpos.append(formatado)

    # Salvar resultado em seguidores.txt
    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f_out:
        for user in limpos:
            f_out.write(f"{user}\n")

    print("\n" + "=" * 65)
    print("📊 RESULTADO FINAL:")
    print(f"  • Total bruto extraído:          {len(todos_usuarios)}")
    print(f"  • Duplicados removidos:          {len(duplicados)}")
    print(f"  • Contas comerciais removidas:   {len(empresas)}")
    print(f"  • Usuários reais limpos salvos:  {len(limpos)}")
    print("=" * 65)

    if empresas:
        print("\n🏢 Exemplos de empresas/páginas que foram removidas:")
        for emp, motivo in empresas[:15]:
            print(f"  - {emp:30} (Filtro: {motivo})")
        if len(empresas) > 15:
            print(f"  ... e mais {len(empresas) - 15} contas comerciais.")

    print(f"\n✅ Arquivo '{ARQUIVO_SAIDA}' gerado com sucesso com {len(limpos)} seguidores limpos!")


if __name__ == "__main__":
    main()