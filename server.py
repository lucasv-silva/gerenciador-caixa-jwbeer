import sqlite3
from flask import Flask, request, jsonify, render_template_string
from bot_engine import processar_pedido_whatsapp

app = Flask(__name__)

def buscar_pedidos():
    try:
        conn = sqlite3.connect('caixa_jwbeer.db')
        cursor = conn.cursor()
        
        # Busca apenas os últimos 20 pedidos válidos
        cursor.execute("SELECT id, data_hora, nome_cliente, cliente_endereco, itens, total, valor_pago, troco, status FROM pedidos ORDER BY id DESC LIMIT 20")
        registros = cursor.fetchall()
        
        # Soma o faturamento total acumulado
        cursor.execute("SELECT SUM(total) FROM pedidos")
        total_faturado = cursor.fetchone()[0] or 0.0
        
        conn.close()
        return registros, total_faturado
    except Exception as e:
        print("Erro ao ler banco:", e)
        return [], 0.0

@app.route("/", methods=["GET"])
def home():
    registros, total_faturado = buscar_pedidos()
    
    html = '''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JW BEER - Painel de Pedidos</title>
        <meta http-equiv="refresh" content="5">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, sans-serif; }
            body { background: #121212; color: #fff; padding: 15px; }
            .header { text-align: center; margin-bottom: 15px; }
            h1 { color: #f39c12; font-size: 22px; }
            .status { color: #27ae60; font-size: 13px; margin-top: 4px; }
            
            /* Indicadores no topo */
            .summary { display: flex; gap: 10px; margin-bottom: 20px; }
            .box { flex: 1; background: #1e1e1e; padding: 12px; border-radius: 8px; border: 1px solid #333; text-align: center; }
            .box-title { font-size: 11px; color: #aaa; text-transform: uppercase; }
            .box-value { font-size: 18px; font-weight: bold; color: #27ae60; margin-top: 4px; }
            
            /* Cartões organizados */
            .card { background: #1e1e1e; padding: 15px; margin-bottom: 12px; border-radius: 10px; border-left: 5px solid #f39c12; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
            .card-top { display: flex; justify-content: space-between; border-bottom: 1px solid #2a2a2a; padding-bottom: 8px; margin-bottom: 8px; }
            .cliente { font-weight: bold; color: #f39c12; font-size: 15px; }
            .hora { font-size: 12px; color: #888; }
            .info { margin: 5px 0; font-size: 14px; color: #ddd; }
            .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-top: 6px; }
            .badge-pendente { background: #d35400; color: #fff; }
            .badge-entregue { background: #27ae60; color: #fff; }
            .total { font-weight: bold; color: #27ae60; text-align: right; font-size: 16px; margin-top: 5px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🍺 JW BEER - Painel de Pedidos</h1>
            <div class="status">🟢 Servidor On-line | Atualizando a cada 5s</div>
        </div>

        <div class="summary">
            <div class="box">
                <div class="box-title">Total de Pedidos</div>
                <div class="box-value">{{ registros|length }}</div>
            </div>
            <div class="box">
                <div class="box-title">Faturamento</div>
                <div class="box-value">R$ {{ "%.2f"|format(total_faturado) }}</div>
            </div>
        </div>

        <div id="pedidos">
            {% for item in registros %}
                <div class="card">
                    <div class="card-top">
                        <span class="cliente">👤 {{ item[2] }}</span>
                        <span class="hora">🕒 {{ item[1] }}</span>
                    </div>
                    <div class="info">📍 <strong>Endereço:</strong> {{ item[3] }}</div>
                    <div class="info">📦 <strong>Pedido:</strong> {{ item[4] }}</div>
                    <div class="total">R$ {{ "%.2f"|format(item[5]) }}</div>
                    <div>
                        {% if item[8] == 'Pendente' %}
                            <span class="badge badge-pendente">⏳ Pendente</span>
                        {% else %}
                            <span class="badge badge-entregue">✅ {{ item[8] }}</span>
                        {% endif %}
                    </div>
                </div>
            {% else %}
                <p style="text-align: center; color: #888; margin-top: 40px;">Nenhum pedido registrado ainda.</p>
            {% endfor %}
        </div>
    </body>
    </html>
    '''
    return render_template_string(html, registros=registros, total_faturado=total_faturado)

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
        
        # FILTRO INTELIGENTE: Se o bot não identificou itens nem total (mensagens pessoais/spam), não salva no banco
        if isinstance(resultado, dict):
            itens = resultado.get("itens") or resultado.get("produtos")
            total = resultado.get("total") or resultado.get("valor_total")
            
            if not itens and not total:
                return jsonify({"status": "ignored", "message": "Conversa sem itens de pedido"}), 200

        return jsonify({"status": "success", "pedido": resultado}), 200

    return jsonify({"status": "ignored", "message": "Mensagem inválida"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)