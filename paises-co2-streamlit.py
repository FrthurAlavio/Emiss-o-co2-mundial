import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Título do app
st.title("Comparador Global de Emissões de CO₂📊")
st.subheader('Dados de Our world in Data -') 
st.link_button("link deles (em inglês)", "https://ourworldindata.org/co2-and-greenhouse-gas-emissions?utm_source=pocket_shared")


@st.cache_data
def carregar_dados():
    caminho_arquivo = 'owid-co2-data.csv'
    return pd.read_csv(caminho_arquivo)

df = carregar_dados()

# Lista de anos disponíveis
anos_disponiveis = sorted(df['year'].dropna().unique())
anos_validos = [ano for ano in anos_disponiveis if ano >= 1990]

# Seleção de dois anos para comparação
col1, col2 = st.columns(2)
with col1:
    ano1 = st.selectbox("Escolha o 1º ano:", anos_validos, index=len(anos_validos)-5)
with col2:
    ano2 = st.selectbox("Escolha o 2º ano para comparar:", anos_validos, index=len(anos_validos)-1)

# Filtrar países com dados em ambos os anos
df_ano1 = df[df['year'] == ano1]
df_ano2 = df[df['year'] == ano2]
paises_comuns = sorted(set(df_ano1['country']).intersection(set(df_ano2['country'])))
paises_selecionados = st.multiselect("Escolha um ou mais países:", paises_comuns)

if not paises_selecionados:
    st.info("Selecione pelo menos um país para comparar.")
else:
    df1 = df_ano1[df_ano1['country'].isin(paises_selecionados)]
    df2 = df_ano2[df_ano2['country'].isin(paises_selecionados)]

    media1 = df_ano1['co2'].mean()
    media2 = df_ano2['co2'].mean()

    st.subheader("📈 Comparação de Emissões entre os anos selecionados")
    fig, ax = plt.subplots()
    ax.bar(df1['country'], df1['co2'], width=0.4, label=f"{ano1}", align='edge')
    ax.bar(df2['country'], df2['co2'], width=-0.4, label=f"{ano2}", align='edge')
    ax.axhline(media1, color='blue', linestyle='--', label=f'Média Global {ano1} ({round(media1, 1)} Mt)')
    ax.axhline(media2, color='green', linestyle='--', label=f'Média Global {ano2} ({round(media2, 1)} Mt)')
    ax.set_ylabel("Emissões de CO₂ (milhões de toneladas)")
    ax.set_xticks(range(len(paises_selecionados)))
    ax.set_xticklabels(paises_selecionados, rotation=45, ha='right')
    ax.legend()
    st.pyplot(fig)

    st.markdown("### 📌 Análise por país")
    for pais in paises_selecionados:
        v1 = df1[df1['country'] == pais]['co2'].values[0]
        v2 = df2[df2['country'] == pais]['co2'].values[0]
        st.write(f"**{pais}**:")
        st.write(f"- Em {ano1}: {round(v1)} Milhões de Toneladas ({round(v1/media1, 2)}x a média global)")
        st.write(f"- Em {ano2}: {round(v2)} Milhões de Toneladas ({round(v2/media2, 2)}x a média global)")
        dif = v2 - v1
        if dif > 0:
            st.success(f"Aumento de {round(dif)} Milhões de Toneladas entre {ano1} e {ano2}")
        elif dif < 0:
            st.warning(f"Redução de {round(abs(dif))} Milhões de Toneladas entre {ano1} e {ano2}")
        else:
            st.info("Sem variação entre os anos")
