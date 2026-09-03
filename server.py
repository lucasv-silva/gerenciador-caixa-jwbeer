from flask import Flask, request, jsonify, render_template_string
from bot_engine import processar_pedido_whatsapp

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    html = '''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JW BEER - Painel</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body { font-family: sans-serif; background: #121212; color: #fff; padding: 20px; }
            h1 { color: #f39c12; text-align: center; }
            .card { background: #1e1e1e; padding: 15px; margin-bottom: 12px; border-radius: 8px; border-left: 5px solid #27ae60; }
            p { margin: 5px 0; }
        </style>
    </head>
    <body>
        <h1>🍺 JW BEER - Painel de Pedidos</h1>
        <p style="text-align: center; color: #27ae60;">🟢 Servidor Webhook Ativo e Conectado</p>
        <hr style="border-color: #333;">
        <p style="text-align: center; color: #aaa;">Os pedidos recebidos via WhatsApp aparecem aqui em tempo real!</p>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Nenhum dado recebido"}), 400

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