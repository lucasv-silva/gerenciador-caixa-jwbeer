import sqlite3
import json
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify, render_template_string, redirect, url_for

app = Flask(__name__)

# Fuso horário de Brasília (UTC-3)
fuso_br = timezone(timedelta(hours=-3))

def inicializar_banco():
    try:
        conn = sqlite3.connect('caixa_jwbeer.db')
        cursor = conn.cursor()
        
        # Tabela de Vendas / Pedidos
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
        
        # Tabela de Produtos do Catálogo
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria TEXT,
                nome TEXT,
                preco REAL,
                foto TEXT
            )
        ''')
        
        # Inserir produtos padrão caso a tabela esteja vazia
        cursor.execute("SELECT COUNT(*) FROM produtos")
        if cursor.fetchone()[0] == 0:
            produtos_iniciais = [
                ("🍺 Cervejas", "Caixa Heineken Long Neck", 50.00, "https://images.unsplash.com/photo-1608270586620-248524c67de9?w=150"),
                ("🍺 Cervejas", "Fardo Skol Pilsen Lata", 38.00, "https://images.unsplash.com/photo-1535958636474-b021ee887b13?w=150"),
                ("🥃 Destilados & Cachaças", "Cachaça 51 (965ml)", 18.50, "https://images.unsplash.com/photo-1527281400683-1aae777175f8?w=150"),
                ("🥤 Refrigerantes & Sem Álcool", "Guaraná Iara 2L", 7.50, "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=150")
            ]
            cursor.executemany("INSERT INTO produtos (categoria, nome, preco, foto) VALUES (?, ?, ?, ?)", produtos_iniciais)
            
        conn.commit()
        conn.close()
    except Exception as e:
        print("Erro ao inicializar banco:", e)

inicializar_banco()

# ----------------------------------------------------
# 1. ROTA PÚBLICA: CARDÁPIO DIGITAL DILÂMICO (/)
# ----------------------------------------------------
@app.route("/", methods=["GET"])
def loja():
    # Buscar produtos do banco
    conn = sqlite3.connect('caixa_jwbeer.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, categoria, nome, preco, foto FROM produtos ORDER BY categoria, id")
    produtos_db = cursor.fetchall()
    conn.close()

    # Organizar produtos por categoria para o JS
    catalogo_dict = {}
    for p in produtos_db:
        cat = p[1]
        if cat not in catalogo_dict:
            catalogo_dict[cat] = []
        catalogo_dict[cat].append({"id": p[0], "nome": p[2], "preco": p[3], "foto": p[4]})

    catalogo_json = json.dumps(catalogo_dict)

    html_loja = f'''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JW BEER - Cardápio Digital</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }}
            body {{ background: #121212; color: #fff; padding-bottom: 120px; }}
            header {{ background: #1e1e1e; padding: 15px; text-align: center; border-bottom: 2px solid #f39c12; position: sticky; top: 0; z-index: 100; }}
            h1 {{ color: #f39c12; font-size: 22px; }}
            p.sub {{ color: #aaa; font-size: 13px; }}
            
            .container {{ padding: 15px; max-width: 600px; margin: 0 auto; }}
            .categoria-titulo {{ color: #f39c12; margin: 25px 0 12px 0; font-size: 18px; border-bottom: 1px solid #333; padding-bottom: 5px; text-transform: uppercase; letter-spacing: 0.5px; }}
            
            /* Card do Produto */
            .produto-card {{ background: #1e1e1e; padding: 12px; border-radius: 10px; margin-bottom: 12px; display: flex; align-items: center; gap: 12px; border: 1px solid #2a2a2a; }}
            .prod-img {{ width: 65px; height: 65px; border-radius: 8px; object-fit: cover; background: #2a2a2a; flex-shrink: 0; }}
            .prod-info {{ flex: 1; }}
            .prod-nome {{ font-weight: bold; font-size: 15px; color: #fff; }}
            .prod-preco {{ color: #27ae60; font-size: 14px; margin-top: 4px; font-weight: bold; }}
            
            .qtd-controls {{ display: flex; align-items: center; gap: 8px; }}
            .btn-qtd {{ background: #2a2a2a; color: #f39c12; border: 1px solid #f39c12; width: 32px; height: 32px; border-radius: 6px; font-weight: bold; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; }}
            .btn-qtd:active {{ background: #f39c12; color: #121212; }}
            .qtd-num {{ font-size: 16px; font-weight: bold; min-width: 20px; text-align: center; }}
            
            /* Botão de Adicionar Novo Item */
            .btn-add-novo {{ width: 100%; background: #f39c12; color: #121212; border: none; padding: 14px; border-radius: 10px; font-weight: bold; font-size: 15px; margin-top: 15px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; }}
            .box-cadastrar {{ background: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #f39c12; margin-top: 15px; display: none; }}
            
            /* Form Entrega & Inputs */
            .box-entrega {{ background: #1e1e1e; padding: 15px; border-radius: 10px; margin-top: 25px; border: 1px solid #333; }}
            .input-field {{ width: 100%; padding: 10px; margin-top: 6px; margin-bottom: 12px; border-radius: 6px; border: 1px solid #444; background: #2a2a2a; color: #fff; font-size: 14px; }}
            
            /* Rodapé Fixo */
            .bar-carrinho {{ position: fixed; bottom: 0; left: 0; right: 0; background: #1e1e1e; padding: 12px 20px; border-top: 2px solid #27ae60; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 -4px 10px rgba(0,0,0,0.5); z-index: 99; }}
            .total-texto {{ font-size: 13px; color: #aaa; }}
            .total-valor {{ font-size: 20px; color: #27ae60; font-weight: bold; }}
            .btn-enviar {{ background: #27ae60; color: #fff; border: none; padding: 12px 18px; border-radius: 8px; font-weight: bold; font-size: 14px; cursor: pointer; }}
        </style>
    </head>
    <body>
        <header>
            <h1>🍺 JW BEER</h1>
            <p class="sub">Faça seu pedido online rápido e fácil</p>
        </header>

        <div class="container">
            <!-- BOTÃO GRANDE PARA CADASTRAR NOVO PRODUTO -->
            <button type="button" class="btn-add-novo" onclick="toggleFormCadastro()">
                ➕ Adicionar Novo Produto ao Catálogo
            </button>

            <!-- FORMULÁRIO DE CADASTRO DE NOVO ITEM -->
            <div id="boxCadastrar" class="box-cadastrar">
                <h3 style="color: #f39c12; margin-bottom: 10px; font-size: 16px;">Cadastrar Novo Item</h3>
                <form method="POST" action="/adicionar_produto">
                    <label style="font-size: 12px; color: #aaa;">Categoria:</label>
                    <select name="categoria" class="input-field" required>
                        <option value="🍺 Cervejas">🍺 Cervejas</option>
                        <option value="🥃 Destilados & Cachaças">🥃 Destilados & Cachaças</option>
                        <option value="🥤 Refrigerantes & Sem Álcool">🥤 Refrigerantes & Sem Álcool</option>
                        <option value="🍿 Petiscos & Outros">🍿 Petiscos & Outros</option>
                    </select>

                    <label style="font-size: 12px; color: #aaa;">Nome do Produto:</label>
                    <input type="text" name="nome" class="input-field" placeholder="Ex: Heineken 600ml" required>

                    <label style="font-size: 12px; color: #aaa;">Preço (R$):</label>
                    <input type="number" step="0.01" name="preco" class="input-field" placeholder="Ex: 12.50" required>

                    <label style="font-size: 12px; color: #aaa;">Link/URL da Foto:</label>
                    <input type="url" name="foto" class="input-field" placeholder="https://site.com/foto.jpg" required>

                    <button type="submit" style="width: 100%; background: #27ae60; color: #fff; border: none; padding: 10px; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 5px;">
                        Salvar Produto
                    </button>
                </form>
            </div>

            <!-- FORMULÁRIO DO PEDIDO DO CLIENTE -->
            <form id="formPedido" method="POST" action="/fazer_pedido">
                <input type="hidden" name="itens_json" id="itens_json">
                <input type="hidden" name="total_final" id="total_final">
                <input type="hidden" name="localizacao_maps" id="localizacao_maps">

                <div id="lista-produtos"></div>

                <div class="box-entrega">
                    <label style="font-size: 14px; font-weight: bold; color: #f39c12;">Seus Dados:</label>
                    <input type="text" name="nome" class="input-field" placeholder="Seu Nome completo" required>
                    <input type="text" name="endereco" class="input-field" placeholder="Endereço / Ponto de Referência" required>
                    
                    <label style="font-size: 14px; font-weight: bold; color: #f39c12;">Forma de Pagamento:</label>
                    <select name="pagamento" id="selectPagamento" class="input-field" onchange="verificarPix()" required>
                        <option value="Pix">Pix</option>
                        <option value="Cartão">Cartão (na entrega)</option>
                        <option value="Dinheiro">Dinheiro (na entrega)</option>
                    </select>

                    <!-- CAIXA DA CHAVE PIX COM BOTÃO DE COPIAR -->
                    <div id="boxPix" style="background: #2a2a2a; padding: 12px; border-radius: 8px; border: 1px solid #f39c12; margin-bottom: 12px; text-align: center;">
                        <div style="font-size: 12px; color: #aaa;">Chave Pix do Estabelecimento:</div>
                        <div id="chavePixTexto" style="font-weight: bold; color: #27ae60; margin: 6px 0; font-size: 15px;">suachavepix@email.com</div>
                        <button type="button" onclick="copiarPix()" style="background: #f39c12; color: #121212; border: none; padding: 8px 14px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px;">
                            📋 Copiar Chave Pix
                        </button>
                    </div>
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
            const CATALOGO = {catalogo_json};
            let carrinho = {{}};
            let totalGeral = 0;

            function carregarProdutos() {{
                const container = document.getElementById('lista-produtos');
                let html = "";

                for (let cat in CATALOGO) {{
                    html += `<div class="categoria-titulo">${{cat}}</div>`;
                    CATALOGO[cat].forEach(prod => {{
                        carrinho[prod.nome] = {{ qtd: 0, preco: prod.preco }};
                        html += `
                            <div class="produto-card">
                                <img src="${{prod.foto}}" class="prod-img" alt="${{prod.nome}}" onerror="this.src='https://via.placeholder.com/150/2a2a2a/ffffff?text=JW+Beer'">
                                <div class="prod-info">
                                    <div class="prod-nome">${{prod.nome}}</div>
                                    <div class="prod-preco">R$ ${{prod.preco.toFixed(2).replace('.', ',')}}</div>
                                </div>
                                <div class="qtd-controls">
                                    <button type="button" class="btn-qtd" onclick="alterarQtd('${{prod.nome}}', -1)">-</button>
                                    <span class="qtd-num" id="qtd_${{prod.nome}}">0</span>
                                    <button type="button" class="btn-qtd" onclick="alterarQtd('${{prod.nome}}', 1)">+</button>
                                </div>
                            </div>
                        `;
                    }});
                }}

                container.innerHTML = html;
            }}

            function toggleFormCadastro() {{
                let box = document.getElementById('boxCadastrar');
                box.style.display = box.style.display === 'block' ? 'none' : 'block';
            }}

            function verificarPix() {{
                let pag = document.getElementById('selectPagamento').value;
                let box = document.getElementById('boxPix');
                box.style.display = (pag === 'Pix') ? 'block' : 'none';
            }}

            function copiarPix() {{
                let chave = document.getElementById('chavePixTexto').innerText;
                navigator.clipboard.writeText(chave);
                alert("Chave Pix copiada!");
            }}

            function alterarQtd(nome, delta) {{
                if (carrinho[nome]) {{
                    carrinho[nome].qtd += delta;
                    if (carrinho[nome].qtd < 0) carrinho[nome].qtd = 0;
                    document.getElementById('qtd_' + nome).innerText = carrinho[nome].qtd;
                    recalcularTotal();
                }}
            }}

            function recalcularTotal() {{
                totalGeral = 0;
                for (let prod in carrinho) {{
                    totalGeral += carrinho[prod].qtd * carrinho[prod].preco;
                }}
                document.getElementById('display_total').innerText = 'R$ ' + totalGeral.toFixed(2).replace('.', ',');
            }}

            function solicitarLocalizacaoEEnviar() {{
                let temItem = false;
                for (let prod in carrinho) {{
                    if (carrinho[prod].qtd > 0) temItem = true;
                }}

                if (!temItem) {{
                    alert("Selecione pelo menos um item!");
                    return;
                }}

                let nome = document.querySelector('input[name="nome"]').value;
                let endereco = document.querySelector('input[name="endereco"]').value;

                if (!nome || !endereco) {{
                    alert("Por favor, preencha Nome e Endereço!");
                    return;
                }}

                if (navigator.geolocation) {{
                    navigator.geolocation.getCurrentPosition(
                        (position) => {{
                            let lat = position.coords.latitude;
                            let lon = position.coords.longitude;
                            let linkMaps = "https://maps.google.com/?q=" + lat + "," + lon;
                            processarEEnviar(linkMaps);
                        }},
                        (error) => {{
                            processarEEnviar("Endereço sem GPS");
                        }}
                    );
                }} else {{
                    processarEEnviar("Sem suporte a GPS");
                }}
            }}

            function processarEEnviar(linkMaps) {{
                let nome = document.querySelector('input[name="nome"]').value;
                let endereco = document.querySelector('input[name="endereco"]').value;
                let pagamento = document.querySelector('select[name="pagamento"]').value;

                let resumoTexto = "";
                let itensValidos = {{}};
                for (let prod in carrinho) {{
                    if (carrinho[prod].qtd > 0) {{
                        itensValidos[prod] = carrinho[prod].qtd;
                        resumoTexto += carrinho[prod].qtd + "x " + prod + "%0A";
                    }}
                }}

                document.getElementById('itens_json').value = JSON.stringify(itensValidos);
                document.getElementById('total_final').value = totalGeral;
                document.getElementById('localizacao_maps').value = linkMaps;

                // ALTERE AQUI PARA O SEU NÚMERO DO WHATSAPP COM DDD
                let foneSeuWhatsApp = "5584999999999"; 

                let msgWhats = "🍺 *NOVO PEDIDO - JW BEER*%0A%0A" +
                               "👤 *Cliente:* " + encodeURIComponent(nome) + "%0A" +
                               "📍 *Endereço:* " + encodeURIComponent(endereco) + "%0A" +
                               "💳 *Pagamento:* " + encodeURIComponent(pagamento) + "%0A%0A" +
                               "📦 *Itens:*%0A" + resumoTexto + "%0A" +
                               "💰 *Total:* R$ " + totalGeral.toFixed(2).replace('.', ',') + "%0A%0A" +
                               "📍 *Localização GPS:* " + encodeURIComponent(linkMaps);

                document.getElementById('formPedido').submit();
                window.open("https://wa.me/" + foneSeuWhatsApp + "?text=" + msgWhats, "_blank");
            }}

            carregarProdutos();
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_loja)

# ----------------------------------------------------
# 2. ROTA PARA ADICIONAR NOVO PRODUTO (/adicionar_produto)
# ----------------------------------------------------
@app.route("/adicionar_produto", methods=["POST"])
def adicionar_produto():
    try:
        categoria = request.form.get("categoria")
        nome = request.form.get("nome")
        preco = float(request.form.get("preco") or 0.0)
        foto = request.form.get("foto")

        if categoria and nome and preco > 0 and foto:
            conn = sqlite3.connect('caixa_jwbeer.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO produtos (categoria, nome, preco, foto) VALUES (?, ?, ?, ?)", 
                           (categoria, nome, preco, foto))
            conn.commit()
            conn.close()
    except Exception as e:
        print("Erro ao cadastrar produto:", e)

    return redirect(url_for('loja'))

# ----------------------------------------------------
# 3. PROCESSAMENTO DO PEDIDO (/fazer_pedido)
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
# 4. PAINEL DE CONTROLE DA LOJA (/painel)
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