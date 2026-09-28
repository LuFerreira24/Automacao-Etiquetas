from consultar_sefaz import buscar_xml_sefaz, processar_resposta_xml

# CONFIGURAÇÕES DO SEU CERTIFICADO E LOJA
CAMINHO_CERTIFICADO = "C:/Users/Eder/OneDrive/Documents/certificado.pfx"  # Caminho para o arquivo .pfx
SENHA_CERTIFICADO = "04031995"  # Senha do certificado
CNPJ_LOJA = "20064552000170"  # Apenas números

def buscar_itens_nota(chave_acesso: str) -> list[dict]:
    """
    Busca os itens diretamente na SEFAZ via Certificado A1.
    """
    print("-> Enviando autenticação e chave para a SEFAZ...")
    xml_resposta = buscar_xml_sefaz(
        chave_acesso, 
        CNPJ_LOJA, 
        CAMINHO_CERTIFICADO, 
        SENHA_CERTIFICADO
    )
    
    produtos = processar_resposta_xml(xml_resposta)
    
    if not produtos:
        raise Exception("Nenhum produto foi retornado pela SEFAZ para esta chave de acesso.")
        
    return produtos