import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from barcode import Code128
from barcode.writer import ImageWriter

def gerar_codigo_barras_img(sku: str) -> io.BytesIO:
    """Gera a imagem do código de barras Code128 sem o texto inferior nativo."""
    stream_memoria = io.BytesIO()
    Code128(str(sku), writer=ImageWriter()).write(stream_memoria, options={'write_text': False})
    stream_memoria.seek(0)
    return stream_memoria

def criar_pdf_etiquetas(itens: list[dict], arquivo_saida: str = "etiquetas_pecas.pdf"):
    # Caminho para a imagem da logo na mesma pasta do projeto
    caminho_logo = "logo.png"

    # Configuração da folha A4 e margens externas
    doc = SimpleDocTemplate(
        arquivo_saida,
        pagesize=A4,
        rightMargin=12,
        leftMargin=12,
        topMargin=15,
        bottomMargin=15
    )
    
    # Estilos de texto
    style_descricao = ParagraphStyle(
        'DescricaoProduto',
        fontName='Helvetica',
        fontSize=10,
        leading=12,
        alignment=0, # Alinhado à esquerda
        textColor=colors.black
    )
    
    style_cod_interno = ParagraphStyle(
        'CodigoInternoRodape',
        fontName='Helvetica',
        fontSize=11,
        leading=13,
        alignment=0, # Alinhado à esquerda
        textColor=colors.black
    )

    celulas = []
    
    for item in itens:
        cod_imprimir = item.get('cod_interno') or item.get('sku') or item.get('codigo', '')
        desc_produto = item.get('nome') or item.get('descricao', '')

        for _ in range(item.get('qtd', 1)):
            # 1. Carrega a imagem real da Logo
            if os.path.exists(caminho_logo):
                # Mantém a proporção da imagem no topo
                logo_obj = Image(caminho_logo, width=120, height=38)
            else:
                # Caso a imagem não seja encontrada, exibe um texto de aviso no topo
                style_aviso = ParagraphStyle('AvisoLogo', fontName='Helvetica-Bold', fontSize=10, alignment=1)
                logo_obj = Paragraph("CASA DA CAMIONETE", style_aviso)
            
            # 2. Código de Barras
            if cod_imprimir:
                img_bc_stream = gerar_codigo_barras_img(cod_imprimir)
                img_bc_obj = Image(img_bc_stream, width=155, height=28)
            else:
                img_bc_obj = Paragraph("", style_cod_interno)

            # Tabela de cada Etiqueta
            # Linha 0: Logo (Topo)
            # Linha 1: Descrição do Produto
            # Linha 2: Código de Barras
            # Linha 3: CÓDIGO INTERNO: XXXXXX
            conteudo_etiqueta = Table(
                [
                    [logo_obj],
                    [Paragraph(desc_produto.upper()[:42], style_descricao)],
                    [img_bc_obj],
                    [Paragraph(f"CÓDIGO INTERNO: {cod_imprimir}", style_cod_interno)]
                ],
                colWidths=[170],
                rowHeights=[42, 26, 32, 20]
            )

            # Estilo com as divisórias pretas idêntico à captura de tela
            conteudo_etiqueta.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('ALIGN', (0,0), (0,0), 'CENTER'),      # Centraliza a logo no topo
                ('ALIGN', (0,2), (0,2), 'CENTER'),      # Centraliza o código de barras
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LINEBELOW', (0,0), (0,0), 1.2, colors.black), # Linha preta sob a logo
                ('LINEBELOW', (0,2), (0,2), 1.2, colors.black), # Linha preta sob o código de barras
                ('TOPPADDING', (0,0), (-1,-1), 1),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ('LEFTPADDING', (0,0), (-1,-1), 4),
                ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ]))

            celulas.append(conteudo_etiqueta)

    # Organização na grade da folha A4 (3 colunas por linha)
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

    # Tabela principal com as bordas externas de cada etiqueta
    tabela_principal = Table(
        tabela_dados, 
        colWidths=[185] * colunas, 
        rowHeights=[128] * len(tabela_dados)
    )
    
    tabela_principal.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.8, colors.black), # Borda preta em volta de cada etiqueta
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))

    doc.build([tabela_principal])