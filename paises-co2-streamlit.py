import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import numpy as np
from matplotlib.cm import get_cmap
import country_converter as coco
import geopandas as gpd
from folium.features import GeoJsonTooltip

# Configuração da página
st.set_page_config(
    page_title="Comparador Global de Emissões de CO₂",
    page_icon="🌍",
    layout="wide"
)

# Título e descrição do app
st.title("🌍 Comparador Global de Emissões de CO₂")
st.markdown("""
Este aplicativo permite comparar as emissões de CO₂ entre diferentes países e anos.
Os dados são fornecidos pela Our World in Data.
""")
st.link_button("Fonte dos dados (em inglês)", "https://ourworldindata.org/co2-and-greenhouse-gas-emissions?utm_source=pocket_shared")

# Função para carregar e processar os dados
@st.cache_data
def carregar_dados():
    """Carrega e prepara os dados para análise"""
    try:
        caminho_arquivo = 'owid-co2-data.csv'
        df = pd.read_csv(caminho_arquivo)
        
        # Garantir que estamos trabalhando apenas com países (não regiões)
        # e remover registros com dados ausentes de CO2
        df_paises = df[~df['country'].isin(['World', 'International transport'])]
        df_paises = df_paises.dropna(subset=['co2'])
        
        # Adicionar códigos ISO para uso no mapa
        cc = coco.CountryConverter()
        df_paises['iso_code'] = df_paises['country'].apply(
            lambda x: cc.convert(names=[x], to='ISO3', not_found=None)
        )
        
        return df_paises
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Carregando os dados
with st.spinner("Carregando dados..."):
    df = carregar_dados()

# Verificando se os dados foram carregados corretamente
if df.empty:
    st.error("Não foi possível carregar os dados. Verifique o arquivo 'owid-co2-data.csv'.")
    st.stop()

# Carregar dados geográficos dos países
@st.cache_data
def carregar_geodata():
    """Carrega os dados geográficos dos países diretamente de um URL"""
    try:
        # URL para o shapefile do Natural Earth (110m)
        url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
        world = gpd.read_file(url)
        
        # Adicionar classificação de continentes manualmente
        # Usamos o country_converter para obter os continentes
        cc = coco.CountryConverter()
        world['continente'] = world['ISO_A3'].apply(
            lambda x: cc.convert(names=[x], to='continent', not_found=None) if x != '-99' else None
        )
        
        # Converter códigos para ISO3 para compatibilidade
        world['iso_a3'] = world['ISO_A3'].apply(
            lambda x: cc.convert(names=[x], to='ISO3', not_found=None) if x != '-99' else None
        )
        return world
    except Exception as e:
        st.error(f"Erro ao carregar dados geográficos: {e}")
        return gpd.GeoDataFrame()

# Carregando geodata
world_gdf = carregar_geodata()

# Barra lateral para controles
st.sidebar.header("📊 Configurações")

# Anos disponíveis para seleção
anos_disponiveis = sorted(df['year'].dropna().unique())
anos_validos = [ano for ano in anos_disponiveis if ano >= 1990]

# Seleção de dois anos para comparação
ano1 = st.sidebar.selectbox(
    "Ano base:",
    anos_validos,
    index=len(anos_validos)-10  # Default para 10 anos atrás
)

ano2 = st.sidebar.selectbox(
    "Ano para comparação:",
    anos_validos,
    index=len(anos_validos)-1   # Default para o ano mais recente
)

# Filtrar dados para os anos selecionados
df_ano1 = df[df['year'] == ano1]
df_ano2 = df[df['year'] == ano2]

# Encontrar países com dados disponíveis em ambos os anos
paises_comuns = sorted(set(df_ano1['country']).intersection(set(df_ano2['country'])))

# Opção para filtrar por continente
continentes = ['Todos']
if not world_gdf.empty and 'continente' in world_gdf.columns:
    continentes += sorted(world_gdf['continente'].dropna().unique().tolist())
