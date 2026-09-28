import ssl
import requests
import xml.etree.ElementTree as ET
import tempfile
import os
import gzip
import base64
import time
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption

def extrair_cert_e_chave(caminho_pfx: str, senha_pfx: str):
    """Extrai certificado e chave privada em formato PEM temporário."""
    with open(caminho_pfx, 'rb') as f:
        pfx_data = f.read()

    senha_bytes = senha_pfx.encode('utf-8') if senha_pfx else None
    chave_privada, certificado, _ = pkcs12.load_key_and_certificates(pfx_data, senha_bytes)

    if not chave_privada or not certificado:
        raise ValueError("Falha ao abrir o certificado .pfx com a senha fornecida.")

    cert_pem = certificado.public_bytes(Encoding.PEM)
    key_pem = chave_privada.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=NoEncryption()
    )

    cert_file = tempfile.NamedTemporaryFile(delete=False)
    key_file = tempfile.NamedTemporaryFile(delete=False)
    cert_file.write(cert_pem)
    key_file.write(key_pem)
    cert_file.close()
    key_file.close()

    return cert_file.name, key_file.name


def enviar_ciencia_emissao(chave_acesso: str, cnpj: str, cert_pem: str, key_pem: str):
    """
    Envia o evento de Ciência da Emissão (210210) para a SEFAZ.
    Isso força a SEFAZ a disponibilizar o XML completo com a lista de itens.
    """
    url_recepcao_evento = "https://www1.nfe.fazenda.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx"
    
    # ID do Evento
    tp_evento = "210210" # Ciência da Emissão
    id_evento = f"ID{tp_evento}{chave_acesso}01"
    
    soap_xml = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
      <soap12:Body>
        <nfeRecepcaoEventoNF xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4">
          <nfeDadosMsg>
            <envEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00">
              <idLote>1</idLote>
              <evento versao="1.00">
                <infEvento Id="{id_evento}">
                  <cOrgao>91</cOrgao> <!-- 91 = Ambiente Nacional -->
                  <tpAmb>1</tpAmb>
                  <CNPJ>{cnpj}</CNPJ>
                  <chNFe>{chave_acesso}</chNFe>
                  <dhEvento>2026-09-28T14:00:00-03:00</dhEvento>
                  <tpEvento>{tp_evento}</tpEvento>
                  <nSeqEvento>1</nSeqEvento>
                  <verEvento>1.00</verEvento>
                  <detEvento versao="1.00">
                    <descEvento>Ciencia da Emissao</descEvento>
                  </detEvento>
                </infEvento>
              </evento>
            </envEvento>
          </nfeDadosMsg>
        </nfeRecepcaoEventoNF>
      </soap12:Body>
    </soap12:Envelope>"""

    headers = {'Content-Type': 'application/soap+xml; charset=utf-8'}
    try:
        requests.post(url_recepcao_evento, data=soap_xml, headers=headers, cert=(cert_pem, key_pem), timeout=10)
    except Exception:
        pass # Segue o fluxo caso a ciência já tenha sido enviada anteriormente


def buscar_xml_sefaz(chave_acesso: str, cnpj: str, caminho_pfx: str, senha_pfx: str) -> str:
    """Realiza a consulta no WebService NFeDistribuicaoDFe da SEFAZ Nacional."""
    url_sefaz = "https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx"
    
    cert_pem, key_pem = extrair_cert_e_chave(caminho_pfx, senha_pfx)
    
    # 1. Registra ciência para autorizar liberação do XML de produtos
    enviar_ciencia_emissao(chave_acesso, cnpj, cert_pem, key_pem)
    time.sleep(1) # Aguarda autorização no servidor da SEFAZ

    # 2. Requisita o documento
    soap_xml = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
      <soap12:Body>
        <nfeDistDFeInteresse xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe">
          <nfeDadosMsg>
            <distDFeInt xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.01">
              <tpAmb>1</tpAmb>
              <cUFAutor>52</cUFAutor>
              <CNPJ>{cnpj}</CNPJ>
              <consChave>
                <chNFe>{chave_acesso}</chNFe>
              </consChave>
            </distDFeInt>
          </nfeDadosMsg>
        </nfeDistDFeInteresse>
      </soap12:Body>
    </soap12:Envelope>"""

    headers = {'Content-Type': 'application/soap+xml; charset=utf-8'}

    try:
        response = requests.post(
            url_sefaz, 
            data=soap_xml, 
            headers=headers, 
            cert=(cert_pem, key_pem),
            timeout=15
        )
        return response.text
    finally:
        if os.path.exists(cert_pem): os.remove(cert_pem)
        if os.path.exists(key_pem): os.remove(key_pem)


def processar_resposta_xml(xml_resposta: str) -> list[dict]:
    """Parseia a resposta SOAP descompactando o conteúdo das tags <docZip>."""
    root = ET.fromstring(xml_resposta)
    ns_sefaz = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

    xmls_nota = []

    # Extrai e descompacta os blocos de XML da resposta
    for doc_zip in root.findall('.//nfe:docZip', ns_sefaz):
        try:
            conteudo_zip = base64.b64decode(doc_zip.text)
            xml_descompactado = gzip.decompress(conteudo_zip).decode('utf-8', errors='ignore')
            xmls_nota.append(xml_descompactado)
        except Exception:
            continue

    produtos = []

    for xml_str in xmls_nota:
        try:
            doc_root = ET.fromstring(xml_str)
        except Exception:
            continue

        ns_doc = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

        # Extrai fornecedor
        emitente = doc_root.find('.//nfe:emit/nfe:xNome', ns_doc)
        if emitente is None:
            emitente = doc_root.find('.//emit/xNome')
        nome_fornecedor = emitente.text if emitente is not None else "FORNECEDOR DESCONHECIDO"

        # Extrai itens
        itens = doc_root.findall('.//nfe:det', ns_doc)
        if not itens:
            itens = doc_root.findall('.//det')

        for det in itens:
            prod = det.find('nfe:prod', ns_doc)
            if prod is None:
                prod = det.find('prod')

            if prod is not None:
                c_prod = prod.find('nfe:cProd', ns_doc) if prod.find('nfe:cProd', ns_doc) is not None else prod.find('cProd')
                x_prod = prod.find('nfe:xProd', ns_doc) if prod.find('nfe:xProd', ns_doc) is not None else prod.find('xProd')
                q_com = prod.find('nfe:qCom', ns_doc) if prod.find('nfe:qCom', ns_doc) is not None else prod.find('qCom')

                if c_prod is not None and x_prod is not None:
                    codigo_fornecedor = c_prod.text
                    descricao_produto = x_prod.text
                    qtd = int(float(q_com.text)) if q_com is not None else 1

                    produtos.append({
                        "codigo": codigo_fornecedor,
                        "descricao": descricao_produto,
                        "fornecedor": nome_fornecedor,
                        "qtd": qtd,
                        "sku": codigo_fornecedor
                    })

    return produtos