import sqlite3
import json
import re
from datetime import datetime, timedelta, timezone
fuso_br = timezone(timedelta(hours=-3))

# Tenta importar a OpenAI se a chave/biblioteca estiver configurada
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

OPENAI_API_KEY = "SUA_CHAVE_OPENAI_AQUI" # Insira sua chave se for usar a API da OpenAI

# ----------------------------------------------------
# 1. TRANSCRIÇÃO DE ÁUDIO (Whisper)
# ----------------------------------------------------
def transcrever_audio(caminho_arquivo_audio):
    if not HAS_OPENAI or OPENAI_API_KEY == "SUA_CHAVE_OPENAI_AQUI":
        print("⚠️ [Modo Simulação]: Sem chave da OpenAI configurada. Retornando texto de exemplo.")
        return "Manda 2 Heineken e 1 Skol Pilsen para a Rua Maria do Ceu 100, vou pagar com 50 reais"
    
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        with open(caminho_arquivo_audio, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                language="pt"
            )
        return transcript.text
    except Exception as e:
        print(f"Erro na transcrição: {e}")
        return None

# ----------------------------------------------------
# 2. REGEX / MOTOR LOCAL (Funciona 100% Grátis/Offline)
# ----------------------------------------------------
def interpretar_pedido_local(texto, produtos_db):
    texto_lower = texto.lower()
    
    # Tentar extrair endereço
    endereco = "Retirada no Balcão"
    match_end = re.search(r'(?:rua|av|avenida|bairro|local|em|na|no)\s+([^\.,\n]+)', texto_lower)
    if match_end:
        endereco = match_end.group(0).title()

    # Tentar extrair pagamento
    valor_pago = 0.0
    match_pago = re.search(r'(?:nota de|pagar com|pago com|troco para)\s*(\d+)', texto_lower)
    if match_pago:
        valor_pago = float(match_pago.group(1))

    # Identificar itens do catálogo
    itens_encontrados = []
    total = 0.0

    for prod_id, nome, preco in produtos_db:
        nome_lower = nome.lower()
        # Busca variações do nome do produto no texto
        palavras_chave = [p for p in nome_lower.split() if len(p) > 3]
        if any(kw in texto_lower for kw in palavras_chave):
            # Procura quantidade antes do nome
            match_qtd = re.search(r'(\d+)\s*(x|unidades|garrafas|latas)?\s*' + re.escape(palavras_chave[0]), texto_lower)
            qtd = int(match_qtd.group(1)) if match_qtd else 1
            
            subtotal = preco * qtd
            total += subtotal
            itens_encontrados.append(f"{qtd}x {nome}")

    if not itens_encontrados:
        itens_str = "Pedido genérico (Verificar mensagem original)"
    else:
        itens_str = ", ".join(itens_encontrados)

    if valor_pago < total:
        valor_pago = total

    troco = valor_pago - total

    return {
        "nome_cliente": "Cliente WhatsApp",
        "endereco": endereco,
        "itens": itens_str,
        "total": total,
        "valor_pago": valor_pago,
        "troco": troco
    }

# ----------------------------------------------------
# 3. INTERPRETAÇÃO COM IA (GPT-4o-mini)
# ----------------------------------------------------
def interpretar_pedido_ia(texto, catalogo_str):
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    prompt_sistema = f"""
    Você é o atendente virtual da adega 'JW BEER'.
    Extraia as informações do pedido a partir do texto enviado pelo cliente.

    Catálogo de Produtos Cadastrados (Nome e Preço R$):
    {catalogo_str}

    Retorne ESTRITAMENTE um JSON com este formato:
    {{
        "nome_cliente": "Nome do cliente se houver, ou 'Cliente WhatsApp'",
        "endereco": "Endereço informado de entrega",
        "itens": "Lista com quantidades e nomes exatos do catálogo",
        "total": 0.00,
        "valor_pago": 0.00,
        "troco": 0.00
    }}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": texto}
        ],
        temperature=0.1
    )
    conteudo = response.choices[0].message.content.strip()
    if conteudo.startswith("```"):
        conteudo = conteudo.split("\n", 1)[1].rsplit("\n", 1)[0]
    return json.loads(conteudo)

# ----------------------------------------------------
# 4. FUNÇÃO PRINCIPAL DE PROCESSAMENTO
# ----------------------------------------------------
def processar_pedido_whatsapp(texto_cliente=None, caminho_audio=None, nome_whatsapp="Cliente Whats"):
    # 1. Obter texto
    if caminho_audio:
        print("🎙️ Processando áudio...")
        texto_processar = transcrever_audio(caminho_audio)
    else:
        texto_processar = texto_cliente

    if not texto_processar:
        return {"sucesso": False, "mensagem": "Nenhuma mensagem/áudio para processar."}

    print(f"📝 Mensagem Recebida: '{texto_processar}'")

    # 2. Buscar catálogo do banco SQLite
    conn = sqlite3.connect("caixa_jwbeer.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, preco FROM produtos")
    produtos = cursor.fetchall()

    # 3. Interpretar
    if HAS_OPENAI and OPENAI_API_KEY != "SUA_CHAVE_OPENAI_AQUI":
        try:
            catalogo_str = "\n".join([f"- {p[1]}: R$ {p[2]:.2f}" for p in produtos])
            dados = interpretar_pedido_ia(texto_processar, catalogo_str)
        except Exception as e:
            print(f"⚠️ Erro na IA GPT ({e}), usando interpretador local fallback...")
            dados = interpretar_pedido_local(texto_processar, produtos)
    else:
        dados = interpretar_pedido_local(texto_processar, produtos)

    if dados.get("nome_cliente") in ["Cliente WhatsApp", "", None]:
        dados["nome_cliente"] = nome_whatsapp

    # 4. Inserir no Banco de Dados SQLite do App
    data_hora = datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M')
    cursor.execute("""
        INSERT INTO pedidos (data_hora, nome_cliente, cliente_endereco, itens, total, valor_pago, troco, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pendente')
    """, (
        data_hora,
        dados["nome_cliente"],
        dados["endereco"],
        dados["itens"],
        dados["total"],
        dados["valor_pago"],
        dados["troco"]
    ))
    conn.commit()
    conn.close()

    print("✅ Pedido gravado no banco de dados com sucesso!")
    return {"sucesso": True, "dados": dados}