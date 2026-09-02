from bot_engine import processar_pedido_whatsapp

# Simulação 1: Mensagem de Texto
print("--- TESTE 1: MENSAGEM DE TEXTO ---")
mensagem_1 = "Oi, meu nome é Maria. Quero pedir 2 Heineken Long Neck 330ml para a Rua Maria do Ceu 100, vou pagar com nota de 50"
processar_pedido_whatsapp(texto_cliente=mensagem_1, nome_whatsapp="Maria Silva")

print("\n-----------------------------------\n")

# Simulação 2: Outra mensagem
print("--- TESTE 2: MENSAGEM DE TEXTO ---")
mensagem_2 = "Manda 1 Skol Pilsen 350ml e 1 Cachaça 51 para a Rua Central 45"
processar_pedido_whatsapp(texto_cliente=mensagem_2, nome_whatsapp="João Gabriel")