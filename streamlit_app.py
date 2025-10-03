import streamlit as st
import pandas as pd
from datetime import datetime, date
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# ---------- Função utilitária ----------
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ---------- Configuração inicial ----------
st.set_page_config(page_title="Proposta Comercial", page_icon="📄", layout="wide")

# ---------- Sidebar: menu principal ----------
menu = st.sidebar.radio(
    "📌 Navegação",
    ["📝 Proposta", "⚙️ Configurações"]
)

# ---------- Aba de Proposta ----------
if menu == "📝 Proposta":
    st.title("📝 Proposta Comercial")

    # Dados gerais
    data_proposta = st.sidebar.date_input(
        "Data da Proposta", 
        value=date.today(), 
        format="DD/MM/YYYY"
    )
    prazo_pagamento = st.sidebar.text_input("Prazo de Pagamento", "À vista")

    cliente = st.sidebar.text_input("Cliente")
    projeto = st.sidebar.text_input("Projeto")

    # Entrada de itens
    st.subheader("Itens da Proposta")
    df = pd.DataFrame(columns=["Descrição", "Quantidade", "Valor Unitário", "Total"])

    with st.form("form_itens", clear_on_submit=True):
        descricao = st.text_input("Descrição")
        quantidade = st.number_input("Quantidade", min_value=1, value=1)
        valor_unitario = st.number_input("Valor Unitário", min_value=0.0, value=0.0, format="%.2f")
        adicionar = st.form_submit_button("Adicionar Item")

        if adicionar and descricao:
            novo_item = {
                "Descrição": descricao,
                "Quantidade": quantidade,
                "Valor Unitário": valor_unitario,
                "Total": quantidade * valor_unitario
            }
            df = pd.concat([df, pd.DataFrame([novo_item])], ignore_index=True)

    if not df.empty:
        st.table(df)

    # Geração do PDF
    if st.button("📄 Gerar PDF da Proposta"):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)

        styles = getSampleStyleSheet()
        estilo_titulo = ParagraphStyle(
            "Titulo", parent=styles["Heading1"], alignment=TA_CENTER, spaceAfter=20
        )

        story = []

        # Cabeçalho
        story.append(Paragraph("Proposta Comercial", estilo_titulo))
        story.append(Paragraph(f"Cliente: {cliente}", styles["Normal"]))
        story.append(Paragraph(f"Projeto: {projeto}", styles["Normal"]))
        story.append(Paragraph(f"Data: {data_proposta.strftime('%d/%m/%Y')}", styles["Normal"]))
        story.append(Paragraph(f"Prazo de Pagamento: {prazo_pagamento}", styles["Normal"]))
        story.append(Spacer(1, 20))

        # Tabela
        if not df.empty:
            dados = [["Descrição", "Qtd", "V.Unitário", "Total"]]
            for _, row in df.iterrows():
                dados.append([
                    row["Descrição"],
                    int(row["Quantidade"]),
                    formatar_moeda(row["Valor Unitário"]),
                    formatar_moeda(row["Total"])
                ])

            tabela = Table(dados, hAlign="LEFT")
            tabela.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(tabela)

        doc.build(story)
        buffer.seek(0)

        st.download_button(
            "⬇️ Baixar PDF",
            buffer,
            file_name=f"Proposta_{cliente}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )

# ---------- Aba de Configurações ----------
elif menu == "⚙️ Configurações":
    st.title("⚙️ Configurações do Sistema")

    logo = st.file_uploader("Carregar Logo", type=["png", "jpg"])
    assinatura = st.file_uploader("Carregar Assinatura", type=["png", "jpg"])
    cor_principal = st.color_picker("Cor principal", "#004AAD")

    st.write("Essas configurações podem futuramente ser salvas em cache ou arquivo para reaproveitar.")
