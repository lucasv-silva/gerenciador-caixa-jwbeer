import sqlite3
from flask import Flask, request, jsonify, render_template_string
from bot_engine import processar_pedido_whatsapp

app = Flask(__name__)

# Busca os pedidos salvos no banco de dados
def buscar_pedidos():
    try:
        conn = sqlite3.connect('caixa_jwbeer.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, data_hora, cliente, itens, total, endereco FROM pedidos ORDER BY id DESC LIMIT 10")
        pedidos = cursor.fetchall()
        conn.close()
        return pedidos
    except Exception as e:
        print("Erro ao buscar pedidos no banco:", e)
        return []

# Página do Celular
@app.route("/", methods=["GET"])
def home():
    pedidos = buscar_pedidos()
    html = '''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JW BEER - Painel</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body { font-family: sans-serif; background: #121212; color: #fff; padding: 15px; }
            h1 { color: #f39c12; text-align: center; margin-bottom: 5px; }
            .status { text-align: center; color: #27ae60; font-size: 14px; margin-bottom: 20px; }
            .card { background: #1e1e1e; padding: 15px; margin-bottom: 12px; border-radius: 8px; border-left: 5px solid #27ae60; box-shadow: 0 2px 5px rgba(0,0,0,0.5); }
            .cliente { font-weight: bold; color: #f39c12; font-size: 16px; }
            .itens { margin: 8px 0; color: #e0e0e0; }
            .detalhes { font-size: 13px; color: #aaa; }
        </style>
    </head>
    <body>
        <h1>🍺 JW BEER - Painel de Pedidos</h1>
        <div class="status">🟢 Servidor On-line | Atualizando a cada 5s</div>
        
        <div id="pedidos">
            {% for p in pedidos %}
                <div class="card">
                    <div class="cliente">👤 {{ p[2] }}</div>
                    <div class="itens">📦 <strong>Pedido:</strong> {{ p[3] }}</div>
                    <div class="detalhes">📍 <strong>Endereço:</strong> {{ p[5] }}</div>
                    <div class="detalhes">💰 <strong>Total:</strong> R$ {{ p[4] }}</div>
                </div>
            {% else %}
                <p style="text-align: center; color: #888; margin-top: 40px;">Nenhum pedido registrado ainda.</p>
            {% endfor %}
        </div>
    </body>
    </html>
    '''
    return render_template_string(html, pedidos=pedidos)

# Entrada do WhatsApp
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