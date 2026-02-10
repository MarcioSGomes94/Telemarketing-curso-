# =========================
# IMPORTS
# =========================
import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO

# =========================
# CONFIGURAÇÃO
# =========================
st.set_page_config(
    page_title="Dynamic Data Dashboard",
    page_icon="📊",
    layout="wide"
)

custom_params = {"axes.spines.right": False, "axes.spines.top": False}
sns.set_theme(style="ticks", rc=custom_params)

# =========================
# FUNÇÕES
# =========================

@st.cache_data(show_spinner=True)
def load_data(file):
    try:
        return pd.read_csv(file, sep=";")
    except Exception:
        return pd.read_excel(file)


@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    return output.getvalue()


def calculate_percentage(df, column):
    if column not in df.columns or df.empty:
        return pd.DataFrame()

    return (
        df[column]
        .value_counts(normalize=True)
        .mul(100)
        .to_frame(name="Percentual")
        .sort_index()
    )


# =========================
# APP
# =========================

def main():

    st.title("📊 Dynamic Data Dashboard")
    st.markdown("Dashboard automático baseado no arquivo anexado.")
    st.markdown("---")

    # Upload
    st.sidebar.header("Upload do Arquivo")
    file = st.sidebar.file_uploader(
        "Envie um arquivo CSV ou XLSX",
        type=["csv", "xlsx"]
    )

    if file is None:
        st.info("Aguardando upload do arquivo...")
        return

    df_raw = load_data(file)
    df = df_raw.copy()

    st.subheader("Visualização inicial")
    st.dataframe(df.head(), use_container_width=True)

    st.markdown("---")
    st.sidebar.header("Filtros Dinâmicos")

    # =========================
    # FILTROS AUTOMÁTICOS
    # =========================

    filtros = {}

    with st.sidebar.form("Filtros"):

        for col in df.columns:

            # NUMÉRICAS
            if pd.api.types.is_numeric_dtype(df[col]):

                min_val = float(df[col].min())
                max_val = float(df[col].max())

                if min_val != max_val:
                    filtros[col] = st.slider(
                        label=col,
                        min_value=min_val,
                        max_value=max_val,
                        value=(min_val, max_val)
                    )

            # CATEGÓRICAS
            elif pd.api.types.is_object_dtype(df[col]):

                valores = sorted(df[col].dropna().unique())
                filtros[col] = st.multiselect(
                    label=col,
                    options=valores,
                    default=valores
                )

        aplicar = st.form_submit_button("Aplicar filtros")

    # Aplicação dos filtros
    for col, valor in filtros.items():

        if isinstance(valor, tuple):
            df = df[(df[col] >= valor[0]) & (df[col] <= valor[1])]

        elif isinstance(valor, list):
            if valor:
                df = df[df[col].isin(valor)]

    # =========================
    # RESULTADO FILTRADO
    # =========================

    st.subheader("Dados após filtros")
    st.dataframe(df.head(), use_container_width=True)

    st.download_button(
        "📥 Download dados filtrados (Excel)",
        data=to_excel(df),
        file_name="dados_filtrados.xlsx"
    )

    st.markdown("---")

    # =========================
    # ANÁLISE AUTOMÁTICA
    # =========================

    st.subheader("Análise Automática")

    colunas_categoricas = df.select_dtypes(include="object").columns.tolist()

    if len(colunas_categoricas) > 0:

        coluna_escolhida = st.selectbox(
            "Selecione uma coluna categórica para análise percentual",
            colunas_categoricas
        )

        raw_perc = calculate_percentage(df_raw, coluna_escolhida)
        filtered_perc = calculate_percentage(df, coluna_escolhida)

        col1, col2 = st.columns(2)

        with col1:
            st.write("### Dados Originais (%)")
            st.dataframe(raw_perc)
            st.download_button(
                "Download original",
                data=to_excel(raw_perc),
                file_name="original_percentual.xlsx",
                key="orig"
            )

        with col2:
            st.write("### Dados Filtrados (%)")
            st.dataframe(filtered_perc)
            st.download_button(
                "Download filtrado",
                data=to_excel(filtered_perc),
                file_name="filtrado_percentual.xlsx",
                key="filt"
            )

        # =========================
        # GRÁFICO
        # =========================

        fig, ax = plt.subplots(1, 2, figsize=(10, 4))

        if not raw_perc.empty:
            raw_perc["Percentual"].plot(
                kind="bar",
                ax=ax[0]
            )
            ax[0].set_title("Original")

        if not filtered_perc.empty:
            filtered_perc["Percentual"].plot(
                kind="bar",
                ax=ax[1]
            )
            ax[1].set_title("Filtrado")

        st.pyplot(fig)

    else:
        st.warning("Nenhuma coluna categórica encontrada para análise percentual.")

    st.markdown("---")

    # =========================
    # ESTATÍSTICAS DESCRITIVAS
    # =========================

    st.subheader("Estatísticas Descritivas")
    st.dataframe(df.describe(), use_container_width=True)


if __name__ == "__main__":
    main()
