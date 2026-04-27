from datetime import datetime
import os

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def calcular_total():
    total = 0.0
    try:
        with open("historico_vendas.txt", "r") as arquivo:
            for linha in arquivo:
                # O código busca o valor depois do "R$ " e soma
                if "R$ " in linha:
                    valor_str = linha.split("R$ ")[1].strip()
                    total += float(valor_str)
        return total
    except FileNotFoundError:
        return 0.0

def menu():
    while True:
        limpar_tela()
        print("="*35)
        print("    SISTEMA JW BEER - v2.5")
        print("="*35)
        print("1. Registrar Venda")
        print("2. Ver Histórico (Detalhado)")
        print("3. Ver Valor Total no Caixa")
        print("4. Sair")
        print("="*35)
        
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            try:
                valor = float(input("\nDigite o valor da venda: R$ "))
                agora = datetime.now()
                data_formatada = agora.strftime("%d/%m/%Y %H:%M:%S")
                
                registro = f"[{data_formatada}] Venda: R$ {valor:.2f}\n"
                
                with open("historico_vendas.txt", "a") as arquivo:
                    arquivo.write(registro)
                
                print(f"\n✅ R$ {valor:.2f} registrado com sucesso!")
                input("\n[Enter] para voltar...")
            except ValueError:
                print("\n❌ Use apenas números e ponto (ex: 10.50)")
                input("\n[Enter] para tentar novamente...")

        elif opcao == "2":
            print("\n--- HISTÓRICO DE VENDAS ---")
            try:
                with open("historico_vendas.txt", "r") as arquivo:
                    print(arquivo.read())
            except FileNotFoundError:
                print("Nenhuma venda no sistema.")
            input("\n[Enter] para voltar...")

        elif opcao == "3":
            total_caixa = calcular_total()
            print("\n" + "="*25)
            print(f"💰 TOTAL EM CAIXA: R$ {total_caixa:.2f}")
            print("="*25)
            input("\n[Enter] para voltar...")

        elif opcao == "4":
            total_final = calcular_total()
            print(f"\nFechando caixa... Total final: R$ {total_final:.2f}")
            print("Bom trabalho, Lucas!")
            break
        else:
            print("\nOpção inválida!")
            input("\n[Enter] para tentar novamente...")

if __name__ == "__main__":
    menu()# =========================================================
# PROJETO: Controle de Caixa - JW Beer
# DESENVOLVEDOR: Lucas Vinicius da Silva
# OBJETIVO: Gerenciar entradas e saídas da minha adega
# UFERSA - Bacharelado em Tecnologia da Informação (BTI)
# =========================================================

import os

# Nome do arquivo onde os dados serão guardados no meu Linux
ARQUIVO_BANCO = "caixa_adega.txt"

def carregar_dados():
    """
    Função que eu criei para verificar se já existe um saldo salvo.
    Se não existir, o sistema começa do zero.
    """
    if os.path.exists(ARQUIVO_BANCO):
        with open(ARQUIVO_BANCO, "r") as f:
            return float(f.read())
    return 0.0

def gravar_dados(valor_final):
    """
    Aqui eu salvo o saldo atualizado no arquivo para não perder nada.
    """
    with open(ARQUIVO_BANCO, "w") as f:
        f.write(str(valor_final))

# Inicialização das variáveis
meu_saldo = carregar_dados()
rodando = True

# Loop principal do programa
while rodando:
    print("\n" + "="*30)
    print("      JW BEER - SISTEMA DE CAIXA")
    print("="*30)
    print(f"SALDO EM CONTA: R$ {meu_saldo:.2f}")
    print("-" * 30)
    print("1 -> Registrar Venda (Entrada)")
    print("2 -> Registrar Gasto (Saída)")
    print("3 -> Fechar Sistema")
    print("="*30)
    
    escolha = input("O que deseja fazer, Lucas? ")

    if escolha == "1":
        venda = float(input("Valor da venda: R$ "))
        meu_saldo += venda
        gravar_dados(meu_saldo)
        print(">>> Venda computada com sucesso!")
    
    elif escolha == "2":
        gasto = float(input("Valor do gasto: R$ "))
        meu_saldo -= gasto
        gravar_dados(meu_saldo)
        print(">>> Gasto registrado no sistema.")
        
    elif escolha == "3":
        print("Finalizando sistema... Até logo!")
        rodando = False
    
    else:
        print("Opção inválida! Escolha 1, 2 ou 3.")