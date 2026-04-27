# Gerenciador Financeiro da Adega - Versão 1.0
saldo = 0.0

while True:
    print("\n--- GERENCIADOR FINANCEIRO ---")
    print(f"Saldo atual: R$ {saldo:.2f}")
    print("1. Adicionar Entrada (Venda)")
    print("2. Adicionar Saída (Gasto)")
    print("3. Sair")
    
    opcao = input("Escolha uma opção: ")

    if opcao == "1":
        valor = float(input("Digite o valor da entrada: R$ "))
        saldo += valor
        print("Entrada registrada com sucesso!")
    
    elif opcao == "2":
        valor = float(input("Digite o valor da saída: R$ "))
        saldo -= valor
        print("Saída registrada com sucesso!")
        
    elif opcao == "3":
        print("Saindo... Bons negócios!")
        break
    
    else:
        print("Opção inválida. Tente novamente.")