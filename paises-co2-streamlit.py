import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

# Configuração da página
st.set_page_config(
    page_title="Comparador Global de Emissões de CO₂",
    page_icon="🌍",
    layout="wide"
)

# CSS personalizado para melhorar a aparência
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1e88e5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subheader {
        font-size: 1.5rem;
        color: #424242;
        margin-bottom: 1rem;
    }
    .chart-container {
        background-color: #f5f5f5;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background-color: #f9f9f9;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        margin-bottom: 1rem;
    }
    .footnote {
        font-size: 0.8rem;
        color: #757575;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# Título e descrição do app
st.markdown("<h1 class='main-header'>🌍 Comparador Global de Emissões de CO₂</h1>", unsafe_allow_html=True)

col_intro1, col_intro2 = st.columns([3, 1])
with col_intro1:
    st.markdown("""
    Esta aplicação permite visualizar e comparar as emissões de CO₂ entre diferentes países e anos.
    Explore os dados através de mapas interativos e gráficos comparativos.
    """)
with col_intro2:
    st.markdown("<p class='footnote'>Dados de:</p>", unsafe_allow_html=True)
    st.link_button("Our World in Data", "https://ourworldindata.org/co2-and-greenhouse-gas-emissions")

# Função para carregar dados com cache
@st.cache_data
def carregar_dados():
    try:
        caminho_arquivo = 'owid-co2-data.csv'
        df = pd.read_csv(caminho_arquivo)
        # Garantir que colunas importantes estejam presentes
        required_columns = ['country', 'year', 'co2', 'iso_code']
        for col in required_columns:
            if col not in df.columns:
                if col == 'iso_code':
                    # Criar mapeamento de países para códigos ISO se não existir
                    df['iso_code'] = df['country'].map(get_country_codes())
                else:
                    st.error(f"Coluna {col} não encontrada no arquivo de dados.")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        # Retornar DataFrame vazio com estrutura base se houver erro
        return pd.DataFrame(columns=['country', 'year', 'co2', 'iso_code'])

# Função para obter códigos ISO de países (usado se não estiverem no dataset)
def get_country_codes():
    # Dicionário básico de mapeamento país -> código ISO
    # Na implementação completa, isso poderia ser um arquivo CSV separado
    return {
        'World': 'OWID_WRL', 'United States': 'USA', 'China': 'CHN', 
        'India': 'IND', 'Russia': 'RUS', 'Brazil': 'BRA', 
        'Germany': 'DEU', 'United Kingdom': 'GBR', 'France': 'FRA',
        'Japan': 'JPN', 'Canada': 'CAN', 'Australia': 'AUS',
        # Adicionar mais mapeamentos conforme necessário
    }

# Carregar os dados
with st.spinner('Carregando dados...'):
    df = carregar_dados()

# Verificar se os dados foram carregados corretamente
if df.empty:
    st.error("Não foi possível carregar os dados. Verifique se o arquivo 'owid-co2-data.csv' está disponível.")
    st.stop()

# Limpeza e preparação dos dados
def limpar_dados(df):
    # Remover linhas com valores ausentes nas colunas essenciais
    df_clean = df.dropna(subset=['country', 'year', 'co2'])
    
    # Converter ano para inteiro
    df_clean['year'] = df_clean['year'].astype(int)
    
    # Garantir que a coluna CO2 seja numérica
    df_clean['co2'] = pd.to_numeric(df_clean['co2'], errors='coerce')
    
    # Filtrar para incluir apenas países (remover agregações)
    excludes = ['World', 'International Transport', 'EU-27', 'EU-28']
    df_countries = df_clean[~df_clean['country'].isin(excludes)]
    
    return df_clean, df_countries

df_clean, df_countries = limpar_dados(df)

# Lista de anos disponíveis
anos_disponiveis = sorted(df_clean['year'].unique())
anos_validos = [ano for ano in anos_disponiveis if ano >= 1990]

# Interface do usuário com tabs para organizar o conteúdo
tab1, tab2, tab3 = st.tabs(["📊 Comparação Entre Anos", "🗺️ Mapa Global", "📈 Tendências Históricas"])

with tab1:
    st.markdown("<h2 class='subheader'>Comparação de Emissões entre Anos</h2>", unsafe_allow_html=True)
    
    # Seleção de dois anos para comparação
    col1, col2 = st.columns(2)
    with col1:
        ano1 = st.selectbox("Escolha o 1º ano:", anos_validos, index=len(anos_validos)-5)
    with col2:
        ano2 = st.selectbox("Escolha o 2º ano para comparar:", anos_validos, index=len(anos_validos)-1)
    
    # Filtrar países com dados em ambos os anos
    df_ano1 = df_clean[df_clean['year'] == ano1]
    df_ano2 = df_clean[df_clean['year'] == ano2]
    paises_comuns = sorted(set(df_ano1['country']).intersection(set(df_ano2['country'])))
    
    # Adicionar opção de filtro por continente/região
    if 'continent' in df_clean.columns:
        continentes = ['Todos'] + sorted(df_clean['continent'].dropna().unique().tolist())
        continente_selecionado = st.selectbox("Filtrar por continente:", continentes)
        
        if continente_selecionado != 'Todos':
            paises_filtrados = df_clean[df_clean['continent'] == continente_selecionado]['country'].unique()
            paises_comuns = [p for p in paises_comuns if p in paises_filtrados]
    
    # Adicionar campo de busca para facilitar seleção de países
    pais_busca = st.text_input("Buscar país:", "")
    if pais_busca:
        paises_filtrados = [p for p in paises_comuns if pais_busca.lower() in p.lower()]
        if not paises_filtrados:
            st.info("Nenhum país encontrado com esse termo.")
            paises_selecionados = st.multiselect("Escolha países para comparar:", paises_comuns)
        else:
            paises_selecionados = st.multiselect("Escolha países para comparar:", paises_comuns, default=paises_filtrados[:5])
    else:
        paises_sugeridos = ['Brazil', 'United States', 'China', 'India', 'Germany']
        paises_default = [p for p in paises_sugeridos if p in paises_comuns]
        paises_selecionados = st.multiselect("Escolha países para comparar:", paises_comuns, default=paises_default[:3])
    
    if not paises_selecionados:
        st.info("Selecione pelo menos um país para comparar.")
    else:
        # Calcular médias globais para os anos selecionados
        dados_mundo1 = df_ano1[df_ano1['country'] == 'World']
        dados_mundo2 = df_ano2[df_ano2['country'] == 'World']
        
        if not dados_mundo1.empty and not dados_mundo2.empty:
            media1 = dados_mundo1['co2'].values[0]
            media2 = dados_mundo2['co2'].values[0]
        else:
            media1 = df_ano1['co2'].mean()
            media2 = df_ano2['co2'].mean()
        
        # Criar dataframes para os países selecionados
        df1 = df_ano1[df_ano1['country'].isin(paises_selecionados)]
        df2 = df_ano2[df_ano2['country'].isin(paises_selecionados)]
        
        # Gráfico de comparação usando Plotly (mais interativo)
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        fig = go.Figure()
        
        # Adicionar barras para cada ano
        fig.add_trace(go.Bar(
            x=df1['country'],
            y=df1['co2'],
            name=f'Emissões em {ano1}',
            marker_color='#1e88e5'
        ))
        
        fig.add_trace(go.Bar(
            x=df2['country'],
            y=df2['co2'],
            name=f'Emissões em {ano2}',
            marker_color='#43a047'
        ))
        
        # Adicionar linhas para médias globais
        fig.add_trace(go.Scatter(
            x=df1['country'], 
            y=[media1] * len(df1),
            mode='lines',
            name=f'Média Global {ano1} ({round(media1, 1)} Mt)',
            line=dict(color='blue', dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=df1['country'], 
            y=[media2] * len(df1),
            mode='lines',
            name=f'Média Global {ano2} ({round(media2, 1)} Mt)',
            line=dict(color='green', dash='dash')
        ))
        
        # Configurar layout
        fig.update_layout(
            title=f'Comparação de Emissões de CO₂ entre {ano1} e {ano2}',
            xaxis_title='País',
            yaxis_title='Emissões de CO₂ (milhões de toneladas)',
            barmode='group',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Análise detalhada por país
        st.markdown("<h3 class='subheader'>📌 Análise Detalhada por País</h3>", unsafe_allow_html=True)
        
        # Dividir países em colunas para melhor visualização
        cols = st.columns(min(len(paises_selecionados), 3))
        
        for i, pais in enumerate(paises_selecionados):
            col_index = i % len(cols)
            
            with cols[col_index]:
                st.markdown(f"<div class='metric-card'>", unsafe_allow_html=True)
                
                v1 = df1[df1['country'] == pais]['co2'].values[0]
                v2 = df2[df2['country'] == pais]['co2'].values[0]
                
                # Calcular variação percentual
                if v1 > 0:
                    var_pct = ((v2 - v1) / v1) * 100
                else:
                    var_pct = float('inf') if v2 > 0 else 0
                
                st.markdown(f"#### {pais}")
                
                # Criar métricas mais visuais
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.metric(
                        label=f"Emissões em {ano1}",
                        value=f"{round(v1):,} Mt",
                        delta=f"{round(v1/media1, 1)}x média global"
                    )
                
                with col_m2:
                    st.metric(
                        label=f"Emissões em {ano2}",
                        value=f"{round(v2):,} Mt",
                        delta=f"{round(v2/media2, 1)}x média global"
                    )
                
                # Mostrar variação entre os anos
                dif = v2 - v1
                
                # Minigrafico de variação
                mini_data = [v1, v2]
                mini_fig, mini_ax = plt.subplots(figsize=(3, 1))
                mini_ax.plot(mini_data, marker='o', color='#1e88e5')
                mini_ax.grid(True, linestyle='--', alpha=0.7)
                mini_ax.set_xticks([0, 1])
                mini_ax.set_xticklabels([str(ano1), str(ano2)])
                mini_ax.set_title("Tendência")
                st.pyplot(mini_fig)
                
                if dif > 0:
                    st.markdown(f"**Aumento de {round(dif):,} Mt** ({round(var_pct, 1)}%) entre {ano1} e {ano2}")
                elif dif < 0:
                    st.markdown(f"**Redução de {round(abs(dif)):,} Mt** ({round(abs(var_pct), 1)}%) entre {ano1} e {ano2}")
                else:
                    st.info("Sem variação entre os anos")
                
                st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<h2 class='subheader'>Mapa Global de Emissões de CO₂</h2>", unsafe_allow_html=True)
    
    # Seleção de ano para o mapa
    ano_mapa = st.select_slider(
        "Selecione o ano para visualizar no mapa:",
        options=anos_validos,
        value=anos_validos[-1]
    )
    
    # Filtrar dados para o ano selecionado
    df_mapa = df_clean[df_clean['year'] == ano_mapa].copy()
    
    # Verificar se existem dados de códigos ISO
    if 'iso_code' not in df_mapa.columns or df_mapa['iso_code'].isna().all():
        st.warning("Dados de códigos ISO dos países não estão disponíveis. O mapa pode não exibir todos os países corretamente.")
    
    # Adicionar controles para o tipo de visualização
    col_vis1, col_vis2 = st.columns(2)
    
    with col_vis1:
        metrica_mapa = st.selectbox(
            "Escolha a métrica para visualizar:",
            ["co2", "co2_per_capita"] if "co2_per_capita" in df_mapa.columns else ["co2"]
        )
    
    with col_vis2:
        escala = st.selectbox(
            "Escolha a escala do mapa:",
            ["Linear", "Logarítmica"]
        )
    
    # Preparar dados para o mapa
    if metrica_mapa == "co2":
        titulo_mapa = f"Emissões Totais de CO₂ em {ano_mapa} (milhões de toneladas)"
    else:
        titulo_mapa = f"Emissões de CO₂ per capita em {ano_mapa} (toneladas por pessoa)"
    
    # Criar mapa coroplético interativo com Plotly
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    
    fig_map = px.choropleth(
        df_mapa,
        locations="iso_code" if "iso_code" in df_mapa.columns else None,
        locationmode="ISO-3" if "iso_code" in df_mapa.columns else "country names",
        color=metrica_mapa,
        hover_name="country",
        hover_data={
            metrica_mapa: True,
            "year": False,
            "iso_code": False
        },
        title=titulo_mapa,
        color_continuous_scale="Viridis" if metrica_mapa == "co2" else "YlOrRd",
        log_color=escala == "Logarítmica",
        projection="natural earth"
    )
    
    fig_map.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='equirectangular'
        ),
        height=600,
        margin={"r":0,"t":50,"l":0,"b":0}
    )
    
    st.plotly_chart(fig_map, use_container_width=True)
    
    # Adicionar legenda/explicação
    st.markdown("""
    <div class='footnote'>
    Este mapa mostra as emissões de CO₂ por país. As áreas mais escuras indicam maiores emissões.
    Passe o mouse sobre um país para ver os detalhes específicos.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Top 10 países emissores
    st.markdown("<h3 class='subheader'>Top 10 Países Emissores em {}</h3>".format(ano_mapa), unsafe_allow_html=True)
    
    top10 = df_mapa.sort_values(by=metrica_mapa, ascending=False).head(10)
    
    fig_top10 = px.bar(
        top10,
        x='country',
        y=metrica_mapa,
        title=f"Top 10 Países por {metrica_mapa} em {ano_mapa}",
        color=metrica_mapa,
        labels={'country': 'País', metrica_mapa: 'Emissões de CO₂'},
        color_continuous_scale='Viridis',
        height=400
    )
    
    fig_top10.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_top10, use_container_width=True)

with tab3:
    st.markdown("<h2 class='subheader'>Tendências Históricas de Emissões</h2>", unsafe_allow_html=True)
    
    # Seleção de países para tendências
    paises_tendencia = st.multiselect(
        "Escolha países para analisar tendências:",
        sorted(df_countries['country'].unique()),
        default=['Brazil', 'United States', 'China'][:3] if all(p in df_countries['country'].unique() for p in ['Brazil', 'United States', 'China']) else None
    )
    
    # Intervalo de anos
    ano_min, ano_max = st.select_slider(
        "Intervalo de anos:",
        options=anos_disponiveis,
        value=(anos_disponiveis[0], anos_disponiveis[-1])
    )
    
    if not paises_tendencia:
        st.info("Selecione pelo menos um país para visualizar tendências históricas.")
    else:
        # Filtrar dados para os países e intervalo de anos selecionados
        df_tendencia = df_clean[
            (df_clean['country'].isin(paises_tendencia)) & 
            (df_clean['year'] >= ano_min) & 
            (df_clean['year'] <= ano_max)
        ]
        
        # Gráfico de linha para tendências
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        
        fig_trend = px.line(
            df_tendencia,
            x='year',
            y='co2',
            color='country',
            title=f"Tendência de Emissões de CO₂ ({ano_min}-{ano_max})",
            labels={'year': 'Ano', 'co2': 'Emissões de CO₂ (milhões de toneladas)', 'country': 'País'},
            height=500
        )
        
        fig_trend.update_layout(
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Adicionar opção para visualizar emissões per capita se disponível
        if "co2_per_capita" in df_clean.columns:
            mostrar_per_capita = st.checkbox("Mostrar emissões per capita", value=False)
            
            if mostrar_per_capita:
                fig_per_capita = px.line(
                    df_tendencia,
                    x='year',
                    y='co2_per_capita',
                    color='country',
                    title=f"Tendência de Emissões de CO₂ per Capita ({ano_min}-{ano_max})",
                    labels={'year': 'Ano', 'co2_per_capita': 'Emissões de CO₂ per Capita (toneladas)', 'country': 'País'},
                    height=500
                )
                
                fig_per_capita.update_layout(
                    hovermode="x unified",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig_per_capita, use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Tabela de dados
        with st.expander("Ver dados em tabela"):
            st.dataframe(
                df_tendencia[['country', 'year', 'co2'] + (['co2_per_capita'] if 'co2_per_capita' in df_tendencia.columns else [])],
                use_container_width=True
            )

# Rodapé com informações adicionais
st.markdown("---")
st.markdown("""
<div class='footnote'>
Desenvolvido com Streamlit. Dados de emissões de CO₂ fornecidos por Our World in Data.
Última atualização: Maio 2025.
</div>
""", unsafe_allow_html=True)

# Adicionar informações sobre o dataset em um expander
with st.expander("Sobre os dados"):
    st.markdown("""
    ### Fonte de Dados
    Os dados utilizados nesta aplicação são provenientes do **Our World in Data** e incluem:
    
    - **co2**: Emissões anuais de CO₂ em milhões de toneladas
    - **co2_per_capita**: Emissões anuais de CO₂ per capita em toneladas por pessoa (quando disponível)
    
    ### Interpretação dos Dados
    - As emissões de CO₂ são um indicador importante para avaliar o impacto ambiental de cada país
    - Comparar as emissões totais com as emissões per capita oferece uma visão mais completa sobre a eficiência e o padrão de desenvolvimento de cada nação
    
    ### Limitações
    - Alguns países podem ter dados incompletos ou ausentes para determinados anos
    - As metodologias de coleta e estimativa de dados podem variar entre diferentes regiões
    """)
