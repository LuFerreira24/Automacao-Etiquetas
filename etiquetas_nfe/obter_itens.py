def buscar_itens_nota(chave_acesso: str) -> list[dict]:
    """
    Retorna a lista de produtos contidos na nota fiscal.
    Cada item possui código, descrição, quantidade e SKU interno.
    """
    # Exemplo de itens retornados da nota fiscal
    return [
        {"codigo": "101", "descricao": "Filtro de Oleo Tecfil PSL55", "qtd": 2, "sku": "PEC-101"},
        {"codigo": "204", "descricao": "Pastilha de Freio Dianteira Cobreq", "qtd": 1, "sku": "PEC-204"},
        {"codigo": "512", "descricao": "Vela de Ignação NGK BKR6E", "qtd": 4, "sku": "PEC-512"},
    ]