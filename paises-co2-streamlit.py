import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
import geopandas as gpd
import importlib

# Configurações da página
st.set_page_config(layout="wide", page_title="Comparador Global de Emissões de CO₂")

# Título do app
st.title("Comparador Global de Emissões de CO₂ 📊")
st.subheader('Dados de Our World in Data')
st.link_button("Link da fonte (em inglês)", "https://ourworldindata.org/co2-and-greenhouse-gas-emissions?utm_source=pocket_shared")

# Verificação de pacotes necessários
required_packages = ["pandas", "matplotlib", "plotly", "geopandas", "numpy"]
missing_packages = []

for package in required_packages:
    try:
        importlib.import_module(package)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    st.warning(f"Atenção: as seguintes bibliotecas estão faltando: {', '.join(missing_packages)}")
    st.markdown("""
    Para instalar as bibliotecas necessárias, execute:
    ```
    pip install pandas matplotlib plotly geopandas numpy
    ```
    """)

# Funções para carregar dados
@st.cache_data
def carregar_dados():
    return pd.read_csv('owid-co2-data.csv')

@st.cache_data
def carregar_geojson():
    url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
    try:
        return gpd.read_file(url)
    except Exception as e:
        st.error(f"Erro ao carregar dados geográficos: {e}")
        return gpd.GeoDataFrame(columns=['geometry', 'name'])

# Carregando os dados
df = carregar_dados()
world = carregar_geojson()

# Padronização dos nomes dos países
if 'NAME' in world.columns:
    world = world.rename(columns={'NAME': 'country'})
elif 'ADMIN' in world.columns:
    world = world.rename(columns={'ADMIN': 'country'})
elif 'name' in world.columns:
    world = world.rename(columns={'name': 'country'})

# Mapeamento de nomes alternativos
country_mapping = {
    'United States': 'United States of America',
    'USA': 'United States of America',
    'US': 'United States of America',
    'UK': 'United Kingdom',
    'Russia': 'Russian Federation',
    'Czech Republic': 'Czechia',
    'Congo': 'Republic of the Congo',
    'Democratic Republic of Congo': 'Democratic Republic of the Congo',
    'Laos': 'Lao PDR',
    'Macedonia': 'North Macedonia',
    'Myanmar': 'Burma',
    'Ivory Coast': 'Côte d\'Ivoire',
    'Brunei': 'Brunei Darussalam',
    'Bosnia and Herzegovina': 'Bosnia and Herz.'
}

df['country_mapped'] = df['country'].map(lambda x: country_mapping.get(x, x))

# Tabs principais
tab1, tab2, tab_debug = st.tabs(["Comparação por País", "Mapas Interativos", "Depuração"])

# Lista de anos disponíveis
anos_disponiveis = sorted(df['year'].dropna().unique())
anos_validos = [ano for ano in anos_disponiveis if ano >= 1990]

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        ano1 = st.selectbox("Escolha o 1º ano:", anos_validos, index=len(anos_validos)-5, key="ano1_tab1")
    with col2:
        ano2 = st.selectbox("Escolha o 2º ano para comparar:", anos_validos, index=len(anos_validos)-1, key="ano2_tab1")

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
            st.write(f"- Em {ano1}: {round(v1)} Mt ({round(v1/media1, 2)}x a média)")
            st.write(f"- Em {ano2}: {round(v2)} Mt ({round(v2/media2, 2)}x a média)")
            dif = v2 - v1
            if dif > 0:
                st.success(f"Aumento de {round(dif)} Mt entre {ano1} e {ano2}")
            elif dif < 0:
                st.warning(f"Redução de {round(abs(dif))} Mt entre {ano1} e {ano2}")
            else:
                st.info("Sem variação entre os anos")

with tab2:
    st.header("🗺️ Mapas Interativos de Emissões de CO₂")
    ano_mapa = st.selectbox("Escolha o ano para visualizar:", anos_validos, index=len(anos_validos)-1, key="ano_mapa")
    df_ano_mapa = df[df['year'] == ano_mapa]
    map_data = world.copy()

    if 'country_mapped' in df_ano_mapa.columns:
        map_data = map_data.merge(df_ano_mapa[['country_mapped', 'co2']], left_on='country', right_on='country_mapped', how='left')
    else:
        map_data = map_data.merge(df_ano_mapa[['country', 'co2']], on='country', how='left')

    map_data['co2_categoria'] = pd.cut(
        map_data['co2'],
        bins=[0, 50, 200, 1000, 5000, float('inf')],
        labels=['Muito Baixo', 'Baixo', 'Médio', 'Alto', 'Muito Alto']
    )

    map_data = map_data.to_crs("EPSG:4326")

    try:
        fig = px.choropleth(
            map_data,
            geojson=map_data.geometry,
            locations=map_data.index,
            color='co2',
            color_continuous_scale="Reds",
            hover_name='country',
            hover_data=['co2'],
            title=f'Emissões de CO₂ por País ({ano_mapa})',
            labels={'co2': 'Emissões de CO₂ (Mt)'}
        )
        fig.update_geos(visible=False, showcoastlines=True, showcountries=True, showland=True, landcolor="lightgray")
        fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar o mapa: {e}")

with tab_debug:
    st.subheader("🔍 Depuração dos dados dos EUA")
    usa_in_df = any(df['country'].str.contains('United States', na=False))
    st.write(f"EUA nos dados CSV: {usa_in_df}")
    if usa_in_df:
        st.write(df[df['country'].str.contains('United States', na=False)][['country', 'year', 'co2']].head())

    usa_in_geojson = any(world['country'].str.contains('United States', na=False))
    st.write(f"EUA no GeoJSON: {usa_in_geojson}")
    if not usa_in_geojson:
        possible_usa = world[world['country'].str.contains('States|America|USA|United', na=False)]['country'].unique()
        st.write("Possíveis nomes alternativos encontrados:")
        st.write(possible_usa)
