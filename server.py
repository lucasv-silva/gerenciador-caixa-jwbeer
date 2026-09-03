import sqlite3
from flask import Flask, request, jsonify, render_template_string
from bot_engine import processar_pedido_whatsapp

app = Flask(__name__)

def buscar_pedidos():
    try:
        conn = sqlite3.connect('caixa_jwbeer.db')
        cursor = conn.cursor()
        
        # Descobre quais tabelas existem no banco para evitar erro de tabela inexistente
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tabelas = [t[0] for t in cursor.fetchall()]
        
        # Define a tabela ativa
        tabela_alvo = None
        for t in ['vendas', 'pedidos', 'historico']:
            if t in tabelas:
                tabela_alvo = t
                break
                
        if not tabela_alvo:
            conn.close()
            return []

        # Busca os registros da tabela encontrada
        cursor.execute(f"SELECT * FROM {tabela_alvo} ORDER BY rowid DESC LIMIT 15")
        registros = cursor.fetchall()
        conn.close()
        return registros
    except Exception as e:
        print("Erro ao ler banco:", e)
        return []

@app.route("/", methods=["GET"])
def home():
    registros = buscar_pedidos()
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
            .card { background: #1e1e1e; padding: 15px; margin-bottom: 12px; border-radius: 8px; border-left: 5px solid #27ae60; word-wrap: break-word; }
            .dado { margin: 4px 0; color: #ddd; font-size: 14px; }
        </style>
    </head>
    <body>
        <h1>🍺 JW BEER - Painel de Pedidos</h1>
        <div class="status">🟢 Servidor On-line | Atualizando a cada 5s</div>
        
        <div id="pedidos">
            {% for item in registros %}
                <div class="card">
                    <div class="dado">📌 <strong>Registro:</strong> {{ item }}</div>
                </div>
            {% else %}
                <p style="text-align: center; color: #888; margin-top: 40px;">Nenhum registro encontrado no banco de dados.</p>
            {% endfor %}
        </div>
    </body>
    </html>
    '''
    return render_template_string(html, registros=registros)

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
    app.run(host="0.0.0.0", port=5000)