import flet as ft
from datetime import datetime

def main(page: ft.Page):
    page.title = "SISTEMA JW BEER - v2.5"
    page.theme_mode = ft.ThemeMode.DARK 
    page.window_width = 400
    
    produto_input = ft.TextField(label="Produto (ex: Skol)", width=350)
    valor_input = ft.TextField(label="Valor (R$)", width=350)

    def registrar_venda(e):
        if not produto_input.value or not valor_input.value:
            page.snack_bar = ft.SnackBar(ft.Text("Preencha tudo!"))
            page.snack_bar.open = True
        else:
            data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
            linha = f"{data_hora} - {produto_input.value} - R$ {valor_input.value}\n"
            with open("historico_vendas.txt", "a") as f:
                f.write(linha)
            page.snack_bar = ft.SnackBar(ft.Text("Venda Salva!"))
            page.snack_bar.open = True
            produto_input.value = ""
            valor_input.value = ""
        page.update()

    page.add(
        ft.Text("JW BEER - CAIXA", size=25, weight="bold"),
        produto_input,
        valor_input,
        ft.ElevatedButton("CONFIRMAR VENDA", on_click=registrar_venda, width=350),
        ft.ElevatedButton("SAIR", on_click=lambda _: page.window_close(), width=350)
    )

ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)