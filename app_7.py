# =========================
# IMPORTS
# =========================
import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO

# =========================
# CONFIG VISUAL
# =========================
custom_params = {"axes.spines.right": False, "axes.spines.top": False}
sns.set_theme(style="ticks", rc=custom_params)

st.set_page_config(
    page_title="Telemarketing Analysis",
    page_icon="📊",
    layout="wide"
)

# =========================
# FUNÇÕES
# =========================

@st.cache_data(show_spinner=True)
def load_data(file_data):
    try:
        return pd.read_csv(file_data, sep=";")
    except Exception:
        return pd.read_excel(file_data)


@st.cache_data
def multiselect_filter(df, col, selected):
    if "all" in selected:
        return df
    return df[df[col].isin(selected)].reset_index(drop=True)


@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    return output.getvalue()


# =========================
# APP
# =========================

def main():

    st.title("📊 Telemarketing Analysis")
    st.markdown("---")

    # Sidebar
    st.sidebar.header("Upload de Arquivo")
    file = st.sidebar.file_uploader(
        "Bank marketing data", type=["csv", "xlsx"]
    )

    if file is None:
        st.info("Faça upload de um arquivo para começar.")
        return

    bank_raw = load_data(file)
    bank = bank_raw.copy()

    st.subheader("Prévia dos dados")
    st.dataframe(bank_raw.head(), use_container_width=True)

    # =========================
    # FILTROS
    # =========================
    with st.sidebar.form("Filtros"):

        graph_type = st.radio("Tipo de gráfico", ["Barras", "Pizza"])

        # Idade
        min_age, max_age = int(bank.age.min()), int(bank.age.max())
        age_range = st.slider(
            "Idade",
            min_value=min_age,
            max_value=max_age,
            value=(min_age, max_age)
        )

        # Função auxiliar para multiselect
        def create_multiselect(col_name, label):
            values = sorted(bank[col_name].unique().tolist())
            values.append("all")
            return st.multiselect(label, values, default=["all"])

        jobs = create_multiselect("job", "Profissão")
        marital = create_multiselect("marital", "Estado civil")
        default = create_multiselect("default", "Default")
        housing = create_multiselect("housing", "Financiamento imobiliário")
        loan = create_multiselect("loan", "Empréstimo")
        contact = create_multiselect("contact", "Meio de contato")
        month = create_multiselect("month", "Mês do contato")
        day = create_multiselect("day_of_week", "Dia da semana")

        apply_filters = st.form_submit_button("Aplicar filtros")

    # Aplicando filtros
    bank = (
        bank.query("age >= @age_range[0] and age <= @age_range[1]")
            .pipe(multiselect_filter, "job", jobs)
            .pipe(multiselect_filter, "marital", marital)
            .pipe(multiselect_filter, "default", default)
            .pipe(multiselect_filter, "housing", housing)
            .pipe(multiselect_filter, "loan", loan)
            .pipe(multiselect_filter, "contact", contact)
            .pipe(multiselect_filter, "month", month)
            .pipe(multiselect_filter, "day_of_week", day)
    )

    st.markdown("---")
    st.subheader("Dados após filtros")
    st.dataframe(bank.head(), use_container_width=True)

    # Download tabela filtrada
    st.download_button(
        "📥 Download tabela filtrada (Excel)",
        data=to_excel(bank),
        file_name="bank_filtered.xlsx"
    )

    # =========================
    # CÁLCULO PERCENTUAL
    # =========================

    def calculate_percentage(df):
        if df.empty:
            return pd.DataFrame(columns=["Percentual"])
        return (
            df["y"]
            .value_counts(normalize=True)
            .mul(100)
            .to_frame(name="Percentual")
            .sort_index()
        )

    raw_perc = calculate_percentage(bank_raw)
    filtered_perc = calculate_percentage(bank)

    st.markdown("---")
    st.subheader("Proporção de aceite (%)")

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Dados Originais")
        st.dataframe(raw_perc)
        st.download_button(
            "📥 Download",
            data=to_excel(raw_perc),
            file_name="bank_raw_y.xlsx",
            key="raw"
        )

    with col2:
        st.write("### Dados Filtrados")
        st.dataframe(filtered_perc)
        st.download_button(
            "📥 Download",
            data=to_excel(filtered_perc),
            file_name="bank_filtered_y.xlsx",
            key="filtered"
        )

    # =========================
    # GRÁFICOS
    # =========================

    fig, ax = plt.subplots(1, 2, figsize=(8, 4))

    if graph_type == "Barras":

        sns.barplot(
            x=raw_perc.index,
            y="Percentual",
            data=raw_perc,
            ax=ax[0]
        )
        ax[0].bar_label(ax[0].containers[0], fmt="%.2f")
        ax[0].set_title("Dados Originais")

        if not filtered_perc.empty:
            sns.barplot(
                x=filtered_perc.index,
                y="Percentual",
                data=filtered_perc,
                ax=ax[1]
            )
            ax[1].bar_label(ax[1].containers[0], fmt="%.2f")
            ax[1].set_title("Dados Filtrados")

    else:

        raw_perc["Percentual"].plot(
            kind="pie",
            autopct="%.2f%%",
            ax=ax[0]
        )
        ax[0].set_ylabel("")
        ax[0].set_title("Dados Originais")

        if not filtered_perc.empty:
            filtered_perc["Percentual"].plot(
                kind="pie",
                autopct="%.2f%%",
                ax=ax[1]
            )
            ax[1].set_ylabel("")
            ax[1].set_title("Dados Filtrados")

    st.pyplot(fig)


if __name__ == "__main__":
    main()
