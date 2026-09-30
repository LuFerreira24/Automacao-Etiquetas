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
        self.geometry("880x700")
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
            text="Importe o XML ou adicione manualmente, edite os dados e gere as etiquetas em PDF", 
            font=ctk.CTkFont(size=12)
        )
        self.lbl_subtitulo.pack(pady=(0, 10))

        # --- Topo: Seleção de Arquivo, Limpar e Adicionar Manual ---
        self.frame_top = ctk.CTkFrame(self)
        self.frame_top.pack(padx=20, fill="x", pady=5)

        self.btn_selecionar = ctk.CTkButton(
            self.frame_top, 
            text="📁 Selecionar Arquivo XML", 
            command=self.selecionar_arquivo,
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        self.btn_selecionar.pack(side="left", padx=8, pady=12)

        self.btn_novo_manual = ctk.CTkButton(
            self.frame_top, 
            text="➕ Adicionar Item Manual", 
            command=self.preparar_novo_item,
            fg_color="#27ae60",
            hover_color="#1e8449"
        )
        self.btn_novo_manual.pack(side="left", padx=5, pady=12)

        self.btn_limpar_tudo = ctk.CTkButton(
            self.frame_top, 
            text="🔄 Limpar Tudo", 
            command=self.limpar_tudo_confirmacao,
            fg_color="#7f8c8d",
            hover_color="#616a6b",
            width=100
        )
        self.btn_limpar_tudo.pack(side="left", padx=5, pady=12)

        self.lbl_arquivo = ctk.CTkLabel(
            self.frame_top, 
            text="Nenhum arquivo XML selecionado", 
            font=ctk.CTkFont(size=11, slant="italic")
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

        scrollbar = ttk.Scrollbar(self.frame_tabela, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

        self.tree.bind("<<TreeviewSelect>>", self.ao_selecionar_item)

        # --- Base: Painel de Edição de Dados ---
        self.frame_edicao = ctk.CTkFrame(self)
        self.frame_edicao.pack(padx=20, pady=5, fill="x")

        # Linha 1: Cód. Interno e Qtd
        lbl_ed_int = ctk.CTkLabel(self.frame_edicao, text="Cód. Interno:", font=ctk.CTkFont(size=11, weight="bold"))
        lbl_ed_int.grid(row=0, column=0, padx=(10, 2), pady=8, sticky="e")
        
        self.entry_cod_interno = ctk.CTkEntry(self.frame_edicao, width=200)
        self.entry_cod_interno.grid(row=0, column=1, padx=(0, 15), pady=8, sticky="w")

        lbl_ed_qtd = ctk.CTkLabel(self.frame_edicao, text="Qtd:", font=ctk.CTkFont(size=11, weight="bold"))
        lbl_ed_qtd.grid(row=0, column=2, padx=(10, 2), pady=8, sticky="e")
        
        self.entry_qtd = ctk.CTkEntry(self.frame_edicao, width=70)
        self.entry_qtd.grid(row=0, column=3, padx=(0, 10), pady=8, sticky="w")

        # Linha 2: Descrição e Botões de Ação
        lbl_ed_nome = ctk.CTkLabel(self.frame_edicao, text="Descrição:", font=ctk.CTkFont(size=11, weight="bold"))
        lbl_ed_nome.grid(row=1, column=0, padx=(10, 2), pady=(0, 10), sticky="e")

        self.entry_nome = ctk.CTkEntry(self.frame_edicao, width=420)
        self.entry_nome.grid(row=1, column=1, columnspan=3, padx=(0, 15), pady=(0, 10), sticky="w")

        # Container para botões Salvar / Apagar
        self.frame_botoes_acao = ctk.CTkFrame(self.frame_edicao, fg_color="transparent")
        self.frame_botoes_acao.grid(row=0, column=4, rowspan=2, padx=(0, 10), pady=5, sticky="nsew")

        self.btn_salvar_item = ctk.CTkButton(
            self.frame_botoes_acao, 
            text="💾 Salvar", 
            command=self.salvar_alteracao_item,
            width=100,
            fg_color="#e67e22",
            hover_color="#d35400"
        )
        self.btn_salvar_item.pack(pady=2, fill="x")

        self.btn_excluir_item = ctk.CTkButton(
            self.frame_botoes_acao, 
            text="🗑️ Excluir", 
            command=self.excluir_item_selecionado,
            width=100,
            fg_color="#c0392b",
            hover_color="#962d22",
            state="disabled"
        )
        self.btn_excluir_item.pack(pady=2, fill="x")

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

    # --- Lógica do Sistema ---

    def selecionar_arquivo(self):
        # Se já existirem produtos carregados, pergunta o que fazer
        limpar = True
        if self.produtos:
            resposta = messagebox.askyesnocancel(
                "Novo XML",
                "Já existem itens na lista.\n\n"
                "• Clique em 'Sim' para LIMPAR a lista e abrir o novo XML.\n"
                "• Clique em 'Não' para ADICIONAR os novos itens à lista atual.\n"
                "• Clique em 'Cancelar' para interromper."
            )
            if resposta is None:  # Clicou em Cancelar
                return
            limpar = resposta

        caminho = filedialog.askopenfilename(
            title="Selecione o arquivo XML da NF-e",
            filetypes=[("Arquivos XML", "*.xml"), ("Todos os arquivos", "*.*")]
        )
        if caminho:
            self.caminho_xml_selecionado = caminho
            nome_arquivo = os.path.basename(caminho)
            self.lbl_arquivo.configure(text=f"📄 {nome_arquivo}", font=ctk.CTkFont(size=11, weight="bold"))
            self.carregar_produtos_xml(limpar=limpar)

    def carregar_produtos_xml(self, limpar=True):
        try:
            novos_produtos = processar_xml_local(self.caminho_xml_selecionado)
            
            for prod in novos_produtos:
                if 'nome' not in prod or not prod['nome']:
                    prod['nome'] = prod.get('descricao', '')
                prod['descricao'] = prod['nome']
                
                if 'cod_interno' not in prod or not prod['cod_interno']:
                    prod['cod_interno'] = prod.get('codigo', '')

            if limpar:
                self.produtos = novos_produtos
            else:
                self.produtos.extend(novos_produtos)

            self.atualizar_tabela()
            self.atualizar_resumo_e_botoes()
            self.preparar_novo_item()

        except Exception as e:
            messagebox.showerror("Erro ao LER XML", f"Ocorreu um erro ao ler o XML:\n{e}")

    def limpar_tudo_confirmacao(self):
        if self.produtos:
            if messagebox.askyesno("Confirmar Limpeza", "Deseja remover todos os itens e limpar a tela?"):
                self.resetar_estado()

    def resetar_estado(self):
        self.produtos = []
        self.caminho_xml_selecionado = ""
        self.item_selecionado_index = None
        self.lbl_arquivo.configure(text="Nenhum arquivo XML selecionado", font=ctk.CTkFont(size=11, slant="italic"))
        self.atualizar_tabela()
        self.atualizar_resumo_e_botoes()
        self.preparar_novo_item()

    def atualizar_tabela(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, p in enumerate(self.produtos, start=1):
            cod_interno = p.get('cod_interno', '')
            nome = p.get('nome', '')
            qtd = p.get('qtd', 1)
            
            self.tree.insert("", "end", iid=idx-1, values=(idx, cod_interno, nome, qtd))

    def atualizar_resumo_e_botoes(self):
        if self.produtos:
            total_etiquetas = sum(p['qtd'] for p in self.produtos)
            self.lbl_status.configure(
                text=f"Total: {len(self.produtos)} item(ns) | {total_etiquetas} etiqueta(s)",
                text_color="#1f538d"
            )
            self.btn_gerar.configure(state="normal")
        else:
            self.lbl_status.configure(text="Nenhum item na lista.", text_color="#c0392b")
            self.btn_gerar.configure(state="disabled")

    def ao_selecionar_item(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        index = int(selected_items[0])
        self.item_selecionado_index = index
        prod = self.produtos[index]

        self.entry_cod_interno.delete(0, tk.END)
        self.entry_cod_interno.insert(0, prod.get('cod_interno', ''))

        self.entry_nome.delete(0, tk.END)
        self.entry_nome.insert(0, prod.get('nome', ''))

        self.entry_qtd.delete(0, tk.END)
        self.entry_qtd.insert(0, str(prod.get('qtd', 1)))

        self.btn_excluir_item.configure(state="normal")

    def preparar_novo_item(self):
        """Limpa os campos para inserção manual de um novo produto."""
        self.item_selecionado_index = None
        self.tree.selection_remove(self.tree.selection())

        self.entry_cod_interno.delete(0, tk.END)
        self.entry_nome.delete(0, tk.END)
        self.entry_qtd.delete(0, tk.END)
        self.entry_qtd.insert(0, "1")

        self.entry_cod_interno.focus()
        self.btn_excluir_item.configure(state="disabled")

    def salvar_alteracao_item(self):
        cod_int = self.entry_cod_interno.get().strip()
        nome_val = self.entry_nome.get().strip()
        qtd_str = self.entry_qtd.get().strip()

        if not cod_int or not nome_val:
            messagebox.showwarning("Aviso", "Preencha ao menos o Código Interno e a Descrição.")
            return

        try:
            qtd_val = int(qtd_str)
        except ValueError:
            messagebox.showwarning("Aviso", "Quantidade deve ser um número inteiro válido.")
            return

        if self.item_selecionado_index is not None:
            idx = self.item_selecionado_index
            self.produtos[idx]['cod_interno'] = cod_int
            self.produtos[idx]['nome'] = nome_val
            self.produtos[idx]['descricao'] = nome_val
            self.produtos[idx]['qtd'] = qtd_val
        else:
            novo_prod = {
                "codigo": cod_int,
                "cod_interno": cod_int,
                "nome": nome_val,
                "descricao": nome_val,
                "qtd": qtd_val,
                "fornecedor": ""
            }
            self.produtos.append(novo_prod)

        self.atualizar_tabela()
        self.atualizar_resumo_e_botoes()
        self.preparar_novo_item()

    def excluir_item_selecionado(self):
        if self.item_selecionado_index is None:
            return

        idx = self.item_selecionado_index
        nome_prod = self.produtos[idx].get('nome', 'o item selecionado')

        confirmar = messagebox.askyesno(
            "Confirmar Exclusão", 
            f"Deseja realmente remover '{nome_prod}' da lista de etiquetas?"
        )

        if confirmar:
            self.produtos.pop(idx)
            self.item_selecionado_index = None
            
            self.atualizar_tabela()
            self.atualizar_resumo_e_botoes()
            self.preparar_novo_item()

    def gerar_etiquetas(self):
        if not self.produtos:
            messagebox.showwarning("Aviso", "Nenhum produto na lista para gerar etiquetas.")
            return

        try:
            pasta_destino = "PDFs_Etiquetas"
            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"etiquetas_{timestamp}.pdf"
            caminho_completo_pdf = os.path.join(pasta_destino, nome_arquivo)

            criar_pdf_etiquetas(self.produtos, arquivo_saida=caminho_completo_pdf)

            total_etiquetas = sum(p['qtd'] for p in self.produtos)
            self.lbl_status.configure(
                text=f"✅ Salvo em {pasta_destino}/{nome_arquivo} ({total_etiquetas} etiqueta(s))",
                text_color="#2fa572"
            )

            if os.path.exists(caminho_completo_pdf):
                os.startfile(caminho_completo_pdf)

        except Exception as e:
            messagebox.showerror("Erro ao Gerar PDF", f"Falha ao criar o PDF de etiquetas:\n{e}")

if __name__ == "__main__":
    app = AppEtiquetas()
    app.mainloop()