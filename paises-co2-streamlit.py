import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
import geopandas as gpd

# Configurações da página
st.set_page_config(layout="wide", page_title="Comparador Global de Emissões de CO₂")

# Título do app
st.title("Comparador Global de Emissões de CO₂📊")
st.subheader('Dados de Our world in Data -')
st.link_button("link deles (em inglês)", "https://ourworldindata.org/co2-and-greenhouse-gas-emissions?utm_source=pocket_shared")

# Verificar se todas as bibliotecas necessárias estão instaladas
import importlib

required_packages = ["pandas", "matplotlib", "plotly", "geopandas", "numpy"]
missing_packages = []

for package in required_packages:
    # Verificar e mostrar status dos dados dos EUA
    tab_normal, tab_debug = st.tabs(["Visualização", "Depuração"])
    
    with tab_debug:
        st.subheader("Depuração dos dados dos EUA")
        
        # Verificar se os EUA estão nos dados originais
        usa_in_df = any(df['country'].str.contains('United States', na=False))
        st.write(f"EUA encontrado nos dados originais: {usa_in_df}")
        
        if usa_in_df:
            # Mostrar amostras dos dados dos EUA
            st.write("Amostra dos dados dos EUA:")
            st.write(df[df['country'].str.contains('United States', na=False)][['country', 'year', 'co2']].head())
            
        # Verificar se os EUA estão no GeoJSON
        usa_in_geojson = any(world['country'].str.contains('United States', na=False))
        st.write(f"EUA encontrado no GeoJSON: {usa_in_geojson}")
        
        if not usa_in_geojson:
            st.write("Países no GeoJSON que podem corresponder aos EUA:")
            possible_usa = world[world['country'].str.contains('States|America|USA|United', na=False)]['country'].unique()
            st.write(possible_usa)
        
        # Verificar se os EUA estão nos dados do mapa
        if 'country' in map_data.columns:
            usa_in_map = any(map_data['country'].str.contains('United States|America', na=False))
            st.write(f"EUA encontrado nos dados do mapa: {usa_in_map}")
            
            if not usa_in_map:
                st.write("O nome dos EUA no GeoJSON pode estar diferente do esperado. Alternativas possíveis:")
                st.code("""
                # Adicione ao dicionário de mapeamento:
                'United States': 'United States of America',  # ou outro nome que esteja no GeoJSON
                """)
    
    with tab_normal:try:
        importlib.import_module(package)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    st.warning(f"Atenção: As seguintes bibliotecas estão faltando: {', '.join(missing_packages)}")
    st.markdown("""
    Para instalar as bibliotecas necessárias, execute:
    ```
    pip install pandas matplotlib plotly geopandas numpy
    ```
    """)

@st.cache_data
def carregar_dados():
    caminho_arquivo = 'owid-co2-data.csv'
    return pd.read_csv(caminho_arquivo)

@st.cache_data
def carregar_geojson():
    # URL do dataset naturalearth_lowres no GitHub (acessível publicamente)
    url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
    try:
        return gpd.read_file(url)
    except Exception as e:
        st.error(f"Erro ao carregar dados geográficos: {e}")
        # Fornecer DataFrame vazio como fallback
        return gpd.GeoDataFrame(columns=['geometry', 'name'])

