import sqlite3
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify, render_template_string, redirect, url_for

app = Flask(__name__)

# Fuso horário de Brasília (UTC-3)
fuso_br = timezone(timedelta(hours=-3))

def inicializar_banco():
    try:
        conn = sqlite3.connect('caixa_jwbeer.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT,
                nome_cliente TEXT,
                cliente_endereco TEXT,
                localizacao_maps TEXT,
                itens TEXT,
                valor_total REAL,
                forma_pagamento TEXT,
                status TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print("Erro ao inicializar banco:", e)

inicializar_banco()

# ----------------------------------------------------
# 1. CARDÁPIO DIGITAL DINÂMICO COM FOTOS E GPS (/)
# ----------------------------------------------------
@app.route("/", methods=["GET"])
def loja():
    html_loja = '''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JW BEER - Cardápio Digital</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }
            body { background: #121212; color: #fff; padding-bottom: 110px; }
            header { background: #1e1e1e; padding: 15px; text-align: center; border-bottom: 2px solid #f39c12; position: sticky; top: 0; z-index: 100; }
            h1 { color: #f39c12; font-size: 22px; }
            p.sub { color: #aaa; font-size: 13px; }
            
            .container { padding: 15px; max-width: 600px; margin: 0 auto; }
            .categoria-titulo { color: #f39c12; margin: 25px 0 12px 0; font-size: 18px; border-bottom: 1px solid #333; padding-bottom: 5px; text-transform: uppercase; letter-spacing: 0.5px; }
            
            /* Card com Foto */
            .produto-card { background: #1e1e1e; padding: 12px; border-radius: 10px; margin-bottom: 12px; display: flex; align-items: center; gap: 12px; border: 1px solid #2a2a2a; }
            .prod-img { width: 65px; height: 65px; border-radius: 8px; object-fit: cover; background: #2a2a2a; flex-shrink: 0; }
            .prod-info { flex: 1; }
            .prod-nome { font-weight: bold; font-size: 15px; color: #fff; }
            .prod-preco { color: #27ae60; font-size: 14px; margin-top: 4px; font-weight: bold; }
            
            .qtd-controls { display: flex; align-items: center; gap: 8px; }
            .btn-qtd { background: #2a2a2a; color: #f39c12; border: 1px solid #f39c12; width: 32px; height: 32px; border-radius: 6px; font-weight: bold; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
            .btn-qtd:active { background: #f39c12; color: #121212; }
            .qtd-num { font-size: 16px; font-weight: bold; min-width: 20px; text-align: center; }
            
            /* Formulário de Entrega */
            .box-entrega { background: #1e1e1e; padding: 15px; border-radius: 8px; margin-top: 25px; border: 1px solid #333; }
            .input-field { width: 100%; padding: 10px; margin-top: 8px; margin-bottom: 12px; border-radius: 6px; border: 1px solid #444; background: #2a2a2a; color: #fff; font-size: 14px; }
            
            /* Rodapé Fixo */
            .bar-carrinho { position: fixed; bottom: 0; left: 0; right: 0; background: #1e1e1e; padding: 12px 20px; border-top: 2px solid #27ae60; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 -4px 10px rgba(0,0,0,0.5); z-index: 99; }
            .total-texto { font-size: 13px; color: #aaa; }
            .total-valor { font-size: 20px; color: #27ae60; font-weight: bold; }
            .btn-enviar { background: #27ae60; color: #fff; border: none; padding: 12px 18px; border-radius: 8px; font-weight: bold; font-size: 14px; cursor: pointer; }
        </style>
    </head>
    <body>
        <header>
            <h1>🍺 JW BEER</h1>
            <p class="sub">Faça seu pedido online rápido e fácil</p>
        </header>

        <div class="container">
            <form id="formPedido" method="POST" action="/fazer_pedido">
                <input type="hidden" name="itens_json" id="itens_json">
                <input type="hidden" name="total_final" id="total_final">
                <input type="hidden" name="localizacao_maps" id="localizacao_maps">

                <!-- Área onde os produtos e categorias serão gerados automaticamente -->
                <div id="lista-produtos"></div>

                <div class="box-entrega">
                    <label style="font-size: 14px; font-weight: bold; color: #f39c12;">Seus Dados:</label>
                    <input type="text" name="nome" class="input-field" placeholder="Seu Nome completo" required>
                    <input type="text" name="endereco" class="input-field" placeholder="Endereço / Ponto de Referência" required>
                    <select name="pagamento" class="input-field" required>
                        <option value="Pix">Pagamento: Pix</option>
                        <option value="Cartão">Pagamento: Cartão</option>
                        <option value="Dinheiro">Pagamento: Dinheiro</option>
                    </select>
                </div>
            </form>
        </div>

        <div class="bar-carrinho">
            <div>
                <div class="total-texto">Total:</div>
                <div class="total-valor" id="display_total">R$ 0,00</div>
            </div>
            <button type="button" class="btn-enviar" onclick="solicitarLocalizacaoEEnviar()">Enviar p/ WhatsApp 🚀</button>
        </div>

        <script>
            // CATÁLOGO COMPLETO COM IMAGENS, NOME E PREÇO
            const CATALOGO = [
                {
                    categoria: "🍺 Cervejas",
                    produtos: [
                        { id: 1, nome: "Caixa Heineken Long Neck", preco: 50.00, foto: "https://images.unsplash.com/photo-1608270586620-248524c67de9?w=150" },
                        { id: 2, nome: "Fardo Skol Pilsen Lata", preco: 38.00, foto: "https://images.unsplash.com/photo-1535958636474-b021ee887b13?w=150" },
                        { id: 3, name: "Eisenbahn Long Neck (Caixa)", preco: 48.00, foto: "https://images.unsplash.com/photo-1567696911980-2eed69a46042?w=150" }
                    ]
                },
                {
                    categoria: "🥃 Destilados & Cachaças",
                    produtos: [
                        { id: 4, nome: "Cachaça 51 (965ml)", preco: 18.50, foto: "https://images.unsplash.com/photo-1527281400683-1aae777175f8?w=150" },
                        { id: 5, nome: "Whisky Red Label 1L", preco: 89.90, foto: "https://images.unsplash.com/photo-1527281400683-1aae777175f8?w=150" }
                    ]
                },
                {
                    categoria: "🥤 Refrigerantes & Não Alcoólicos",
                    produtos: [
                        { id: 6, nome: "Guaraná Iara 2L", preco: 7.50, foto: "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=150" },
                        { id: 7, nome: "H2OH! Limão 500ml", preco: 5.50, foto: "https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=150" },
                        { id: 8, nome: "Água de Coco 1L", preco: 8.00, foto: "https://images.unsplash.com/photo-1525385133512-2f3bdd039054?w=150" }
                    ]
                }
            ];

            let carrinho = {};
            let totalGeral = 0;

            // Renderiza o catálogo na tela
            function carregarProdutos() {
                const container = document.getElementById('lista-produtos');
                let html = "";

                CATALOGO.forEach(cat => {
                    html += `<div class="categoria-titulo">${cat.categoria}</div>`;
                    cat.produtos.forEach(prod => {
                        carrinho[prod.nome] = { qtd: 0, preco: prod.preco };
                        html += `
                            <div class="produto-card">
                                <img src="${prod.foto}" class="prod-img" alt="${prod.nome}">
                                <div class="prod-info">
                                    <div class="prod-nome">${prod.nome}</div>
                                    <div class="prod-preco">R$ ${prod.preco.toFixed(2).replace('.', ',')}</div>
                                </div>
                                <div class="qtd-controls">
                                    <button type="button" class="btn-qtd" onclick="alterarQtd('${prod.nome}', -1)">-</button>
                                    <span class="qtd-num" id="qtd_${prod.nome}">0</span>
                                    <button type="button" class="btn-qtd" onclick="alterarQtd('${prod.nome}', 1)">+</button>
                                </div>
                            </div>
                        `;
                    });
                });

                container.innerHTML = html;
            }

            function alterarQtd(nome, delta) {
                if (carrinho[nome]) {
                    carrinho[nome].qtd += delta;
                    if (carrinho[nome].qtd < 0) carrinho[nome].qtd = 0;
                    document.getElementById('qtd_' + nome).innerText = carrinho[nome].qtd;
                    recalcularTotal();
                }
            }

            function recalcularTotal() {
                totalGeral = 0;
                for (let prod in carrinho) {
                    totalGeral += carrinho[prod].qtd * carrinho[prod].preco;
                }
                document.getElementById('display_total').innerText = 'R$ ' + totalGeral.toFixed(2).replace('.', ',');
            }

            function solicitarLocalizacaoEEnviar() {
                let temItem = false;
                for (let prod in carrinho) {
                    if (carrinho[prod].qtd > 0) temItem = true;
                }

                if (!temItem) {
                    alert("Selecione pelo menos um item!");
                    return;
                }

                let nome = document.querySelector('input[name="nome"]').value;
                let endereco = document.querySelector('input[name="endereco"]').value;

                if (!nome || !endereco) {
                    alert("Por favor, informe seu Nome e Endereço!");
                    return;
                }

                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        (position) => {
                            let lat = position.coords.latitude;
                            let lon = position.coords.longitude;
                            let linkMaps = "https://maps.google.com/?q=" + lat + "," + lon;
                            processarEEnviar(linkMaps);
                        },
                        (error) => {
                            processarEEnviar("Apenas Endereço digitado");
                        }
                    );
                } else {
                    processarEEnviar("Navegador sem suporte a GPS");
                }
            }

            function processarEEnviar(linkMaps) {
                let nome = document.querySelector('input[name="nome"]').value;
                let endereco = document.querySelector('input[name="endereco"]').value;
                let pagamento = document.querySelector('select[name="pagamento"]').value;

                let resumoTexto = "";
                let itensValidos = {};
                for (let prod in carrinho) {
                    if (carrinho[prod].qtd > 0) {
                        itensValidos[prod] = carrinho[prod].qtd;
                        resumoTexto += carrinho[prod].qtd + "x " + prod + "%0A";
                    }
                }

                document.getElementById('itens_json').value = JSON.stringify(itensValidos);
                document.getElementById('total_final').value = totalGeral;
                document.getElementById('localizacao_maps').value = linkMaps;

                let foneSeuWhatsApp = "5584999999999"; // ALTERE PARA O SEU NÚMERO COM DDD

                let msgWhats = "🍺 *NOVO PEDIDO - JW BEER*%0A%0A" +
                               "👤 *Cliente:* " + encodeURIComponent(nome) + "%0A" +
                               "📍 *Endereço:* " + encodeURIComponent(endereco) + "%0A" +
                               "💳 *Pagamento:* " + encodeURIComponent(pagamento) + "%0A%0A" +
                               "📦 *Itens:*%0A" + resumoTexto + "%0A" +
                               "💰 *Total:* R$ " + totalGeral.toFixed(2).replace('.', ',') + "%0A%0A" +
                               "📍 *Localização GPS:* " + encodeURIComponent(linkMaps);

                document.getElementById('formPedido').submit();
                window.open("https://wa.me/" + foneSeuWhatsApp + "?text=" + msgWhats, "_blank");
            }

            // Inicializa a renderização
            carregarProdutos();
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_loja)

# ----------------------------------------------------
# 2. PROCESSAMENTO DO PEDIDO (/fazer_pedido)
# ----------------------------------------------------
@app.route("/fazer_pedido", methods=["POST"])
def fazer_pedido():
    try:
        nome = request.form.get("nome")
        endereco = request.form.get("endereco")
        localizacao_maps = request.form.get("localizacao_maps")
        pagamento = request.form.get("pagamento")
        itens_json = request.form.get("itens_json")
        total = float(request.form.get("total_final") or 0.0)

        data_hora = datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M')

        conn = sqlite3.connect('caixa_jwbeer.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO vendas (data_hora, nome_cliente, cliente_endereco, localizacao_maps, itens, valor_total, forma_pagamento, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Pendente')
        ''', (data_hora, nome, endereco, localizacao_maps, itens_json, total, pagamento))
        conn.commit()
        conn.close()

    except Exception as e:
        print("Erro ao gravar venda:", e)

    return redirect(url_for('loja'))

