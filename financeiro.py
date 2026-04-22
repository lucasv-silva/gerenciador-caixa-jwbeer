# =========================================================
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