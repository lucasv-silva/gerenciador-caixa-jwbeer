import flet as ft
import sqlite3
from datetime import datetime

# --- BANCO DE DADOS (SQLite) ---
def init_db():
    conn = sqlite3.connect("caixa_jwbeer.db")
    cursor = conn.cursor()
    
    # Tabela de Produtos no Estoque/Vitrine
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            preco REAL,
            imagem_url TEXT
        )
    """)
    
    # Tabela de Pedidos/Entregas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT,
            cliente_endereco TEXT,
            itens TEXT,
            total REAL,
            valor_pago REAL,
            troco REAL,
            status TEXT
        )
    """)
    
    # Inserir alguns produtos de teste se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone()[0] == 0:
        produtos_iniciais = [
            ("Skol Pilsen 350ml", 4.50, "https://images.unsplash.com/photo-1608270586620-248524c67de9?w=200"),
            ("Heineken Long Neck 330ml", 8.50, "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=200"),
            ("Cachaça 51 965ml", 18.00, "https://images.unsplash.com/photo-1527281400683-1aae777175f8?w=200"),
            ("Eisenbahn Unfiltered 350ml", 6.00, "https://images.unsplash.com/photo-1535958636474-b021ee887b13?w=200")
        ]
        cursor.executemany("INSERT INTO produtos (nome, preco, imagem_url) VALUES (?, ?, ?)", produtos_iniciais)
        
    conn.commit()
    conn.close()

def buscar_produtos_db():
    conn = sqlite3.connect("caixa_jwbeer.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, preco, imagem_url FROM produtos")
    produtos = cursor.fetchall()
    conn.close()
    return produtos

def criar_pedido_db(endereco, itens, total, valor_pago, troco):
    conn = sqlite3.connect("caixa_jwbeer.db")
    cursor = conn.cursor()
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute("""
        INSERT INTO pedidos (data_hora, cliente_endereco, itens, total, valor_pago, troco, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Pendente')
    """, (data_hora, endereco, itens, total, valor_pago, troco))
    conn.commit()
    conn.close()

def buscar_pedidos_db():
    conn = sqlite3.connect("caixa_jwbeer.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, data_hora, cliente_endereco, itens, total, valor_pago, troco, status FROM pedidos ORDER BY id DESC")
    pedidos = cursor.fetchall()
    conn.close()
    return pedidos

def concluir_pedido_db(pedido_id):
    conn = sqlite3.connect("caixa_jwbeer.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE pedidos SET status = 'Entregue' WHERE id = ?", (pedido_id,))
    conn.commit()
    conn.close()

def calcular_total_caixa_db():
    conn = sqlite3.connect("caixa_jwbeer.db")
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total) FROM pedidos WHERE status = 'Entregue'")
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0.0

