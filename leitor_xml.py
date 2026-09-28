import xml.etree.ElementTree as ET
import os

def processar_xml_local(caminho_xml: str) -> list[dict]:
    """
    Lê um arquivo .xml de NF-e local e extrai os produtos,
    o código do fornecedor (cProd) e o nome/descrição do produto (xProd).
    """
    caminho_xml = caminho_xml.strip('"').strip("'")
    
    if not os.path.exists(caminho_xml):
        raise FileNotFoundError(f"Arquivo não encontrado no caminho: {caminho_xml}")

    tree = ET.parse(caminho_xml)
    root = tree.getroot()
    
    ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

    # 1. Busca Razão Social do Fornecedor (Emitente)
    emitente = root.find('.//nfe:emit/nfe:xNome', ns)
    if emitente is None:
        emitente = root.find('.//emit/xNome')
    nome_fornecedor = emitente.text if emitente is not None else "FORNECEDOR DESCONHECIDO"

    # 2. Busca os itens da nota (<det>)
    itens = root.findall('.//nfe:det', ns)
    if not itens:
        itens = root.findall('.//det')

    produtos = []

    for det in itens:
        prod = det.find('nfe:prod', ns)
        if prod is None:
            prod = det.find('prod')

        if prod is not None:
            c_prod = prod.find('nfe:cProd', ns) if prod.find('nfe:cProd', ns) is not None else prod.find('cProd')
            x_prod = prod.find('nfe:xProd', ns) if prod.find('nfe:xProd', ns) is not None else prod.find('xProd')
            q_com = prod.find('nfe:qCom', ns) if prod.find('nfe:qCom', ns) is not None else prod.find('qCom')

            if c_prod is not None and x_prod is not None:
                codigo_fornecedor = c_prod.text
                descricao_produto = x_prod.text
                qtd = int(float(q_com.text)) if q_com is not None else 1

                produtos.append({
                    "codigo": codigo_fornecedor,
                    "nome": descricao_produto,  # Define explicitamente 'nome'
                    "descricao": descricao_produto,  # Compatibilidade com o gerador
                    "fornecedor": nome_fornecedor,
                    "qtd": qtd,
                    "cod_interno": codigo_fornecedor  # Inicializa o cod_interno com o código do fornecedor
                })

    return produtos