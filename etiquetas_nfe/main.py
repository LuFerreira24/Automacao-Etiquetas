from extrair_chave import extrair_chave_nfe
from obter_itens import buscar_itens_nota
from gerar_etiquetas import criar_pdf_etiquetas

def main():
    print("==================================================")
    print("   SISTEMA DE ETIQUETAGEM DE PEÇAS POR QR CODE    ")
    print("==================================================")
    
    # 1. Recebe a URL do leitor de QR Code
    qr_input = input("\nEscaneie ou cole a URL do QR Code da Nota Fiscal: ").strip()
    
    try:
        # 2. Extrai os 44 dígitos
        chave = extrair_chave_nfe(qr_input)
        print(f"-> Chave de Acesso identificada: {chave}")
        
        # 3. Consulta a SEFAZ via Certificado Digital A1
        print("-> Conectando à SEFAZ para buscar os produtos reais...")
        produtos = buscar_itens_nota(chave)
        print(f"-> Sucesso! {len(produtos)} produto(s) encontrado(s) na nota.")
        
        # 4. Gera o PDF das etiquetas
        criar_pdf_etiquetas(produtos)
        
    except Exception as e:
        print(f"\n❌ Erro ao processar a nota fiscal: {e}")

if __name__ == "__main__":
    main()