# --- INTERFACE GRÁFICA (Flet) ---
def main(page: ft.Page):
    init_db()

    page.title = "SISTEMA JW BEER - PDV & Entregas"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # Estado do Carrinho Local
    carrinho = []

    # Componentes de Controle de Pedido
    endereco_input = ft.TextField(label="Endereço de Entrega", hint_text="Ex: Rua Central, 123", expand=True)
    valor_pago_input = ft.TextField(label="Valor Pago pelo Cliente (R$)", hint_text="Ex: 50.00", width=220, keyboard_type=ft.KeyboardType.NUMBER)
    txt_troco = ft.Text("Troco: R$ 0,00", size=16, weight="bold", color=ft.Colors.AMBER)
    txt_total_carrinho = ft.Text("Subtotal: R$ 0,00", size=18, weight="bold", color=ft.Colors.GREEN_400)
    
    # Containers Visuais
    grid_produtos = ft.Row(wrap=True, spacing=15)
    lista_carrinho_view = ft.Column(spacing=5)
    lista_entregas_view = ft.Column(spacing=10)
    txt_total_caixa = ft.Text("R$ 0,00", size=24, weight="bold", color=ft.Colors.GREEN_400)

    def atualizar_carrinho_ui():
        lista_carrinho_view.controls.clear()
        subtotal = sum(p['preco'] for p in carrinho)
        txt_total_carrinho.value = f"Subtotal: R$ {subtotal:.2f}".replace('.', ',')
        
        # Calcular Troco
        try:
            pago = float(valor_pago_input.value.replace(',', '.')) if valor_pago_input.value else 0.0
            troco = pago - subtotal if pago >= subtotal else 0.0
            txt_troco.value = f"Troco: R$ {troco:.2f}".replace('.', ',')
        except ValueError:
            txt_troco.value = "Troco: Valor inválido"

        for item in carrinho:
            lista_carrinho_view.controls.append(
                ft.Row([
                    ft.Text(f"1x {item['nome']}", weight="bold"),
                    ft.Text(f"R$ {item['preco']:.2f}".replace('.', ','), color=ft.Colors.AMBER)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )
        page.update()

    def adicionar_ao_carrinho(produto):
        carrinho.append(produto)
        atualizar_carrinho_ui()

    def valor_pago_changed(e):
        atualizar_carrinho_ui()

    valor_pago_input.on_change = valor_pago_changed

    def finalizar_pedido_clique(e):
        if not carrinho:
            page.snack_bar = ft.SnackBar(ft.Text("O carrinho está vazio!"), open=True)
            page.update()
            return

        subtotal = sum(p['preco'] for p in carrinho)
        try:
            pago = float(valor_pago_input.value.replace(',', '.')) if valor_pago_input.value else subtotal
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Digite um valor numérico válido para o pagamento!"), open=True)
            page.update()
            return

        if pago < subtotal:
            page.snack_bar = ft.SnackBar(ft.Text("O valor pago é menor que o total do pedido!"), open=True)
            page.update()
            return

        troco = pago - subtotal
        itens_str = ", ".join([p['nome'] for p in carrinho])
        end = endereco_input.value if endereco_input.value else "Retirada no Balcão"

        criar_pedido_db(end, itens_str, subtotal, pago, troco)
        
        carrinho.clear()
        endereco_input.value = ""
        valor_pago_input.value = ""
        
        page.snack_bar = ft.SnackBar(ft.Text("Pedido gerado com sucesso!"), open=True)
        recarregar_tela()

    def marcar_entregue(pedido_id):
        concluir_pedido_db(pedido_id)
        page.snack_bar = ft.SnackBar(ft.Text("Entrega concluída e valor adicionado ao Caixa!"), open=True)
        recarregar_tela()

    def recarregar_tela():
        # 1. Carregar produtos na vitrine
        grid_produtos.controls.clear()
        produtos = buscar_produtos_db()
        for prod in produtos:
            p_dict = {"id": prod[0], "nome": prod[1], "preco": prod[2], "imagem": prod[3]}
            grid_produtos.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Image(
                            src=prod[3], 
                            width=130, 
                            height=90, 
                            fit="cover", 
                            border_radius=8,
                            error_content=ft.Icon(ft.Icons.LOCAL_DRINK, size=50, color=ft.Colors.AMBER)
                        ),
                        ft.Text(prod[1], size=13, weight="bold", text_align=ft.TextAlign.CENTER, max_lines=2),
                        ft.Text(f"R$ {prod[2]:.2f}".replace('.', ','), size=14, color=ft.Colors.AMBER_400, weight="bold"),
                        ft.ElevatedButton(
                            "+ ADICIONAR",
                            icon=ft.Icons.ADD_SHOPPING_CART,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER, color=ft.Colors.BLACK),
                            on_click=lambda e, p=p_dict: adicionar_ao_carrinho(p)
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=10,
                    width=170,
                    bgcolor=ft.Colors.GREY_900,
                    border_radius=10,
                    border=ft.border.all(1, ft.Colors.GREY_800)
                )
            )

        # 2. Carregar Pedidos
        lista_entregas_view.controls.clear()
        pedidos = buscar_pedidos_db()
        for ped in pedidos:
            pid, data_h, end, itens, tot, pago, troco, st = ped
            
            is_entregue = st == "Entregue"
            cor_status = ft.Colors.GREEN_400 if is_entregue else ft.Colors.ORANGE_400

            btn_ok = ft.IconButton(
                icon=ft.Icons.CHECK_CIRCLE,
                icon_color=ft.Colors.GREEN,
                icon_size=32,
                tooltip="Marcar como Entregue",
                on_click=lambda e, id_ped=pid: marcar_entregue(id_ped),
                disabled=is_entregue
            )

            lista_entregas_view.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Row([
                                    ft.Text(f"Pedido #{pid}", weight="bold", size=16),
                                    ft.Text(f"[{st}]", color=cor_status, weight="bold"),
                                    ft.Text(data_h, color=ft.Colors.GREY_400, size=12),
                                ]),
                                ft.Text(f"Local: {end}", weight="bold", color=ft.Colors.AMBER),
                                ft.Text(f"Itens: {itens}", size=13),
                                ft.Text(f"Total: R$ {tot:.2f} | Pago: R$ {pago:.2f} | Troco: R$ {troco:.2f}".replace('.', ','), size=13, weight="bold")
                            ], expand=True),
                            btn_ok
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=15,
                        bgcolor=ft.Colors.GREY_900 if not is_entregue else ft.Colors.GREY_950,
                        border_radius=10
                    )
                )
            )

        # 3. Atualizar Total do Caixa
        tot_caixa = calcular_total_caixa_db()
        txt_total_caixa.value = f"R$ {tot_caixa:.2f}".replace('.', ',')

        atualizar_carrinho_ui()

    # Layout Principal
    page.add(
        ft.Row([
            ft.Icon(ft.Icons.LOCAL_BAR, color=ft.Colors.AMBER, size=32),
            ft.Text("JW BEER - PAINEL DE VENDAS & ENTREGAS", size=22, weight="bold"),
        ], alignment=ft.MainAxisAlignment.CENTER),
        
        ft.Divider(height=15),

        ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.Text("SALDO ATUAL EM CAIXA (CONFIRMADO):", size=14, weight="bold"),
                    txt_total_caixa
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=15,
                bgcolor=ft.Colors.GREY_900,
                border_radius=10
            )
        ),

        ft.Divider(height=15, color=ft.Colors.TRANSPARENT),

        ft.Text("🍺 Catálogo de Bebidas (Clique no + para adicionar)", size=18, weight="bold"),
        grid_produtos,

        ft.Divider(height=20),

        ft.Text("🛒 Comanda / Novo Pedido", size=18, weight="bold"),
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    lista_carrinho_view,
                    ft.Divider(),
                    txt_total_carrinho,
                    ft.Row([endereco_input, valor_pago_input]),
                    ft.Row([
                        txt_troco,
                        ft.ElevatedButton(
                            "CONFIRMAR E DISPARAR PEDIDO",
                            icon=ft.Icons.SEND,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER, color=ft.Colors.BLACK, padding=15),
                            on_click=finalizar_pedido_clique
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ]),
                padding=15,
                bgcolor=ft.Colors.GREY_900,
                border_radius=10
            )
        ),

        ft.Divider(height=20),

        ft.Text("🛵 Painel de Entregas & Status", size=18, weight="bold"),
        lista_entregas_view
    )

    recarregar_tela()

ft.app(target=main, view=ft.AppView.WEB_BROWSER)