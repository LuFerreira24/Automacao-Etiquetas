from extrair_chave import extrair_chave_nfe
from obter_itens import buscar_itens_nota
from gerar_etiquetas import criar_pdf_etiquetas

def main():
    print("==================================================")
    print("   SISTEMA DE ETIQUETAGEM DE PEÇAS POR QR CODE    ")
    print("==================================================")
    
    # Simula a leitura do leitor de código de barras USB/Câmera
    qr_input = input("\nEscaneie ou cole a URL do QR Code da Nota Fiscal: ").strip()
    
    try:
        # 1. Extrai a chave de 44 dígitos
        chave = extrair_chave_nfe(qr_input)
        print(f"-> Chave de Acesso identificada: {chave}")
        
        # 2. Busca os produtos da nota
        print("-> Buscando produtos da nota fiscal...")
        produtos = buscar_itens_nota(chave)
        print(f"-> Encontrados {len(produtos)} produtos diferentes.")
        
        # 3. Gera o arquivo PDF
        criar_pdf_etiquetas(produtos)
        
    except Exception as e:
        print(f"❌ Erro ao processar: {e}")

if __name__ == "__main__":
    main()