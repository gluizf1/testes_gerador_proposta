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

# ---------- Helper: formata número no padrão brasileiro (1.234,56) ----------
def formato_brl_num(valor):
    try:
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(valor)

# ---------- Configuração inicial ----------
st.set_page_config(page_title="Gerador de Proposta", layout="wide")

# ---------- Sidebar com botão de Configurações ----------
col1, col2 = st.sidebar.columns([8, 1])
with col2:
    if st.button("⚙️", help="Abrir Configurações"):
        st.session_state["pagina"] = "config"

# Define página padrão
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "proposta"

# ---------- Página de Proposta ----------
if st.session_state["pagina"] == "proposta":
    st.title("Gerador de Proposta Comercial")

    # Sidebar: dados da proposta
    st.sidebar.header("Detalhes da Proposta")
    cliente = st.sidebar.text_input("Nome do Cliente", "Cliente Exemplo")
    data_proposta = st.sidebar.date_input("Data da Proposta", value=date.today(), format="DD/MM/YYYY")
    prazo_pagamento = st.sidebar.text_input("Prazo de Pagamento", "À vista")
    prazo_entrega = st.sidebar.text_input("Prazo de Entrega", "15 dias")
    validade_proposta = st.sidebar.text_input("Validade da Proposta", "30 dias")

    st.sidebar.markdown("---")
    st.sidebar.header("Upload de Produtos")
    uploaded_file = st.sidebar.file_uploader(
        "Enviar planilha (.xlsx) com colunas: Produto, Quant., Preço Unit., Observações", 
        type=["xlsx"]
    )

    # Função para gerar Excel em memória
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

    with st.sidebar:
        st.download_button(
            label="Baixar Modelo Excel",
            data=gerar_excel_modelo(),
            file_name="produtos_modelo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # ---------- Processar upload ----------
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

    # ---------- Inicializa produtos ----------
    if "produtos" not in st.session_state:
        st.session_state.produtos = [{"id": str(uuid.uuid4()), "Produto": "Produto Exemplo", "Quant.": 1, "Preço Unit.": 100.0, "Observações": ""}]

    # ---------- Dados fixos da empresa ----------
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

    # ---------- Funções para manipular produtos ----------
    def adicionar_produto():
        st.session_state.produtos.append({"id": str(uuid.uuid4()), "Produto": "", "Quant.": 1, "Preço Unit.": 0.0, "Observações": ""})
        st.rerun()

    def remover_produto():
        if len(st.session_state.produtos) > 1:
            st.session_state.produtos.pop()
        st.rerun()

    def limpar_produtos():
        st.session_state.produtos = [{"id": str(uuid.uuid4()), "Produto": "", "Quant.": 1, "Preço Unit.": 0.0, "Observações": ""}]
        st.rerun()

    # ---------- Edição dinâmica dos produtos ----------
    st.header("Itens da Proposta")
    produtos_editados = []
    for i, item in enumerate(st.session_state.produtos):
        with st.expander(f"Produto {i+1}", expanded=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                nome = st.text_input("Nome do Produto", item.get("Produto", ""), key=f"nome_{item['id']}")
                obs = st.text_input("Observações", item.get("Observações", ""), key=f"obs_{item['id']}")
            with col2:
                qtd = st.number_input("Quant.", min_value=0.0, value=float(item.get("Quant.", 0)), key=f"qtd_{item['id']}")
                preco = st.number_input("Preço Unit. (R$)", min_value=0.0, value=float(item.get("Preço Unit.", 0.0)), key=f"preco_{item['id']}")
            total = qtd * preco
            st.markdown(f"**Total do Item: R$ {total:,.2f}**")
            produtos_editados.append({"Produto": nome, "Quant.": qtd, "Preço Unit.": preco, "Observações": obs, "Total (R$)": total})

    # Atualiza session_state
    for idx, (old, new) in enumerate(zip(st.session_state.produtos, produtos_editados)):
        st.session_state.produtos[idx].update(new)

    # ---------- Botões de ação ----------
    col1, col2, col3 = st.columns(3)
    with col1: st.button("➕ Adicionar Produto", on_click=adicionar_produto)
    with col2: st.button("➖ Remover Último", on_click=remover_produto, disabled=len(st.session_state.produtos) <= 1)
    with col3: st.button("🗑️ Limpar Todos", on_click=limpar_produtos)

    # ---------- Resumo e total ----------
    df_final = pd.DataFrame(produtos_editados)
    st.subheader("Resumo da Proposta")
    st.dataframe(df_final, use_container_width=True)
    total_geral = df_final["Total (R$)"].sum() if not df_final.empty else 0.0
    st.markdown(f"**Total Geral: R$ {total_geral:,.2f}**")

    # ---------- Condições Comerciais ----------
    st.markdown("---")
    st.subheader("Condições Comerciais")
    st.markdown(f"- **Validade da Proposta:** {validade_proposta}")
    st.markdown(f"- **Prazo de Pagamento:** {prazo_pagamento}")
    st.markdown(f"- **Prazo de Entrega:** {prazo_entrega}")
    st.markdown("- **Impostos:** Nos preços estão incluídos todos os custos indispensáveis à perfeita execução do objeto.")

    # ---------- Data formatada ----------
    meses_pt = {1:"janeiro",2:"fevereiro",3:"março",4:"abril",5:"maio",6:"junho",7:"julho",8:"agosto",9:"setembro",10:"outubro",11:"novembro",12:"dezembro"}
    dia = data_proposta.day
    mes = meses_pt[data_proposta.month]
    ano = data_proposta.year
    data_formatada = f"{dia} de {mes} de {ano}"

    st.markdown(f"\n\n\n**Rio de Janeiro, {data_formatada}.**")
    st.markdown("**Gustavo Luiz Freitas de Sousa**")

    # ---------- Botão de download PDF ----------
    # (Mesma função de gerar_pdf_bytes do seu código original)
    # Para não alongar muito, podemos manter a função de gerar PDF exatamente como você tinha

# ---------- Página de Configurações ----------
elif st.session_state["pagina"] == "config":
    st.title("⚙️ Configurações")
    if st.button("⬅️ Voltar para Proposta"):
        st.session_state["pagina"] = "proposta"

    st.markdown("### Personalizações")
    logo = st.file_uploader("Carregar Logo", type=["png", "jpg"])
    if logo:
        st.session_state["logo"] = logo
    assinatura = st.file_uploader("Carregar Assinatura", type=["png", "jpg"])
    if assinatura:
        st.session_state["assinatura"] = assinatura
    cor = st.color_picker("Cor Principal da Tabela", "#004AAD")
    st.session_state["cor_principal"] = cor