# Carregando os dados
df = carregar_dados()
# Carregando os dados
df = carregar_dados()
try:
    world = carregar_geojson()
    
    # Renomeando para compatibilizar com os dados de CO2
    if 'NAME' in world.columns:
        world = world.rename(columns={'NAME': 'country'})
    elif 'ADMIN' in world.columns:
        world = world.rename(columns={'ADMIN': 'country'})
    elif 'name' in world.columns:
        world = world.rename(columns={'name': 'country'})
    
    # Mapeamento para nomes de países com diferentes grafias
    country_mapping = {
        'United States': 'United States of America',
        'USA': 'United States of America',
        'US': 'United States of America',
        'United States of America': 'United States of America',
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
    
    # Verificar se 'United States' está nos dados
    if 'United States' in df['country'].unique():
        st.info("Encontrado 'United States' nos dados. Aplicando mapeamento para compatibilizar.")
    
    # Aplicar mapeamento nos dados de CO2
    df['country_mapped'] = df['country'].map(lambda x: country_mapping.get(x, x))
    
    # Debug: mostrar países disponíveis no mapa e nos dados
    with st.expander("Depuração de dados de países"):
        st.write("Primeiros países no GeoJSON:")
        st.write(world['country'].head(10).tolist())
        
        st.write("Primeiros países nos dados CSV:")
        st.write(df['country'].head(10).tolist())
        
        st.write("EUA nos dados (verificação):")
        us_entries = df[df['country'].str.contains('United States', na=False)]
        st.write(f"Entradas com 'United States': {len(us_entries)}")
        if not us_entries.empty:
            st.write(us_entries[['country', 'year', 'co2']].head())
    
    # Agora usamos country_mapped para a junção
except Exception as e:
    st.error(f"Erro ao processar dados geográficos: {e}")
    # Criar um dataframe vazio como fallback
    world = gpd.GeoDataFrame(columns=['geometry', 'country'])

# Lista de anos disponíveis
anos_disponiveis = sorted(df['year'].dropna().unique())
anos_validos = [ano for ano in anos_disponiveis if ano >= 1990]

# Interface principal
tab1, tab2 = st.tabs(["Comparação por País", "Mapas Interativos"])

with tab1:
    # Seleção de dois anos para comparação
    col1, col2 = st.columns(2)
    with col1:
        ano1 = st.selectbox("Escolha o 1º ano:", anos_validos, index=len(anos_validos)-5, key="ano1_tab1")
    with col2:
        ano2 = st.selectbox("Escolha o 2º ano para comparar:", anos_validos, index=len(anos_validos)-1, key="ano2_tab1")

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

with tab2:
    st.header("Mapas Interativos de Emissões de CO₂")
    
    # Seleção do ano para o mapa
    ano_mapa = st.selectbox("Escolha o ano para visualizar:", anos_validos, index=len(anos_validos)-1, key="ano_mapa")
    
    # Filtrar dados para o ano selecionado
    df_ano_mapa = df[df['year'] == ano_mapa]
    
    # Criar uma cópia do GeoDataFrame
    map_data = world.copy()
    
    # Mesclar os dados de CO2 com o GeoDataFrame
    if 'country_mapped' in df_ano_mapa.columns:
        map_data = map_data.merge(df_ano_mapa[['country_mapped', 'co2']], 
                                 left_on='country',
                                 right_on='country_mapped',
                                 how='left')
    else:
        map_data = map_data.merge(df_ano_mapa[['country', 'co2']], 
                                 on='country', 
                                 how='left')
    
    # Criar categorias para visualização
    map_data['co2_categoria'] = pd.cut(
        map_data['co2'], 
        bins=[0, 50, 200, 1000, 5000, float('inf')],
        labels=['Muito Baixo', 'Baixo', 'Médio', 'Alto', 'Muito Alto']
    )
    
    # Converter para CRS compatível com plotly
    map_data = map_data.to_crs("EPSG:4326")
    
    # Plotando o mapa com plotly
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
            labels={'co2': 'Emissões de CO₂ (milhões de toneladas)'}
        )
        
        fig.update_geos(
            visible=False,
            showcoastlines=True,
            showcountries=True,
            showland=True,
            landcolor="lightgray"
        )
        
        fig.update_layout(
            margin={"r":0,"t":50,"l":0,"b":0},
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar mapa global: {e}")
        st.info("Este erro pode ser resolvido seguindo as sugestões abaixo.")
        st.markdown("""
        Se os mapas não estiverem funcionando, tente uma abordagem alternativa:
        1. Instale os pacotes necessários: `pip install streamlit pandas matplotlib plotly geopandas`
        2. Baixe manualmente o arquivo GeoJSON dos países
        """)

    
    # Adicionar um segundo mapa para comparação (opcional)
    st.subheader("Comparar Variação de Emissões entre Anos")
    
    col1, col2 = st.columns(2)
    with col1:
        ano_comp1 = st.selectbox("Ano Inicial:", anos_validos, index=len(anos_validos)-5, key="ano_comp1")
    with col2:
        ano_comp2 = st.selectbox("Ano Final:", anos_validos, index=len(anos_validos)-1, key="ano_comp2")
    
    # Filtrar dados para os anos selecionados
    df_comp1 = df[df['year'] == ano_comp1]
    df_comp2 = df[df['year'] == ano_comp2]
    
    # Criar DataFrame de variação
    if 'country_mapped' in df_comp1.columns and 'country_mapped' in df_comp2.columns:
        df_variacao = pd.merge(
            df_comp1[['country', 'country_mapped', 'co2']], 
            df_comp2[['country', 'country_mapped', 'co2']], 
            on='country', 
            suffixes=('_inicial', '_final')
        )
    else:
        df_variacao = pd.merge(
            df_comp1[['country', 'co2']], 
            df_comp2[['country', 'co2']], 
            on='country', 
            suffixes=('_inicial', '_final')
        )
    
    # Calcular variação percentual
    df_variacao['variacao_abs'] = df_variacao['co2_final'] - df_variacao['co2_inicial']
    df_variacao['variacao_perc'] = (df_variacao['variacao_abs'] / df_variacao['co2_inicial']) * 100
    
    # Mesclar com o GeoDataFrame
    map_variacao = world.copy()
    
    # Mesclar adequadamente baseado nas colunas disponíveis
    if 'country_mapped' in df_variacao.columns:
        map_variacao = map_variacao.merge(
            df_variacao[['country_mapped', 'variacao_abs', 'variacao_perc']], 
            left_on='country',
            right_on='country_mapped',
            how='left'
        )
    else:
        map_variacao = map_variacao.merge(
            df_variacao[['country', 'variacao_abs', 'variacao_perc']], 
            on='country', 
            how='left'
        )
    
    # Converter para CRS compatível com plotly
    map_variacao = map_variacao.to_crs("EPSG:4326")
    
    # Escolher entre variação absoluta ou percentual
    tipo_variacao = st.radio("Tipo de Variação:", ["Absoluta (em Mt)", "Percentual (%)"], horizontal=True)
    
    # Definir valor e título com base na escolha
    if tipo_variacao == "Absoluta (em Mt)":
        var_col = 'variacao_abs'
        titulo = f'Variação Absoluta nas Emissões de CO₂ entre {ano_comp1} e {ano_comp2} (em Mt)'
        hover_label = 'Variação (Mt)'
    else:
        var_col = 'variacao_perc'
        titulo = f'Variação Percentual nas Emissões de CO₂ entre {ano_comp1} e {ano_comp2} (%)'
        hover_label = 'Variação (%)'
    
    # Criar escala de cores divergente (vermelho para aumento, verde para redução)
    max_abs = max(abs(map_variacao[var_col].min()), abs(map_variacao[var_col].max()))
    
    # Plotando o mapa com plotly
    try:
        fig_var = px.choropleth(
            map_variacao,
            geojson=map_variacao.geometry,
            locations=map_variacao.index,
            color=var_col,
            color_continuous_scale="RdYlGn_r",
            range_color=[-max_abs, max_abs],
            hover_name='country',
            hover_data={var_col: ':.2f'},
            title=titulo,
            labels={var_col: hover_label}
        )
        
        fig_var.update_geos(
            visible=False,
            showcoastlines=True,
            showcountries=True,
            showland=True,
            landcolor="lightgray"
        )
        
        fig_var.update_layout(
            margin={"r":0,"t":50,"l":0,"b":0},
            height=600
        )
        
        st.plotly_chart(fig_var, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar mapa de variação: {e}")

    
    # Adicionar mapa em estilo choropleth para a América do Sul (semelhante ao exemplo do desmatamento)
    st.subheader("Foco Regional: Emissões na América do Sul")
    
    # Filtrar apenas países da América do Sul
    south_america = ['Brazil', 'Argentina', 'Colombia', 'Chile', 'Peru', 'Venezuela', 'Ecuador', 
                     'Bolivia', 'Paraguay', 'Uruguay', 'Guyana', 'Suriname', 'French Guiana']
    
    map_sa = map_data[map_data['country'].isin(south_america)].copy()
    
    # Criar um mapa de calor estilo choropleth
    try:
        fig_sa = px.choropleth(
            map_sa,
            geojson=map_sa.geometry,
            locations=map_sa.index,
            color='co2',
            color_continuous_scale="Reds",
            hover_name='country',
            hover_data=['co2'],
            title=f'Emissões de CO₂ na América do Sul ({ano_mapa})',
            labels={'co2': 'Emissões de CO₂ (Mt)'}
        )
        
        # Ajustar limites do mapa para América do Sul
        fig_sa.update_geos(
            visible=False,
            showcoastlines=True, 
            showcountries=True,
            showland=True,
            landcolor="lightgray",
            fitbounds="locations",
            center={"lat": -15, "lon": -60},
        )
        
        fig_sa.update_layout(
            margin={"r":0,"t":50,"l":0,"b":0},
            height=600
        )
        
        st.plotly_chart(fig_sa, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar mapa da América do Sul: {e}")
        st.info("Este erro pode ser resolvido com as opções de suporte acima.")
    
    # Adicionar legenda e explicação
    st.markdown("""
    ### Legenda do Mapa
    - **Vermelho escuro**: Maiores emissões
    - **Vermelho claro**: Emissões moderadas
    - **Cinza**: Dados não disponíveis
    
    ### Fonte dos dados:
    - Dados de emissões: Our World in Data
    - Fronteiras: Natural Earth
    """)

    # Opção para baixar GeoJSON caso não consiga carregar
    st.markdown("---")
    st.warning("Se o mapa não estiver carregando corretamente, há algumas opções para resolver:")
    
    with st.expander("Opções para resolver problemas com os mapas"):
        st.markdown("""
        1. **Instale as dependências corretas**:
           ```bash
           pip install streamlit pandas matplotlib plotly geopandas numpy
           ```
           
        2. **Opção alternativa**: Você pode baixar manualmente o arquivo GeoJSON e colocá-lo na mesma pasta que seu script:
           - [Download do arquivo GeoJSON dos países](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson)
           
        3. **Atualização do código**: Se preferir usar um arquivo local, modifique a função `carregar_geojson()` para:
           ```python
           @st.cache_data
           def carregar_geojson():
               # Substitua pelo caminho do arquivo que você baixou
               caminho_arquivo = 'ne_110m_admin_0_countries.geojson'
               return gpd.read_file(caminho_arquivo)
           ```
        """)

