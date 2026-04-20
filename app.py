import streamlit as st
from fpdf import FPDF
from io import BytesIO
import num2words
import os
from datetime import datetime

class CustomPDF(FPDF):
    def header(self):
        pass  # Remove cabeçalho automático


def data_atual_em_texto():
    meses = {
        'January': 'Janeiro',
        'February': 'Fevereiro',
        'March': 'Março',
        'April': 'Abril',
        'May': 'Maio',
        'June': 'Junho',
        'July': 'Julho',
        'August': 'Agosto',
        'September': 'Setembro',
        'October': 'Outubro',
        'November': 'Novembro',
        'December': 'Dezembro'
    }

    data = datetime.now()
    data_formatada = data.strftime('%d de %B de %Y')

    mes = data_formatada.split('de')[1].strip()
    data_formatada = data_formatada.replace(mes, meses[mes])

    return data_formatada


def generate_pdf(nome_cliente, quantidade, valor, logo_path, assinatura_path):
    pdf = CustomPDF()

    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    pdf.add_page()

    # Verificação de arquivos
    if not os.path.exists(logo_path):
        raise FileNotFoundError(f"Logo não encontrada: {logo_path}")

    if not os.path.exists(assinatura_path):
        raise FileNotFoundError(f"Assinatura não encontrada: {assinatura_path}")

    # Logo
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

    # Formatação brasileira
    valor_corrigido = f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    if quantidade < 1000:
        quantidade_corrigido = quantidade
    else:
        quantidade_corrigido = f"{quantidade:,}".replace(',', '.')

    texto = (
        f"Eu, Maria Verônica Gomes Pereira Avelino, CPF: 047.589.934-24, "
        f"recebi do(a) {nome_cliente} o valor de R$ {valor_corrigido} ({valor_extenso}), "
        f"referente ao fornecimento de {quantidade_corrigido} ({quantidade_extenso}) salgados."
    )

    pdf.multi_cell(0, 5, texto, align='J')

    # Data
    pdf.ln(40)
    data_hoje = data_atual_em_texto()
    pdf.cell(0, 10, f"Lajes/RN, {data_hoje}", ln=True, align='C')

    # Assinatura
    pdf.ln(50)
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

nome_cliente = st.text_input('Nome do Cliente')
quantidade = st.number_input('Quantidade de Itens', min_value=1, step=1)
valor = st.number_input('Valor Total (R$)', min_value=0.0, step=0.01)

# Caminhos locais das imagens
BASE_DIR = os.path.dirname(__file__)

logo_path = os.path.join(BASE_DIR, "images", "logo.png")
assinatura_path = os.path.join(BASE_DIR, "images", "assinatura.png")

if st.button('Gerar PDF'):
    pdf_bytes = generate_pdf(
        nome_cliente,
        quantidade,
        valor,
        logo_path,
        assinatura_path
    )

    nome_cliente_saida = nome_cliente.lower().split()
    nome_cliente_saida = "_".join(nome_cliente_saida)

    st.download_button(
        label="Baixar PDF",
        data=pdf_bytes,
        file_name=f"recibo_{nome_cliente_saida}.pdf",
        mime="application/pdf"
    )