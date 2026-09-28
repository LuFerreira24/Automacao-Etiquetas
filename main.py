from leitor_xml import processar_xml_local
from gerar_etiquetas import criar_pdf_etiquetas

def main():
    print("==================================================")
    print("   GERADOR DE ETIQUETAS DE PEÇAS (IMPORTAÇÃO XML) ")
    print("==================================================")
    
    caminho_xml = input("\nArraste e solte o arquivo .xml aqui e pressione Enter: ").strip()
    
    try:
        print("-> Lendo arquivo XML...")
        produtos = processar_xml_local(caminho_xml)
        
        if not produtos:
            print("❌ Nenhum produto encontrado no arquivo XML fornecido.")
            return

        print(f"-> Sucesso! {len(produtos)} tipo(s) de produto(s) encontrado(s).")
        
        # Exibe resumo no terminal
        for p in produtos:
            print(f"   • [{p['codigo']}] {p['descricao'][:30]} (Qtd: {p['qtd']})")
        
        print("\n-> Gerando etiquetas em PDF...")
        criar_pdf_etiquetas(produtos)
        
    except Exception as e:
        print(f"\n❌ Erro ao processar o arquivo XML: {e}")

if __name__ == "__main__":
    main()