continente_selecionado = st.sidebar.selectbox("Filtrar por continente:", continentes)

# Filtrar países por continente
if continente_selecionado != 'Todos' and not world_gdf.empty:
    paises_no_continente = world_gdf[world_gdf['continente'] == continente_selecionado]['NAME'].tolist()
    paises_comuns = [p for p in paises_comuns if p in paises_no_continente]

# Calcular médias globais para os anos selecionados
media1 = df_ano1['co2'].mean()
media2 = df_ano2['co2'].mean()

# Informações sobre médias globais
st.sidebar.markdown("### 🌐 Médias Globais de Emissão")
st.sidebar.info(f"**{ano1}**: {round(media1, 2)} Mt CO₂")
st.sidebar.info(f"**{ano2}**: {round(media2, 2)} Mt CO₂")

# Mudança percentual na média global
mudanca_percentual = ((media2 - media1) / media1) * 100
if mudanca_percentual > 0:
    st.sidebar.warning(f"↗️ Aumento de {round(mudanca_percentual, 1)}% na média global")
else:
    st.sidebar.success(f"↘️ Redução de {round(abs(mudanca_percentual), 1)}% na média global")

# Seleção de países para comparação detalhada
paises_selecionados = st.multiselect(
    "Escolha países para comparação detalhada:",
    paises_comuns,
    default=paises_comuns[:3] if len(paises_comuns) > 3 else paises_comuns
)

# Criação das abas para diferentes visualizações
tab1, tab2, tab3 = st.tabs(["🗺️ Mapa de Emissões", "📊 Comparação entre Anos", "📈 Análise Detalhada"])

with tab1:
    st.header(f"Mapa Global de Emissões de CO₂ - {ano2}")
    
    # Preparar dados para o mapa
    mapa_df = df_ano2[['country', 'iso_code', 'co2']].copy()
    mapa_df = mapa_df[~mapa_df['iso_code'].isna()]  # Remover países sem código ISO
    
    # Mesclar com dados geográficos
    if not world_gdf.empty:
        mapa_geo = world_gdf.merge(mapa_df, left_on='iso_a3', right_on='iso_code', how='left')
        
        # Normalizar os dados para coloração
        vmin, vmax = mapa_geo['co2'].min(), mapa_geo['co2'].max()
        
        # Criar o mapa base com folium
        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")
        
        # Criar escala de cores
        colormap = get_cmap('YlOrRd')
        
        # Função para determinar a cor com base na emissão
        def get_color(emissao):
            if pd.isna(emissao):
                return '#CCCCCC'  # Cinza para dados ausentes
            norm_emissao = (emissao - vmin) / (vmax - vmin) if vmax > vmin else 0
            rgba = colormap(norm_emissao)
            return f'#{int(rgba[0]*255):02x}{int(rgba[1]*255):02x}{int(rgba[2]*255):02x}'
        
        # Adicionar camada GeoJson com coloração por emissão
        folium.GeoJson(
            mapa_geo.to_json(),
            style_function=lambda feature: {
                'fillColor': get_color(feature['properties']['co2']),
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': 0.7
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['NAME', 'co2'],
                aliases=['País:', 'Emissão (Mt CO₂):'],
                localize=True,
                sticky=False,
                labels=True
            )
        ).add_to(m)
        
        # Adicionar legenda ao mapa
        legend_html = '''
        <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; 
                    padding: 10px; border: 1px solid grey; border-radius: 5px;">
        <p style="text-align: center; margin-bottom: 5px;"><b>Emissões de CO₂ (Mt)</b></p>
        <div style="display: flex; flex-direction: column; gap: 5px;">
        '''
        
        # Criar faixas para a legenda
        ranges = np.linspace(vmin, vmax, 5)
        for i in range(len(ranges)-1):
            color = get_color((ranges[i] + ranges[i+1]) / 2)
            legend_html += f'''
            <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: {color};"></div>
            <span style="margin-left: 5px;">{int(ranges[i])} - {int(ranges[i+1])}</span>
            </div>
            '''
        
        legend_html += '''
        </div>
        </div>
        '''
        
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Exibir o mapa no Streamlit
        st_folium(m, width=1200, height=600)
    else:
        # Fallback se não conseguir carregar dados geográficos
        st.error("Não foi possível carregar o mapa. Verificando dados disponíveis...")
        
        # Criar visualização alternativa - mapa de calor simples
        if not mapa_df.empty:
            st.subheader("Maiores emissores de CO₂")
            top_emissores = mapa_df.sort_values('co2', ascending=False).head(20)
            
            fig, ax = plt.subplots(figsize=(10, 8))
            bars = ax.barh(top_emissores['country'], top_emissores['co2'], color='firebrick')
            ax.set_xlabel('Emissões de CO₂ (Mt)')
            ax.set_title(f'Maiores emissores de CO₂ - {ano2}')
            
            # Adicionar valores nas barras
            for i, v in enumerate(top_emissores['co2']):
                ax.text(v + 0.5, i, f"{int(v)}", va='center')
                
            plt.tight_layout()
            st.pyplot(fig)

