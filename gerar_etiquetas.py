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
    caminho_logo = "logo.png"

    # Margens da folha A4 otimizadas
    doc = SimpleDocTemplate(
        arquivo_saida,
        pagesize=A4,
        rightMargin=14,
        leftMargin=14,
        topMargin=16,
        bottomMargin=16
    )
    
    # Estilos Visuais
    style_descricao = ParagraphStyle(
        'DescricaoProduto',
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=11.5,
        alignment=0, # Alinhado à esquerda
        textColor=colors.HexColor('#111111')
    )
    
    style_cod_interno = ParagraphStyle(
        'CodigoInternoRodape',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        alignment=0, # Alinhado à esquerda
        textColor=colors.black
    )

    style_aviso_logo = ParagraphStyle(
        'AvisoLogo', 
        fontName='Helvetica-Bold', 
        fontSize=9, 
        alignment=1,
        textColor=colors.black
    )

    celulas = []
    
    for item in itens:
        cod_imprimir = item.get('cod_interno') or item.get('sku') or item.get('codigo', '')
        desc_produto = item.get('nome') or item.get('descricao', '')

        for _ in range(item.get('qtd', 1)):
            # 1. Logo da empresa
            if os.path.exists(caminho_logo):
                logo_obj = Image(caminho_logo, width=110, height=32)
            else:
                logo_obj = Paragraph("CASA DA CAMIONETE", style_aviso_logo)
            
            # 2. Código de Barras
            if cod_imprimir:
                img_bc_stream = gerar_codigo_barras_img(cod_imprimir)
                img_bc_obj = Image(img_bc_stream, width=145, height=24)
            else:
                img_bc_obj = Paragraph("", style_cod_interno)

            # --- ESTRUTURA INTERNA DA ETIQUETA ---
            # Redistribuição das alturas: Linha 2 (Código de barras) ampliada para 34pt
            conteudo_etiqueta = Table(
                [
                    [logo_obj],
                    [Paragraph(desc_produto.upper()[:44], style_descricao)],
                    [img_bc_obj],
                    [Paragraph(f"CÓDIGO INTERNO: {cod_imprimir}", style_cod_interno)]
                ],
                colWidths=[165],
                rowHeights=[36, 26, 34, 18]
            )

            # Estilo com alinhamento e elevação do código de barras
            conteudo_etiqueta.setStyle(TableStyle([
                # Alinhamentos
                ('ALIGN', (0,0), (0,0), 'CENTER'),      # Logo centralizado
                ('VALIGN', (0,0), (0,0), 'MIDDLE'),
                ('ALIGN', (0,1), (0,1), 'LEFT'),        # Descrição alinhada à esquerda
                ('VALIGN', (0,1), (0,1), 'MIDDLE'),
                ('ALIGN', (0,2), (0,2), 'CENTER'),      # Código de barras centralizado
                ('VALIGN', (0,2), (0,2), 'MIDDLE'),     # Alinhamento vertical ao centro
                ('ALIGN', (0,3), (0,3), 'LEFT'),        # Código interno alinhado à esquerda
                ('VALIGN', (0,3), (0,3), 'MIDDLE'),

                # Divisórias horizontais
                ('LINEBELOW', (0,0), (0,0), 1.0, colors.black), # Linha abaixo da logo
                ('LINEBELOW', (0,2), (0,2), 1.0, colors.black), # Linha acima do código interno

                # Paddings (Espaçamento extra na célula do código de barras para subir em relação à linha)
                ('TOPPADDING', (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,2), (0,2), 5),     # Eleva o código de barras afastando da linha
                ('LEFTPADDING', (0,0), (-1,-1), 4),
                ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ]))

            celulas.append(conteudo_etiqueta)

    # --- MONTAGEM DA GRADE DE ETIQUETAS A4 ---
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

    # Tabela externa com contornos das etiquetas
    tabela_principal = Table(
        tabela_dados, 
        colWidths=[180] * colunas, 
        rowHeights=[122] * len(tabela_dados)
    )
    
    tabela_principal.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.6, colors.HexColor('#222222')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))

    doc.build([tabela_principal])