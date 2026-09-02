from flask import Flask, request, jsonify
from bot_engine import processar_pedido_whatsapp

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Nenhum dado recebido"}), 400

    # Lógica para extrair mensagem e áudio dos dados do WhatsApp
    # Adapta-se automaticamente dependendo da API usada (Z-API, Evolution API, etc.)
    texto_mensagem = data.get("body") or data.get("text", {}).get("message")
    nome_remetente = data.get("pushName") or data.get("sender", {}).get("name") or "Cliente Whats"
    url_audio = data.get("audioUrl") or data.get("mediaUrl")

    if texto_mensagem or url_audio:
        resultado = processar_pedido_whatsapp(
            texto_cliente=texto_mensagem, 
            caminho_audio=url_audio, 
            nome_whatsapp=nome_remetente
        )
        return jsonify({"status": "success", "pedido": resultado}), 200

    return jsonify({"status": "ignored", "message": "Mensagem não continha texto nem áudio válido"}), 200

if __name__ == "__main__":
    print("🚀 Servidor Webhook rodando na porta 5000...")
    app.run(host="0.0.0.0", port=5000)              