import streamlit as st
from fpdf import FPDF
from io import BytesIO
import num2words
import os
from datetime import datetime


class CustomPDF(FPDF):
    def header(self):
        pass


def data_em_texto(data):
    meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março',
        4: 'Abril', 5: 'Maio', 6: 'Junho',
        7: 'Julho', 8: 'Agosto', 9: 'Setembro',
        10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }

    return f"{data.day} de {meses[data.month]} de {data.year}"


def generate_pdf(nome_cliente, quantidade, valor, data_recibo, logo_path, assinatura_path):
    pdf = CustomPDF()

    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    pdf.add_page()

    # Logo
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=87.5, y=30, w=35)

    # Título
    pdf.set_font('Times', 'B', 18)
    pdf.ln(60)
    pdf.cell(0, 10, 'RECIBO DE PAGAMENTO', ln=True, align='C')

    # Texto
    pdf.set_font('Times', '', 11)
    pdf.ln(25)

    valor_extenso = num2words.num2words(valor, lang='pt_BR', to='currency')
    quantidade_extenso = num2words.num2words(quantidade, lang='pt_BR')

    valor_corrigido = f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    if quantidade < 1000:
        quantidade_corrigido = quantidade
    else:
        quantidade_corrigido = f"{quantidade:,}".replace(',', '.')

    texto = (
        f"Eu, Maria Verônica Gomes Pereira Avelino, CPF: 047.589.934-24, "
        f"recebi do(a) {nome_cliente} no valor de R$ {valor_corrigido} ({valor_extenso}), "
        f"referente ao fornecimento de {quantidade_corrigido} ({quantidade_extenso}) salgados."
    )

    pdf.multi_cell(0, 5, texto, align='J')

    # Data
    pdf.ln(40)
    data_formatada = data_em_texto(data_recibo)
    pdf.cell(0, 10, f"Lajes/RN, {data_formatada}", ln=True, align='C')

    # Assinatura
    pdf.ln(50)
    if os.path.exists(assinatura_path):
        pdf.image(assinatura_path, x=65, w=80)

    pdf.ln(-5)
    pdf.set_font('Times', '', 11)
    pdf.cell(0, 10, "_______________________________________", ln=True, align='C')
    pdf.ln(-5)
    pdf.cell(0, 10, "Maria Verônica Gomes Pereira Avelino", ln=True, align='C')

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_bytes)


# ========================
# STREAMLIT UI
# ========================

st.title('Gerador de Recibo')

# 1. Nome
nome_cliente = st.text_input('Nome do Cliente')

# 2. Quantidade
quantidade = st.number_input('Quantidade de Salgados', min_value=1, step=1)

# 3. Valor
valor = st.number_input('Valor Total (R$)', min_value=0.0, step=0.01)

# 4. Data (editável)
data_recibo = st.date_input('Data do Recibo', value=datetime.today())

# Caminhos das imagens
BASE_DIR = os.path.dirname(__file__)
logo_path = os.path.join(BASE_DIR, "images", "logo.png")
assinatura_path = os.path.join(BASE_DIR, "images", "assinatura.png")


if st.button('Gerar PDF'):

    if not nome_cliente:
        st.error("Informe o nome do cliente.")
        st.stop()

    pdf_bytes = generate_pdf(
        nome_cliente,
        quantidade,
        valor,
        data_recibo,
        logo_path,
        assinatura_path
    )

    nome_cliente_saida = "_".join(nome_cliente.lower().split())

    st.download_button(
        label="Baixar PDF",
        data=pdf_bytes,
        file_name=f"recibo_{nome_cliente_saida}.pdf",
        mime="application/pdf"
    )