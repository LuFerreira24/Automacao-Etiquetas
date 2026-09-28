import os
import sys
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from leitor_xml import processar_xml_local
from gerar_etiquetas import criar_pdf_etiquetas

# Configuração do tema visual
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AppEtiquetas(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configurações da janela principal
        self.title("Gerador de Etiquetas de Peças - NF-e")
        self.geometry("820x640")
        self.resizable(True, True)

        self.caminho_xml_selecionado = ""
        self.produtos = []  # Lista de dicionários dos produtos carregados
        self.item_selecionado_index = None

        # Estilizar o Treeview do Tkinter
        self.configurar_estilo_tabela()

        # Construção da interface
        self.criar_widgets()

    def configurar_estilo_tabela(self):
        style = ttk.Style()
        style.theme_use("default")
        
        # Cores para o tema
        bg_color = "#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#ffffff"
        fg_color = "#ffffff" if ctk.get_appearance_mode() == "Dark" else "#000000"
        selected_bg = "#1f538d"

        style.configure(
            "Treeview",
            background=bg_color,
            foreground=fg_color,
            fieldbackground=bg_color,
            rowheight=28,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Treeview.Heading",
            background="#1f538d",
            foreground="white",
            font=("Segoe UI", 10, "bold")
        )
        style.map("Treeview", background=[("selected", selected_bg)])

    def criar_widgets(self):
        # --- Cabeçalho ---
        self.lbl_titulo = ctk.CTkLabel(
            self, 
            text="Etiquetagem de Peças Automotive", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.lbl_titulo.pack(pady=(15, 2))

        self.lbl_subtitulo = ctk.CTkLabel(
            self, 
            text="Importe o XML, ajuste o Código Interno, Nome ou Qtd e gere as etiquetas em PDF", 
            font=ctk.CTkFont(size=12)
        )
        self.lbl_subtitulo.pack(pady=(0, 10))

        # --- Topo: Seleção de Arquivo ---
        self.frame_top = ctk.CTkFrame(self)
        self.frame_top.pack(padx=20, fill="x", pady=5)

        self.btn_selecionar = ctk.CTkButton(
            self.frame_top, 
            text="📁 Selecionar Arquivo XML", 
            command=self.selecionar_arquivo,
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        self.btn_selecionar.pack(side="left", padx=15, pady=12)

        self.lbl_arquivo = ctk.CTkLabel(
            self.frame_top, 
            text="Nenhum arquivo XML selecionado", 
            font=ctk.CTkFont(size=12, slant="italic")
        )
        self.lbl_arquivo.pack(side="left", padx=10, fill="x", expand=True)

        # --- Centro: Tabela de Produtos ---
        self.frame_tabela = ctk.CTkFrame(self)
        self.frame_tabela.pack(padx=20, pady=10, fill="both", expand=True)

        columns = ("pos", "cod_interno", "nome", "qtd")
        self.tree = ttk.Treeview(self.frame_tabela, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("pos", text="#")
        self.tree.heading("cod_interno", text="Cód. Interno")
        self.tree.heading("nome", text="Descrição da Peça")
        self.tree.heading("qtd", text="Qtd")

        self.tree.column("pos", width=40, anchor="center")
        self.tree.column("cod_interno", width=140, anchor="w")
        self.tree.column("nome", width=480, anchor="w")
        self.tree.column("qtd", width=60, anchor="center")

        # Scrollbar vertical para a tabela
        scrollbar = ttk.Scrollbar(self.frame_tabela, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

        # Evento ao selecionar item na tabela
        self.tree.bind("<<TreeviewSelect>>", self.ao_selecionar_item)

        # --- Base: Painel de Edição de Dados ---
        self.frame_edicao = ctk.CTkFrame(self)
        self.frame_edicao.pack(padx=20, pady=5, fill="x")

        # Linha 1 de Edição: Código Interno e Quantidade
        lbl_ed_int = ctk.CTkLabel(self.frame_edicao, text="Cód. Interno:", font=ctk.CTkFont(size=11, weight="bold"))
        lbl_ed_int.grid(row=0, column=0, padx=(10, 2), pady=8, sticky="e")
        
        self.entry_cod_interno = ctk.CTkEntry(self.frame_edicao, width=200)
        self.entry_cod_interno.grid(row=0, column=1, padx=(0, 15), pady=8, sticky="w")

        lbl_ed_qtd = ctk.CTkLabel(self.frame_edicao, text="Qtd:", font=ctk.CTkFont(size=11, weight="bold"))
        lbl_ed_qtd.grid(row=0, column=2, padx=(10, 2), pady=8, sticky="e")
        
        self.entry_qtd = ctk.CTkEntry(self.frame_edicao, width=70)
        self.entry_qtd.grid(row=0, column=3, padx=(0, 10), pady=8, sticky="w")

        # Linha 2 de Edição: Nome/Descrição e Botão Salvar
        lbl_ed_nome = ctk.CTkLabel(self.frame_edicao, text="Descrição:", font=ctk.CTkFont(size=11, weight="bold"))
        lbl_ed_nome.grid(row=1, column=0, padx=(10, 2), pady=(0, 10), sticky="e")

        self.entry_nome = ctk.CTkEntry(self.frame_edicao, width=450)
        self.entry_nome.grid(row=1, column=1, columnspan=3, padx=(0, 15), pady=(0, 10), sticky="w")

        self.btn_salvar_item = ctk.CTkButton(
            self.frame_edicao, 
            text="💾 Salvar Item", 
            command=self.salvar_alteracao_item,
            width=120,
            fg_color="#e67e22",
            hover_color="#d35400",
            state="disabled"
        )
        self.btn_salvar_item.grid(row=1, column=4, padx=(0, 10), pady=(0, 10), sticky="w")

        # --- Rodapé: Status e Gerar PDF ---
        self.frame_footer = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_footer.pack(padx=20, pady=10, fill="x")

        self.lbl_status = ctk.CTkLabel(
            self.frame_footer, 
            text="", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#1f538d"
        )
        self.lbl_status.pack(side="left", padx=10)

        self.btn_gerar = ctk.CTkButton(
            self.frame_footer, 
            text="🖨️ Gerar PDF de Etiquetas", 
            command=self.gerar_etiquetas,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=220,
            state="disabled",
            fg_color="#2fa572",
            hover_color="#1e704d"
        )
        self.btn_gerar.pack(side="right", padx=10)

    # --- Lógica da Aplicação ---

    def selecionar_arquivo(self):
        caminho = filedialog.askopenfilename(
            title="Selecione o arquivo XML da NF-e",
            filetypes=[("Arquivos XML", "*.xml"), ("Todos os arquivos", "*.*")]
        )
        if caminho:
            self.caminho_xml_selecionado = caminho
            nome_arquivo = os.path.basename(caminho)
            self.lbl_arquivo.configure(text=f"📄 {nome_arquivo}", font=ctk.CTkFont(size=12, weight="bold"))
            
            # Carregar e exibir produtos
            self.carregar_produtos_xml()

    def carregar_produtos_xml(self):
        try:
            self.produtos = processar_xml_local(self.caminho_xml_selecionado)
            
            for prod in self.produtos:
                if 'nome' not in prod or not prod['nome']:
                    prod['nome'] = prod.get('descricao', '')
                prod['descricao'] = prod['nome']
                
                if 'cod_interno' not in prod or not prod['cod_interno']:
                    prod['cod_interno'] = prod.get('codigo', '')

            self.atualizar_tabela()

            if self.produtos:
                total_etiquetas = sum(p['qtd'] for p in self.produtos)
                self.lbl_status.configure(
                    text=f"Total: {len(self.produtos)} item(ns) | {total_etiquetas} etiqueta(s)",
                    text_color="#1f538d"
                )
                self.btn_gerar.configure(state="normal")
            else:
                messagebox.showwarning("Aviso", "Nenhum produto foi localizado no XML.")

        except Exception as e:
            messagebox.showerror("Erro ao LER XML", f"Ocorreu um erro ao ler o XML:\n{e}")

    def atualizar_tabela(self):
        # Limpar tabela
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Preencher tabela
        for idx, p in enumerate(self.produtos, start=1):
            cod_interno = p.get('cod_interno', '')
            nome = p.get('nome', '')
            qtd = p.get('qtd', 1)
            
            self.tree.insert("", "end", iid=idx-1, values=(idx, cod_interno, nome, qtd))

    def ao_selecionar_item(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        index = int(selected_items[0])
        self.item_selecionado_index = index
        prod = self.produtos[index]

        # Limpa e preenche os campos do painel de edição
        self.entry_cod_interno.delete(0, tk.END)
        self.entry_cod_interno.insert(0, prod.get('cod_interno', ''))

        self.entry_nome.delete(0, tk.END)
        self.entry_nome.insert(0, prod.get('nome', ''))

        self.entry_qtd.delete(0, tk.END)
        self.entry_qtd.insert(0, str(prod.get('qtd', 1)))

        self.btn_salvar_item.configure(state="normal")

    def salvar_alteracao_item(self):
        if self.item_selecionado_index is None:
            return

        idx = self.item_selecionado_index
        
        try:
            qtd_val = int(self.entry_qtd.get().strip())
        except ValueError:
            messagebox.showwarning("Aviso", "Quantidade deve ser um número inteiro válido.")
            return

        # Atualiza a lista em memória
        novo_nome = self.entry_nome.get().strip()
        self.produtos[idx]['cod_interno'] = self.entry_cod_interno.get().strip()
        self.produtos[idx]['nome'] = novo_nome
        self.produtos[idx]['descricao'] = novo_nome
        self.produtos[idx]['qtd'] = qtd_val

        # Atualiza a tabela gráfica
        self.atualizar_tabela()

        # Atualiza o resumo
        total_etiquetas = sum(p['qtd'] for p in self.produtos)
        self.lbl_status.configure(
            text=f"Item #{idx+1} atualizado! Total etiquetas: {total_etiquetas}",
            text_color="#2fa572"
        )

    def gerar_etiquetas(self):
        if not self.produtos:
            messagebox.showwarning("Aviso", "Nenhum produto carregado.")
            return

        try:
            # 1. Cria a pasta 'PDFs_Etiquetas' caso ela ainda não exista
            pasta_destino = "PDFs_Etiquetas"
            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)

            # 2. Gera o nome do arquivo com data e horário atual (ex: etiquetas_20260928_152117.pdf)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"etiquetas_{timestamp}.pdf"
            caminho_completo_pdf = os.path.join(pasta_destino, nome_arquivo)

            # 3. Cria o PDF no caminho especificado
            criar_pdf_etiquetas(self.produtos, arquivo_saida=caminho_completo_pdf)

            total_etiquetas = sum(p['qtd'] for p in self.produtos)
            self.lbl_status.configure(
                text=f"✅ Salvo em {pasta_destino}/{nome_arquivo} ({total_etiquetas} etiqueta(s))",
                text_color="#2fa572"
            )

            # 4. Abre o arquivo PDF gerado no leitor padrão do Windows
            if os.path.exists(caminho_completo_pdf):
                os.startfile(caminho_completo_pdf)

        except Exception as e:
            messagebox.showerror("Erro ao Gerar PDF", f"Falha ao criar o PDF de etiquetas:\n{e}")

if __name__ == "__main__":
    app = AppEtiquetas()
    app.mainloop()