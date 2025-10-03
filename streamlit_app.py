import streamlit as st
import pandas as pd
from datetime import datetime, date
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import uuid

# ---------- Helper: formata número no padrão brasileiro ----------
def formato_brl_num(valor):
    try:
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(valor)

# ---------- Configuração inicial ----------
st.set_page_config(page_title="Gerador de Proposta", layout="wide")

# ---------- Define página atual ----------
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "proposta"

# ---------- Função para abrir configurações ----------
def abrir_configuracoes():
    st.session_state["pagina"] = "config"

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Detalhes da Proposta")
    cliente = st.text_input("Nome do Cliente", "Cliente Exemplo")
    data_proposta = st.date_input("Data da Proposta", value=date.today(), format="DD/MM/YYYY")
    prazo_pagamento = st.text_input("Prazo de Pagamento", "À vista")
    prazo_entrega = st.text_input("Prazo de Entrega", "15 dias")
    validade_proposta = st.text_input("Validade da Proposta", "30 dias")
    st.markdown("---")
    st.header("Upload de Produtos")
    uploaded_file = st.file_uploader(
        "Enviar planilha (.xlsx) com colunas: Produto, Quant., Preço Unit., Observações", 
        type=["xlsx"]
    )

    # Botão de download do modelo Excel
    def gerar_excel_modelo():
        data = {
            "Produto": ["Produto A", "Produto B", "Produto C"],
            "Quant.": [10, 5, 2],
            "Preço Unit.": [25.50, 100.00, 350.75],
            "Observações": ["", "", ""]
        }
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return output

    st.download_button(
        label="Baixar Modelo Excel",
        data=gerar_excel_modelo(),
        file_name="produtos_modelo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ---------- Botão de Configurações no final ----------
    st.markdown("", unsafe_allow_html=True)  # força espaço até o final
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.button("⚙️", on_click=abrir_configuracoes, help="Configurações")

# ---------- Página de Proposta ----------
if st.session_state["pagina"] == "proposta":
    st.title("Gerador de Proposta Comercial")

    # Processa upload
    if uploaded_file is not None:
        last = st.session_state.get("_last_uploaded_name")
        if last != getattr(uploaded_file, "name", None):
            try:
                df_excel = pd.read_excel(uploaded_file)
                expected = {"Produto", "Quant.", "Preço Unit."}
                if not expected.issubset(set(df_excel.columns)):
                    st.sidebar.error(f"Planilha inválida. Precisa conter as colunas: {sorted(list(expected))}")
                else:
                    novos = []
                    for _, r in df_excel.iterrows():
                        novos.append({
                            "id": str(uuid.uuid4()),
                            "Produto": r.get("Produto", "") if pd.notna(r.get("Produto", "")) else "",
                            "Quant.": float(r.get("Quant.", 0)) if pd.notna(r.get("Quant.", 0)) else 0.0,
                            "Preço Unit.": float(r.get("Preço Unit.", 0)) if pd.notna(r.get("Preço Unit.", 0)) else 0.0,
                            "Observações": r.get("Observações", "") if "Observações" in df_excel.columns and pd.notna(r.get("Observações", "")) else ""
                        })
                    st.session_state.produtos = novos
                    st.session_state._last_uploaded_name = getattr(uploaded_file, "name", None)
                    st.sidebar.success("Produtos carregados com sucesso.")
            except ImportError:
                st.sidebar.error("Dependência ausente: instale 'openpyxl'.")
            except Exception as e:
                st.sidebar.error(f"Erro ao ler o Excel: {e}")

    if "produtos" not in st.session_state:
        st.session_state.produtos = [{"id": str(uuid.uuid4()), "Produto": "Produto Exemplo", "Quant.": 1, "Preço Unit.": 100.0, "Observações": ""}]

    # Dados da empresa
    st.markdown(f"**A/C {cliente}**")
    st.markdown("### Dados da Empresa")
    st.markdown("""**Nome da Empresa:** GUSTAVO LUIZ FREITAS DE SOUSA  
**CNPJ:** 41.640.044/0001-63  
**IE:** 33.822.412.281  
**IM:** 1.304.930-0  
**Endereço:** Rua Henrique Fleiuss, 444 - Tijuca  
**Cidade/UF:** Rio de Janeiro / RJ  
**CEP:** 20521-260""")
    st.markdown("### Dados para Contato")
    st.markdown("""**E-mail:** gustavo_lfs@hotmail.com  
**Telefone:** (21) 996913090""")
    st.markdown("### Dados Bancários")
    st.markdown("""**Banco:** Inter  
**Agência:** 0001  
**Conta:** 12174848-0  
**PIX:** 41.640.044/0001-63""")

    # Funções de manipulação
    def adicionar_produto():
        st.session_state.produtos.append({"id": str(uuid.uuid4()), "Produto": "", "Quant.": 1, "Preço Unit.": 0.0, "Observações": ""})
        st.rerun()
    def remover_produto():
        if len(st.session_state.produtos) > 1: st.session_state.produtos.pop()
        st.rerun()
    def limpar_produtos():
        st.session_state.produtos = [{"id": str(uuid.uuid4()), "Produto": "", "Quant.": 1, "Preço Unit.": 0.0, "Observações": ""}]
        st.rerun()

    # Edição dinâmica dos produtos
    st.header("Itens da Proposta")
    produtos_editados = []
    for i, item in enumerate(st.session_state.produtos):
        with st.expander(f"Produto {i+1}", expanded=True):
            col1, col2 = st.columns([3,1])
            with col1:
                nome = st.text_input("Nome do Produto", item.get("Produto",""), key=f"nome_{item['id']}")
                obs = st.text_input("Observações", item.get("Observações",""), key=f"obs_{item['id']}")
            with col2:
                qtd = st.number_input("Quant.", min_value=0.0, value=float(item.get("Quant.",0)), key=f"qtd_{item['id']}")
                preco = st.number_input("Preço Unit. (R$)", min_value=0.0, value=float(item.get("Preço Unit.",0.0)), key=f"preco_{item['id']}")
            total = qtd * preco
            st.markdown(f"**Total do Item: R$ {total:,.2f}**")
            produtos_editados.append({"Produto": nome,"Quant.":qtd,"Preço Unit.":preco,"Observações":obs,"Total (R$)":total})

    # Atualiza session_state
    for idx, (old,new) in enumerate(zip(st.session_state.produtos, produtos_editados)):
        st.session_state.produtos[idx].update(new)

    # Botões
    col1,col2,col3 = st.columns(3)
    with col1: st.button("➕ Adicionar Produto", on_click=adicionar_produto)
    with col2: st.button("➖ Remover Último", on_click=remover_produto, disabled=len(st.session_state.produtos)<=1)
    with col3: st.button("🗑️ Limpar Todos", on_click=limpar_produtos)

    # Resumo
    df_final = pd.DataFrame(produtos_editados)
    st.subheader("Resumo da Proposta")
    st.dataframe(df_final, use_container_width=True)
    total_geral = df_final["Total (R$)"].sum() if not df_final.empty else 0.0
    st.markdown(f"**Total Geral: R$ {total_geral:,.2f}**")

    # Condições Comerciais
    st.markdown("---")
    st.subheader("Condições Comerciais")
    st.markdown(f"- **Validade da Proposta:** {validade_proposta}")
    st.markdown(f"- **Prazo de Pagamento:** {prazo_pagamento}")
    st.markdown(f"- **Prazo de Entrega:** {prazo_entrega}")
    st.markdown("- **Impostos:** Nos preços estão incluídos todos os custos indispensáveis à perfeita execução do objeto.")

    # Data
    meses_pt = {1:"janeiro",2:"fevereiro",3:"março",4:"abril",5:"maio",6:"junho",7:"julho",8:"agosto",9:"setembro",10:"outubro",11:"novembro",12:"dezembro"}
    data_formatada = f"{data_proposta.day} de {meses_pt[data_proposta.month]} de {data_proposta.year}"
    st.markdown(f"\n\n\n**Rio de Janeiro, {data_formatada}.**")
    st.markdown("**Gustavo Luiz Freitas de Sousa**")

    # ---------- Função gerar PDF completa ----------
    def gerar_pdf_bytes(cliente, data_formatada, df_final, total_geral, prazo_pagamento, prazo_entrega, validade_proposta):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elementos = []
    estilos = getSampleStyleSheet()
    estilos.add(ParagraphStyle(name="CenterTitle", alignment=TA_CENTER, fontSize=22, leading=26, spaceAfter=12, fontName="Helvetica-Bold"))
    estilos.add(ParagraphStyle(name="SectionTitle", alignment=TA_LEFT, fontSize=12, leading=14, spaceAfter=6, fontName="Helvetica-BoldOblique"))
    estilos.add(ParagraphStyle(name="NormalLeft", alignment=TA_LEFT, fontSize=10, leading=12))

    # Logo
    try:
        if "logo" in st.session_state and st.session_state["logo"] is not None:
            logo = Image(st.session_state["logo"])
        else:
            logo = Image("logo.jpg")
        logo.drawHeight = 50
        logo.drawWidth = 120
        logo.hAlign = 'CENTER'
        elementos.append(logo)
        elementos.append(Spacer(1, 8))
    except Exception:
        elementos.append(Spacer(1, 20))

    # Título central
    elementos.append(Paragraph("Proposta Comercial", estilos["CenterTitle"]))
    elementos.append(Spacer(1, 6))

    # A/C
    elementos.append(Paragraph(f"A/C {cliente}", estilos["NormalLeft"]))
    elementos.append(Spacer(1, 8))

    # Dados fixos
    elementos.append(Paragraph("Dados da Empresa", estilos["SectionTitle"]))
    dados_empresa = [
        "Nome da Empresa: GUSTAVO LUIZ FREITAS DE SOUSA",
        "CNPJ: 41.640.044/0001-63",
        "IE: 33.822.412.281",
        "IM: 1.304.930-0",
        "Endereço: Rua Henrique Fleiuss, 444 - Tijuca",
        "Cidade/UF: Rio de Janeiro / RJ",
        "CEP: 20521-260"
    ]
    for linha in dados_empresa:
        elementos.append(Paragraph(linha, estilos["NormalLeft"]))
    elementos.append(Spacer(1, 6))

    elementos.append(Paragraph("Dados para Contato", estilos["SectionTitle"]))
    contato = ["E-mail: gustavo_lfs@hotmail.com", "Telefone: (21) 996913090"]
    for linha in contato:
        elementos.append(Paragraph(linha, estilos["NormalLeft"]))
    elementos.append(Spacer(1, 6))

    elementos.append(Paragraph("Dados Bancários", estilos["SectionTitle"]))
    bancarios = ["Banco: Inter", "Agência: 0001", "Conta: 12174848-0", "PIX: 41.640.044/0001-63"]
    for linha in bancarios:
        elementos.append(Paragraph(linha, estilos["NormalLeft"]))
    elementos.append(Spacer(1, 10))

    # Itens da proposta (tabela)
    elementos.append(Paragraph("Itens da Proposta", estilos["SectionTitle"]))
    if not df_final.empty:
        df_tabela = df_final.copy()
        if "Preço Unit." in df_tabela.columns:
            df_tabela = df_tabela.rename(columns={"Preço Unit.": "Preço Unit. (R$)"})
        if "Preço Unit. (R$)" in df_tabela.columns:
            df_tabela["Preço Unit. (R$)"] = df_tabela["Preço Unit. (R$)"].apply(formato_brl_num)
        if "Total (R$)" in df_tabela.columns:
            df_tabela["Total (R$)"] = df_tabela["Total (R$)"].apply(formato_brl_num)

        header = list(df_tabela.columns)
        dados_tabela = [header]
        for row in df_tabela.itertuples(index=False, name=None):
            linha = [Paragraph(str(c).replace("\n", " "), estilos["NormalLeft"]) for c in row]
            dados_tabela.append(linha)

        margem_esq = doc.leftMargin
        margem_dir = doc.rightMargin
        largura_total = A4[0] - margem_esq - margem_dir
        col_widths = []
        for col in header:
            if "Produto" in col:
                col_widths.append(largura_total * 0.35)
            elif "Observações" in col:
                col_widths.append(largura_total * 0.25)
            elif "Quant." in col:
                col_widths.append(largura_total * 0.1)
            elif "Preço Unit." in col:
                col_widths.append(largura_total * 0.15)
            else:
                col_widths.append(largura_total * 0.15)

        tabela = Table(dados_tabela, colWidths=col_widths, repeatRows=1)
        cor_header = st.session_state.get("cor_tabela", "#D3D3D3")
        estilo_table = TableStyle([
            ("BOX", (0,0), (-1,-1), 1, colors.black),
            ("INNERGRID", (0,0), (-1,-1), 0.4, colors.black),
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor(cor_header)),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1, -1), 9),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ])
        for ci, col in enumerate(header):
            if "Produto" in col or "Observações" in col:
                estilo_table.add("ALIGN", (ci,1), (ci,-1), "LEFT")
            else:
                estilo_table.add("ALIGN", (ci,1), (ci,-1), "CENTER")
        tabela.setStyle(estilo_table)
        elementos.append(tabela)
        elementos.append(Spacer(1, 8))
        elementos.append(Paragraph(f"Total Geral: R$ {formato_brl_num(total_geral)}", estilos["NormalLeft"]))
        elementos.append(Spacer(1, 10))
    else:
        elementos.append(Paragraph("Nenhum item adicionado.", estilos["NormalLeft"]))
        elementos.append(Spacer(1, 10))

    # Condições comerciais
    elementos.append(Paragraph("Condições Comerciais", estilos["SectionTitle"]))
    elementos.append(Paragraph(f"Validade da Proposta: {validade_proposta}", estilos["NormalLeft"]))
    elementos.append(Paragraph(f"Prazo de Pagamento: {prazo_pagamento}", estilos["NormalLeft"]))
    elementos.append(Paragraph(f"Prazo de Entrega: {prazo_entrega}", estilos["NormalLeft"]))
    elementos.append(Paragraph("Impostos: Nos preços estão incluídos todos os custos indispensáveis à perfeita execução do objeto.", estilos["NormalLeft"]))
    elementos.append(Spacer(1, 8))

    # Data + assinatura + nome
    elementos.append(Paragraph(f"Rio de Janeiro, {data_formatada}.", estilos["NormalLeft"]))
    try:
        if "assinatura" in st.session_state and st.session_state["assinatura"] is not None:
            assinatura_img = Image(st.session_state["assinatura"])
            assinatura_img.drawHeight = 50
            assinatura_img.drawWidth = 120
            assinatura_img.hAlign = 'LEFT'
            elementos.append(assinatura_img)
    except Exception:
        pass
    elementos.append(Paragraph("Gustavo Luiz Freitas de Sousa", estilos["NormalLeft"]))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()


# ---------- Página de Configurações ----------
elif st.session_state["pagina"] == "config":
    st.title("Configurações")
    
    if st.button("⬅️ Voltar para Proposta"):
        st.session_state["pagina"] = "proposta"

    st.markdown("### Personalizações")

    # Upload de logo
    logo = st.file_uploader("Carregar Logo", type=["png","jpg"])
    if logo is not None:
        st.session_state["logo"] = logo

    # Upload de assinatura
    assinatura = st.file_uploader("Carregar Assinatura", type=["png","jpg"])
    if assinatura is not None:
        st.session_state["assinatura"] = assinatura

    # Cor principal da tabela
    cor_tabela = st.color_picker("Cor Principal da Tabela", "#D3D3D3")  # cor default lightgrey
    st.session_state["cor_tabela"] = cor_tabela