# ----------------------------------------------------
# 3. PAINEL DE CONTROLE DA LOJA (/painel)
# ----------------------------------------------------
@app.route("/painel", methods=["GET"])
def painel():
    try:
        conn = sqlite3.connect('caixa_jwbeer.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, data_hora, nome_cliente, cliente_endereco, localizacao_maps, itens, valor_total, forma_pagamento, status FROM vendas ORDER BY id DESC LIMIT 20")
        registros = cursor.fetchall()
        
        cursor.execute("SELECT SUM(valor_total) FROM vendas")
        total_faturado = cursor.fetchone()[0] or 0.0
        conn.close()
    except Exception as e:
        print("Erro no painel:", e)
        registros, total_faturado = [], 0.0

    html_painel = '''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JW BEER - Painel</title>
        <meta http-equiv="refresh" content="5">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }
            body { background: #121212; color: #fff; padding: 15px; }
            h1 { color: #f39c12; text-align: center; font-size: 22px; }
            .status { text-align: center; color: #27ae60; font-size: 13px; margin: 5px 0 15px 0; }
            
            .summary { display: flex; gap: 10px; margin-bottom: 20px; }
            .box { flex: 1; background: #1e1e1e; padding: 12px; border-radius: 8px; border: 1px solid #333; text-align: center; }
            .box-title { font-size: 11px; color: #aaa; text-transform: uppercase; }
            .box-value { font-size: 18px; font-weight: bold; color: #27ae60; margin-top: 4px; }
            
            .card { background: #1e1e1e; padding: 15px; margin-bottom: 12px; border-radius: 10px; border-left: 5px solid #f39c12; }
            .card-top { display: flex; justify-content: space-between; border-bottom: 1px solid #2a2a2a; padding-bottom: 8px; margin-bottom: 8px; }
            .cliente { font-weight: bold; color: #f39c12; font-size: 15px; }
            .hora { font-size: 12px; color: #888; }
            .info { margin: 5px 0; font-size: 14px; color: #ddd; }
            .link-maps { color: #3498db; text-decoration: none; font-weight: bold; }
            .total { font-weight: bold; color: #27ae60; text-align: right; font-size: 16px; margin-top: 5px; }
        </style>
    </head>
    <body>
        <h1>🍺 JW BEER - Painel de Controle</h1>
        <div class="status">🟢 Servidor On-line | Atualização em tempo real</div>

        <div class="summary">
            <div class="box">
                <div class="box-title">Pedidos</div>
                <div class="box-value">{{ registros|length }}</div>
            </div>
            <div class="box">
                <div class="box-title">Faturamento</div>
                <div class="box-value">R$ {{ "%.2f"|format(total_faturado) }}</div>
            </div>
        </div>

        <div>
            {% for item in registros %}
                <div class="card">
                    <div class="card-top">
                        <span class="cliente">👤 {{ item[2] }}</span>
                        <span class="hora">🕒 {{ item[1] }}</span>
                    </div>
                    <div class="info">📍 <strong>Endereço:</strong> {{ item[3] }}</div>
                    {% if 'http' in item[4] %}
                        <div class="info">🗺️ <strong>GPS:</strong> <a href="{{ item[4] }}" target="_blank" class="link-maps">Abrir no Google Maps ↗</a></div>
                    {% endif %}
                    <div class="info">💳 <strong>Pagamento:</strong> {{ item[7] }}</div>
                    <div class="info">📦 <strong>Itens:</strong> {{ item[5] }}</div>
                    <div class="total">R$ {{ "%.2f"|format(item[6]) }}</div>
                </div>
            {% else %}
                <p style="text-align: center; color: #888; margin-top: 40px;">Nenhum pedido registrado ainda.</p>
            {% endfor %}
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_painel, registros=registros, total_faturado=total_faturado)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)