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

OPENAI_API_KEY = "SUA_CHAVE_OPENAI_AQUI"  # Insira sua chave se for usar a API da OpenAI

# ----------------------------------------------------
# 1. TRANSCRIÇÃO DE ÁUDIO (Whisper)
# ----------------------------------------------------
def transcrever_audio(caminho_arquivo_audio):
    """
    Função para transcrever áudio recebido pelo WhatsApp/sistema
    usando o modelo Whisper da OpenAI.
    """
    if not HAS_OPENAI or OPENAI_API_KEY == "SUA_CHAVE_OPENAI_AQUI":
        print("OpenAI não configurada ou biblioteca faltando.")
        return None

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
        print(f"Erro ao transcrever áudio: {e}")
        return None

# ----------------------------------------------------
# 2. MOTOR DO BOT (Processamento de Mensagens)
# ----------------------------------------------------
def processar_mensagem_bot(mensagem_texto, cliente_nome="Cliente"):
    """
    Processa mensagens de texto do cliente e gera respostas automáticas.
    """
    texto_limpo = mensagem_texto.lower().strip()

    # Respostas automáticas simples
    if any(palavra in texto_limpo for palavra in ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite"]):
        return f"Olá {cliente_nome}! Welcome ao JW BEER! 🍺\nComo posso te ajudar hoje? Digite 'cardapio' para ver nossas opções!"

    if "cardapio" in texto_limpo or "cardápio" in texto_limpo or "menu" in texto_limpo:
        return "Você pode acessar nosso cardápio completo e fazer seu pedido pelo link: https://jwbeer-api.onrender.com/"

    if "pix" in texto_limpo or "pagamento" in texto_limpo:
        return "Aceitamos Pix, Cartão e Dinheiro na entrega! 💳💵"

    # Resposta padrão caso não identifique
    return "Obrigado pela mensagem! Em instantes um de nossos atendentes irá te responder. Se preferir, veja nosso cardápio: https://jwbeer-api.onrender.com/"

if __name__ == "__main__":
    print("Bot Engine inicializado com sucesso!")