with tab2:
    if not paises_selecionados:
        st.info("Selecione pelo menos um país acima para visualizar comparações.")
    else:
        st.header(f"Comparação das Emissões de CO₂ entre {ano1} e {ano2}")
        
        # Filtrar dados para os países selecionados
        df1 = df_ano1[df_ano1['country'].isin(paises_selecionados)]
        df2 = df_ano2[df_ano2['country'].isin(paises_selecionados)]
        
        # Criar gráfico de barras comparativas
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Ordenar países por emissão no ano mais recente
        ordem_paises = df2.sort_values('co2', ascending=False)['country'].tolist()
        df1 = df1.set_index('country').reindex(ordem_paises).reset_index()
        df2 = df2.set_index('country').reindex(ordem_paises).reset_index()
        
        x = np.arange(len(paises_selecionados))
        width = 0.35
        
        # Barras para cada ano
        bars1 = ax.bar(x - width/2, df1['co2'], width, label=f'{ano1}', color='steelblue')
        bars2 = ax.bar(x + width/2, df2['co2'], width, label=f'{ano2}', color='firebrick')
        
        # Linhas de média global
        ax.axhline(media1, color='blue', linestyle='--', 
                   label=f'Média Global {ano1} ({round(media1, 1)} Mt)')
        ax.axhline(media2, color='red', linestyle='--', 
                   label=f'Média Global {ano2} ({round(media2, 1)} Mt)')
        
        # Rótulos e legendas
        ax.set_ylabel('Emissões de CO₂ (milhões de toneladas)', fontsize=12)
        ax.set_title(f'Comparação de Emissões de CO₂: {ano1} vs {ano2}', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(df1['country'], rotation=45, ha='right', fontsize=10)
        ax.legend()
        
        # Adicionar valores acima das barras
        def autolabel(bars):
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{int(height)}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 pontos de deslocamento vertical
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8)
        
        autolabel(bars1)
        autolabel(bars2)
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # Adicionar informações sobre variação percentual
        st.subheader("Variação Percentual das Emissões")
        
        # Calcular e mostrar variações percentuais
        col1, col2 = st.columns(2)
        
        with col1:
            # Maiores aumentos
            df_variacao = pd.DataFrame({
                'country': df1['country'],
                'co2_ano1': df1['co2'],
                'co2_ano2': df2['co2']
            })
            
            df_variacao['variacao_abs'] = df_variacao['co2_ano2'] - df_variacao['co2_ano1']
            df_variacao['variacao_pct'] = (df_variacao['variacao_abs'] / df_variacao['co2_ano1']) * 100
            
            # Ordenar por variação percentual (maiores aumentos)
            df_aumentos = df_variacao.sort_values('variacao_pct', ascending=False)
            
            st.markdown("#### 📈 Maiores aumentos")
            for _, row in df_aumentos[df_aumentos['variacao_pct'] > 0].head(3).iterrows():
                st.warning(f"**{row['country']}**: +{round(row['variacao_pct'], 1)}% ({round(row['variacao_abs'], 1)} Mt)")
        
        with col2:
            # Maiores reduções
            df_reducoes = df_variacao.sort_values('variacao_pct', ascending=True)
            
            st.markdown("#### 📉 Maiores reduções")
            for _, row in df_reducoes[df_reducoes['variacao_pct'] < 0].head(3).iterrows():
                st.success(f"**{row['country']}**: {round(row['variacao_pct'], 1)}% ({round(row['variacao_abs'], 1)} Mt)")

