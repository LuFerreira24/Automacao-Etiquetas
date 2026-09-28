import re

def extrair_chave_nfe(url_qr_code: str) -> str:
    """Extrai a chave de 44 dígitos a partir da URL do QR Code da NF-e/NFC-e."""
    # Procura o parâmetro p= na URL
    match = re.search(r'p=([0-9]{44})', url_qr_code)
    if match:
        return match.group(1)
    
    # Procura qualquer sequência contínua de 44 dígitos
    match_digits = re.search(r'[0-9]{44}', url_qr_code)
    if match_digits:
        return match_digits.group(0)
        
    raise ValueError("Chave de acesso de 44 dígitos não encontrada no QR Code lido.")