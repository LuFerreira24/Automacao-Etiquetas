import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from barcode import Code128
from barcode.writer import ImageWriter

def gerar_codigo_barras_img(sku: str) -> io.BytesIO:
    """Gera a imagem do código de barras Code128 em memória."""
    stream_memoria = io.BytesIO()
    Code128(sku, writer=ImageWriter()).write(stream_memoria, options={'write_text': False})
    stream_memoria.seek(0)
    return stream_memoria

def criar_pdf_etiquetas(itens: list[dict], arquivo_saida: str = "etiquetas_pecas.pdf"):
    doc = SimpleDocTemplate(
        arquivo_saida,
        pagesize=A4,
        rightMargin=15,
        leftMargin=15,
        topMargin=15,
        bottomMargin=15
    )
    
    # Estilos de texto
    style_titulo = ParagraphStyle(
        'TituloEtiq',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=9,
        alignment=1  # Centralizado
    )
    style_fornecedor = ParagraphStyle(
        'FornEtiq',
        fontName='Helvetica',
        fontSize=7,
        leading=8,
        alignment=1
    )
    style_sku = ParagraphStyle(
        'SkuEtiq',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=9,
        alignment=1
    )

    celulas = []
    
    # Cria a etiqueta com Descrição, Fornecedor, Código de Barras e Código
    for item in itens:
        for _ in range(item['qtd']):
            img_bc_stream = gerar_codigo_barras_img(str(item['sku']))
            img_obj = Image(img_bc_stream, width=110, height=24)
            
            conteudo_etiqueta = [
                Paragraph(item['descricao'][:32], style_titulo),
                Paragraph(f"Forn: {item.get('fornecedor', 'N/I')[:26]}", style_fornecedor),
                img_obj,
                Paragraph(f"Cód: <b>{item['sku']}</b>", style_sku)
            ]
            celulas.append(conteudo_etiqueta)

    # Organiza em grade (3 colunas de etiquetas por linha)
    colunas = 3
    tabela_dados = []
    linha_atual = []
    
    for celula in celulas:
        linha_atual.append(celula)
        if len(linha_atual) == colunas:
            tabela_dados.append(linha_atual)
            linha_atual = []
            
    if linha_atual:
        while len(linha_atual) < colunas:
            linha_atual.append("")
        tabela_dados.append(linha_atual)

    # Monta a tabela em formato de folha A4
    tabela = Table(tabela_dados, colWidths=[180]*3, rowHeights=[90]*len(tabela_dados))
    tabela.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))

    doc.build([tabela])
    print(f"\n✅ PDF de etiquetas gerado com sucesso: {arquivo_saida}")