with tab3:
    if not paises_selecionados:
        st.info("Selecione pelo menos um país acima para visualizar análises detalhadas.")
    else:
        st.header("Análise Detalhada por País")
        
        # Criar cartões para cada país selecionado
        for pais in paises_selecionados:
            # Obter dados do país
            dados_pais1 = df_ano1[df_ano1['country'] == pais]
            dados_pais2 = df_ano2[df_ano2['country'] == pais]
            
            if dados_pais1.empty or dados_pais2.empty:
                continue
                
            v1 = dados_pais1['co2'].values[0]
            v2 = dados_pais2['co2'].values[0]
            
            # Calcular variação
            dif = v2 - v1
            var_pct = (dif / v1) * 100 if v1 != 0 else 0
            
            # Criar cartão para o país
            st.markdown(f"""
            <div style="padding: 1rem; border-radius: 0.5rem; border: 1px solid #eeeeee; margin-bottom: 1rem;">
                <h3>{pais}</h3>
                <table style="width: 100%;">
                    <tr>
                        <td style="width: 50%;"><b>{ano1}:</b> {round(v1, 1)} Mt</td>
                        <td><b>{ano2}:</b> {round(v2, 1)} Mt</td>
                    </tr>
                    <tr>
                        <td><i>({round(v1/media1, 2)}x a média global)</i></td>
                        <td><i>({round(v2/media2, 2)}x a média global)</i></td>
                    </tr>
                </table>
                <hr>
                <p>
            """, unsafe_allow_html=True)
            
            # Mostrar variação com cores apropriadas
            if dif > 0:
                st.warning(f"**Aumento de {round(dif, 1)} Mt ({round(var_pct, 1)}%) entre {ano1} e {ano2}**")
            elif dif < 0:
                st.success(f"**Redução de {round(abs(dif), 1)} Mt ({round(var_pct, 1)}%) entre {ano1} e {ano2}**")
            else:
                st.info(f"**Sem variação entre {ano1} e {ano2}**")
            
            # Adicionar dados extras se disponíveis
            colunas_extras = [
                ('co2_per_capita', 'CO₂ per Capita (toneladas)'),
                ('gdp', 'PIB (US$)'),
                ('population', 'População')
            ]
            
            extras = []
            for col, label in colunas_extras:
                if col in dados_pais1.columns and col in dados_pais2.columns:
                    if not pd.isna(dados_pais1[col].values[0]) and not pd.isna(dados_pais2[col].values[0]):
                        extras.append((col, label))
            
            if extras:
                col1, col2 = st.columns(2)
                for i, (col, label) in enumerate(extras):
                    val1 = dados_pais1[col].values[0]
                    val2 = dados_pais2[col].values[0]
                    var = ((val2 - val1) / val1) * 100 if val1 != 0 else 0
                    
                    with col1 if i % 2 == 0 else col2:
                        st.metric(
                            label=label, 
                            value=f"{round(val2, 2):,}".replace(',', '.'),
                            delta=f"{round(var, 1)}%"
                        )

# Adicionar rodapé
st.markdown("---")
st.markdown("""
<div style="text-align: center;">
    <p><small>Desenvolvido com Streamlit | Dados de Our World in Data</small></p>
</div>
""", unsafe_allow_html=True)

# Requisitos para este app:
# pip install streamlit pandas matplotlib folium streamlit-folium numpy country-converter geopandas
