import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import wbdata
import re
import datetime
from plotly.subplots import make_subplots
import weo 

st.set_page_config(
    page_title="📊 Analyse de l'Économie Mondiale",
    layout="wide",
    initial_sidebar_state="collapsed",
)

hide_streamlit_style = """
    <style>
    /* Hide Streamlit's default hamburger menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Customize the background and font */
    body {
        background-color: #f5f5f5;
        font-family: 'Arial', sans-serif;
    }
    /* Style headers */
    .css-1aumxhk.e1fqkh3o3 {
        text-align: center;
    }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

grouped_indicators = {
    "Business Environment": {
        "IC.BUS.EASE.DFRN.XQ.DB1719": "Global: Ease of doing business score (DB17-20 methodology)",
        "IC.BUS.EASE.XQ": "Ease of doing business rank (1=most business-friendly regulations)",
        "IC.CNST.PRMT.RK": "Rank: Dealing with construction permits (1=most business-friendly regulations)",
        "IC.CRED.ACC.CRD.RK": "Rank: Getting credit (1=most business-friendly regulations)",
        "IC.ELC.ACES.RK.DB19": "Rank: Getting electricity (1=most business-friendly regulations)",
        "IC.REG.STRT.BUS.RK.DB19": "Rank: Starting a business (1=most business-friendly regulations)",
        "PAY.TAX.RK.DB19": "Rank: Paying taxes (1=most business-friendly regulations)",
        "RESLV.ISV.RK.DB19": "Rank: Resolving insolvency (1=most business-friendly regulations)",
        "TRD.ACRS.BRDR.RK.DB19": "Rank: Trading across borders (1=most business-friendly regulations)",
    },
    "Economic Performance": {
        "NY.GDP.MKTP.CD": "GDP (current US$)",
        "NY.GDP.PCAP.CD": "GDP per capita (current US$)",
        "NY.GDP.DEFL.KD.ZG": "Inflation, GDP deflator (annual %)",
        "NY.GDP.MKTP.KD.ZG": "GDP growth (annual %)",
        "NY.GDP.PCAP.KD.ZG": "GDP per capita growth (annual %)",
        "NY.GNS.ICTR.CD": "Gross savings (current US$)",
    },
    "Trade & Investment": {
        "BG.GSR.NFSV.GD.ZS": "Trade in services (% of GDP)",
        "BM.GSR.GNFS.CD": "Imports of goods and services (BoP, current US$)",
        "BM.KLT.DINV.WD.GD.ZS": "Foreign direct investment, net outflows (% of GDP)",
        "BN.CAB.XOKA.GD.ZS": "Current account balance (% of GDP)",
        "BN.KLT.DINV.CD": "Foreign direct investment, net (BoP, current US$)",
        "BN.KLT.PTXL.CD": "Portfolio Investment, net (BoP, current US$)",
        "BX.GSR.GNFS.CD": "Exports of goods and services (BoP, current US$)",
    },
    "Financial Indicators": {
        "CM.MKT.LCAP.GD.ZS": "Market capitalization of listed domestic companies (% of GDP)",
        "GB.XPD.RSDV.GD.ZS": "Research and development expenditure (% of GDP)",
        "GC.DOD.TOTL.GD.ZS": "Central government debt, total (% of GDP)",
    },
    "Social Indicators": {
        "EN.POP.DNST": "Population density (people per sq. km of land area)",
        "FI.RES.TOTL.CD": "Total reserves (includes gold, current US$)",
        "FP.CPI.TOTL": "Consumer price index (2010 = 100)",
        "FP.CPI.TOTL.ZG": "Inflation, consumer prices (annual %)",
        "FP.WPI.TOTL": "Wholesale price index (2010 = 100)",
        "SE.ADT.LITR.ZS": "Literacy rate, adult total (% of people ages 15 and above)",
        "SE.ADT.1524.LT.ZS": "Literacy rate, youth total (% of people ages 15-24)",
        "SH.DTH.IMRT": "Number of infant deaths",
        "SH.MED.BEDS.ZS": "Hospital beds (per 1,000 people)",
        "SI.POV.GINI": "Gini index",
        "SL.UEM.1524.NE.ZS": "Unemployment, youth total (% of total labor force ages 15-24) (national estimate)",
        "SL.UEM.TOTL.NE.ZS": "Unemployment, total (% of total labor force) (national estimate)",
        "SM.POP.NETM": "Net migration",
        "SP.DYN.LE00.IN": "Life expectancy at birth, total (years)",
        "SP.POP.GROW": "Population growth (annual %)",
        "SP.POP.TOTL": "Population, total",
        "SP.RUR.TOTL": "Rural population",
        "SP.URB.TOTL": "Urban population",
    },
    "Governance Indicators": {
        "GE.EST": "Government Effectiveness: Estimate",
        "PV.EST": "Political Stability and Absence of Violence/Terrorism: Estimate",
    },
}


indicator_descriptions = {
    "IC.BUS.EASE.DFRN.XQ.DB1719": (
        "Cette variable représente le score global de facilité de faire des affaires, calculé selon la méthodologie DB17-20. "
        "Elle évalue divers aspects réglementaires affectant les entreprises, tels que la création d'entreprise, la protection des investisseurs, "
        "l'obtention de permis de construction, l'accès au crédit, etc."
    ),
    "IC.BUS.EASE.XQ": (
        "Le rang de facilité de faire des affaires indique la position d'un pays par rapport aux autres en termes de conditions favorables aux entreprises. "
        "Un rang de 1 signifie que le pays a les réglementations les plus favorables."
    ),
    "IC.CNST.PRMT.RK": (
        "Ce rang mesure la facilité avec laquelle une entreprise peut obtenir des permis de construction. "
        "Un rang plus bas indique des procédures plus simples et moins coûteuses."
    ),
    "IC.CRED.ACC.CRD.RK": (
        "Ce rang évalue la facilité d'accès au crédit pour les entreprises. "
        "Un rang de 1 suggère un meilleur accès au financement."
    ),
    "IC.ELC.ACES.RK.DB19": (
        "Ce rang mesure la facilité d'accès à l'électricité pour les entreprises. "
        "Un rang élevé indique une meilleure disponibilité et fiabilité de l'électricité."
    ),
    "IC.REG.STRT.BUS.RK.DB19": (
        "Ce rang évalue la facilité de démarrage d'une entreprise dans un pays donné. "
        "Il prend en compte les procédures administratives, le coût, et le temps nécessaires."
    ),
    "PAY.TAX.RK.DB19": (
        "Ce rang mesure la facilité de paiement des taxes pour les entreprises. "
        "Un rang de 1 indique des procédures fiscales plus simples et moins coûteuses."
    ),
    "RESLV.ISV.RK.DB19": (
        "Ce rang évalue l'efficacité du système judiciaire dans la résolution des insolvabilités. "
        "Un rang élevé indique un processus plus rapide et efficace."
    ),
    "TRD.ACRS.BRDR.RK.DB19": (
        "Ce rang mesure la facilité de commerce à travers les frontières, incluant les procédures douanières et la logistique. "
        "Un rang de 1 suggère des barrières commerciales plus faibles."
    ),
    "NY.GDP.MKTP.CD": (
        "Le Produit Intérieur Brut (PIB) en dollars US courants représente la valeur totale de tous les biens et services finaux produits dans un pays au cours d'une année donnée."
    ),
    "NY.GDP.PCAP.CD": (
        "Le PIB par habitant en dollars US courants est le PIB total divisé par la population totale du pays, offrant une mesure approximative du niveau de vie moyen."
    ),
    "NY.GDP.DEFL.KD.ZG": (
        "Le déflateur du PIB est une mesure de l'inflation qui ajuste le PIB pour refléter les changements de prix. "
        "Il est exprimé en pourcentage annuel."
    ),
    "NY.GDP.MKTP.KD.ZG": (
        "La croissance du PIB (en pourcentage annuel) mesure l'augmentation ou la diminution de la production économique d'un pays d'une année à l'autre."
    ),
    "NY.GDP.PCAP.KD.ZG": (
        "La croissance du PIB par habitant (en pourcentage annuel) indique l'augmentation du PIB par individu, reflétant potentiellement une amélioration du niveau de vie."
    ),
    "NY.GNS.ICTR.CD": (
        "Les économies brutes en épargne (en dollars US courants) représentent la portion du revenu national qui n'est pas consommée et est disponible pour l'investissement."
    ),
    "BG.GSR.NFSV.GD.ZS": (
        "Le commerce des services en pourcentage du PIB mesure la contribution des services (comme le commerce, les finances, le tourisme) à l'économie d'un pays."
    ),
    "BM.GSR.GNFS.CD": (
        "Les importations de biens et services (Balance des Paiements, en dollars US courants) représentent la valeur totale des biens et services achetés par un pays à l'étranger."
    ),
    "BM.KLT.DINV.WD.GD.ZS": (
        "Les investissements directs étrangers nets en pourcentage du PIB indiquent le montant net des investissements étrangers dans les entreprises nationales, exprimé en pourcentage du PIB."
    ),
    "BN.CAB.XOKA.GD.ZS": (
        "Le solde du compte courant en pourcentage du PIB reflète la différence entre les exportations et les importations de biens et services, ajustée par les revenus primaires et secondaires."
    ),
    "BN.KLT.DINV.CD": (
        "Les investissements directs étrangers nets (Balance des Paiements, en dollars US courants) représentent les investissements directs reçus moins les investissements directs effectués par le pays."
    ),
    "BN.KLT.PTXL.CD": (
        "Les investissements de portefeuille nets (Balance des Paiements, en dollars US courants) mesurent les investissements en actions et obligations achetés ou vendus par des investisseurs étrangers."
    ),
    "BX.GSR.GNFS.CD": (
        "Les exportations de biens et services (Balance des Paiements, en dollars US courants) représentent la valeur totale des biens et services vendus à l'étranger."
    ),
    "CM.MKT.LCAP.GD.ZS": (
        "La capitalisation boursière des entreprises domestiques cotées en pourcentage du PIB mesure la taille totale des entreprises nationales cotées sur les marchés financiers."
    ),
    "GB.XPD.RSDV.GD.ZS": (
        "Les dépenses en recherche et développement en pourcentage du PIB indiquent l'investissement d'un pays dans l'innovation et le développement technologique."
    ),
    "GC.DOD.TOTL.GD.ZS": (
        "La dette publique totale en pourcentage du PIB mesure le montant total de la dette du gouvernement par rapport à la taille de l'économie."
    ),
    "EN.POP.DNST": (
        "La densité de population (personnes par km²) mesure la concentration de population dans une zone géographique donnée."
    ),
    "FI.RES.TOTL.CD": (
        "Les réserves totales (y compris l'or, en dollars US courants) représentent les actifs financiers détenus par la banque centrale d'un pays."
    ),
    "FP.CPI.TOTL": (
        "L'indice des prix à la consommation (2010 = 100) mesure la variation moyenne des prix des biens et services consommés par les ménages."
    ),
    "FP.CPI.TOTL.ZG": (
        "L'inflation des prix à la consommation (pourcentage annuel) indique le taux auquel le niveau général des prix des biens et services augmente."
    ),
    "FP.WPI.TOTL": (
        "L'indice des prix à la production (2010 = 100) mesure les changements de prix des biens en début de chaîne de production."
    ),
    "SE.ADT.LITR.ZS": (
        "Le taux d'alphabétisation des adultes (pourcentage) indique la proportion de personnes âgées de 15 ans et plus capables de lire et d'écrire."
    ),
    "SE.ADT.1524.LT.ZS": (
        "Le taux d'alphabétisation des jeunes (pourcentage) mesure la proportion de personnes âgées de 15 à 24 ans capables de lire et d'écrire."
    ),
    "SH.DTH.IMRT": (
        "Le nombre de décès d'infants représente le nombre de décès d'enfants de moins d'un an dans une population donnée."
    ),
    "SH.MED.BEDS.ZS": (
        "Le nombre de lits d'hôpital (par 1 000 personnes) indique la disponibilité des infrastructures médicales dans un pays."
    ),
    "SI.POV.GINI": (
        "L'indice de Gini mesure l'inégalité de la distribution des revenus au sein d'un pays. Un indice de 0 représente une égalité parfaite, tandis qu'un indice de 100 indique une inégalité maximale."
    ),
    "SL.UEM.1524.NE.ZS": (
        "Le taux de chômage des jeunes (pourcentage) mesure la proportion de jeunes âgés de 15 à 24 ans qui sont sans emploi mais recherchent activement du travail."
    ),
    "SL.UEM.TOTL.NE.ZS": (
        "Le taux de chômage total (pourcentage) indique la proportion de la population active qui est sans emploi et à la recherche active de travail."
    ),
    "SM.POP.NETM": (
        "La migration nette représente le solde entre les immigrations et les émigrations dans un pays. Un solde positif indique plus d'immigrants que d'émigrants."
    ),
    "SP.DYN.LE00.IN": (
        "L'espérance de vie à la naissance (années) mesure le nombre moyen d'années qu'un nouveau-né peut s'attendre à vivre, en supposant que les conditions de mortalité actuelles restent constantes."
    ),
    "SP.POP.GROW": (
        "La croissance démographique (pourcentage annuel) indique le taux auquel la population d'un pays augmente ou diminue."
    ),
    "SP.POP.TOTL": (
        "La population totale représente le nombre total d'habitants dans un pays à un moment donné."
    ),
    "SP.RUR.TOTL": (
        "La population rurale indique le nombre de personnes vivant dans des zones non urbaines ou rurales."
    ),
    "SP.URB.TOTL": (
        "La population urbaine représente le nombre de personnes vivant dans des zones urbaines ou villes."
    ),
    "GE.EST": (
        "L'efficacité gouvernementale estime la qualité des services publics, la qualité de la gestion publique et la crédibilité des politiques publiques."
    ),
    "PV.EST": (
        "La stabilité politique et l'absence de violence/terrorisme évaluent la probabilité de désordres politiques, de violence ou de terrorisme dans un pays."
    ),
}


def sanitize_key(text):
    """
    Sanitizes a string to be used as a Streamlit widget key.
    Replaces spaces with underscores and removes non-alphanumeric characters.
    """
    text = text.replace(" ", "_")
    text = re.sub(r'\W+', '', text)
    return text

@st.cache_data
def fetch_data(indicators, countries, date_range):
    """
    Fetches data from wbdata and returns a DataFrame.
    """
    return wbdata.get_dataframe(
        indicators,
        country=countries,
        date=date_range,
    )

rank_indicators = [
    "IC.BUS.EASE.XQ",
    "IC.CNST.PRMT.RK",
    "IC.CRED.ACC.CRD.RK",
    "IC.ELC.ACES.RK.DB19",
    "IC.REG.STRT.BUS.RK.DB19",
    "PAY.TAX.RK.DB19",
    "RESLV.ISV.RK.DB19",
    "TRD.ACRS.BRDR.RK.DB19",
]

def EconomicAnalysisTab():
    st.title("📊 Analyse Approfondie des Facteurs Économiques Mondiaux")

    st.header("🌍 Carte des Pays Sélectionnés")
    
    countries_data = wbdata.get_countries()
    countries_df = pd.DataFrame(countries_data)[["id", "name"]].sort_values("name")
    country_names = countries_df["name"].tolist()

    selected_countries = st.multiselect(
        "Choisissez un ou plusieurs pays :", 
        options=country_names,
        default=["France", "United States"] 
    )

    if selected_countries:
        map_df = pd.DataFrame({
            'Country': selected_countries,
            'Selected': [1]*len(selected_countries) 
        })

        fig_map = px.choropleth(
            map_df,
            locations="Country",
            locationmode='country names',
            color="Selected",
            color_continuous_scale=["lightgrey", "#636EFA"],
            hover_name="Country",
            title="Pays Sélectionnés",
            projection="natural earth"
        )

        fig_map.update_layout(
            height=600,
            coloraxis_showscale=False, 
            paper_bgcolor='rgba(0,0,0,0)',  
            geo_bgcolor='rgba(0,0,0,0)',   
            margin={"r":0,"t":50,"l":0,"b":0}
        )

        st.plotly_chart(fig_map, use_container_width=True, key="selected_countries_map")
    else:
        st.write("Aucun pays sélectionné pour la carte.")

    st.markdown("---")  

    years = list(range(1960, datetime.datetime.now().year + 1))  
    years_sorted = sorted(years)
    start_year, end_year = st.select_slider(
        "Sélectionnez la plage d'années :", 
        options=years_sorted,
        value=(1960, datetime.datetime.now().year)
    )

    if st.button("Ok"):
        if not selected_countries:
            st.warning("Veuillez sélectionner au moins un pays.")
            return

        if end_year < start_year:
            st.error("L'année de fin doit être postérieure ou égale à l'année de début.")
            return

        selected_country_ids = countries_df.loc[
            countries_df["name"].isin(selected_countries),
            "id"
        ].tolist()

        all_indicators = []
        for topic, indicators in grouped_indicators.items():
            for ind_id, ind_name in indicators.items():
                all_indicators.append((ind_id, ind_name))

        all_indicators_dict = dict(all_indicators)

        date_range = (str(start_year), str(end_year))

        with st.spinner('Récupération des données...'):
            try:
                df = fetch_data(
                    indicators=all_indicators_dict,
                    countries=selected_country_ids,
                    date_range=date_range
                )
            except Exception as e:
                st.error(f"Erreur lors de la récupération des données: {e}")
                return

        if df.empty:
            st.error("Aucune donnée trouvée pour les paramètres sélectionnés.")
            return

        df = df.reset_index()

        if "country" not in df.columns:
            if len(selected_countries) == 1:
                df["country"] = selected_countries[0]
            else:
                df["country"] = "Unknown"
                st.warning("La colonne 'country' est manquante et a été remplie avec 'Unknown'.")

        try:
            df_melted = df.melt(
                id_vars=["country", "date"],
                var_name="indicator",
                value_name="value"
            )
        except KeyError as e:
            st.error(f"Erreur lors de la transformation des données: {e}")
            return

        indicators_flat = []
        for topic, indicators in grouped_indicators.items():
            for ind_id, ind_name in indicators.items():
                indicators_flat.append({
                    "indicator_id": ind_id,
                    "indicator_name": ind_name,
                    "topic": topic
                })
        indicators_df = pd.DataFrame(indicators_flat)

        df_merged = df_melted.merge(
            indicators_df,
            how="left",
            left_on="indicator",
            right_on="indicator_name"
        )

        unmatched = df_merged[df_merged["topic"].isna()]["indicator"].unique()
        if len(unmatched) > 0:
            st.warning(f"Les indicateurs suivants n'ont pas été regroupés: {', '.join(unmatched)}")

        try:
            df_merged["date"] = pd.to_numeric(df_merged["date"], errors='coerce').astype('Int64')
        except ValueError:
            st.error("Conversion des dates en entiers a échoué. Veuillez vérifier les données.")
            return

        df_merged = df_merged.dropna(subset=["date"])

        st.header("📈 Visualisation des Indicateurs Économiques")

        for topic, indicators in grouped_indicators.items():
            st.subheader(topic)

            df_topic = df_merged[df_merged["topic"] == topic]

            if df_topic.empty:
                st.write(f"Aucune donnée disponible pour le sujet '{topic}'.")
                continue

            topic_indicators_df = df_topic[['indicator', 'indicator_id', 'indicator_name']].drop_duplicates()

            plots_per_row = 2
            num_plots = len(topic_indicators_df)
            rows = (num_plots + plots_per_row - 1) // plots_per_row 

            for row in range(rows):
                cols = st.columns(plots_per_row)
                for idx, col in enumerate(cols):
                    plot_idx = row * plots_per_row + idx
                    if plot_idx >= num_plots:
                        break
                    indicator_id = topic_indicators_df.iloc[plot_idx]['indicator_id']
                    indicator_name = topic_indicators_df.iloc[plot_idx]['indicator_name']

                    if indicator_id == "SP.POP.TOTL":
                        pop_growth_id = "SP.POP.GROW"
                        pop_growth_name = grouped_indicators[topic].get(pop_growth_id, "Population growth")

                        df_pop_total = df_topic[df_topic["indicator_id"] == indicator_id]
                        df_pop_growth = df_topic[df_topic["indicator_id"] == pop_growth_id]

                        if df_pop_growth.empty:
                            col.warning(f"L'indicateur de croissance de la population '{pop_growth_name}' est manquant.")
                            continue

                        df_combined = pd.merge(
                            df_pop_total[['country', 'date', 'value']],
                            df_pop_growth[['country', 'date', 'value']],
                            on=['country', 'date'],
                            suffixes=('_total', '_growth')
                        )

                        gdp_pivot_total = df_combined.pivot(index="date", columns="country", values="value_total")
                        gdp_pivot_growth = df_combined.pivot(index="date", columns="country", values="value_growth")

                        countries_with_no_data_total = gdp_pivot_total.columns[gdp_pivot_total.isna().all()].tolist()
                        countries_with_no_data_growth = gdp_pivot_growth.columns[gdp_pivot_growth.isna().all()].tolist()
                        countries_with_no_data = list(set(countries_with_no_data_total + countries_with_no_data_growth))

                        gdp_pivot_total = gdp_pivot_total.drop(columns=countries_with_no_data, errors='ignore')
                        gdp_pivot_growth = gdp_pivot_growth.drop(columns=countries_with_no_data, errors='ignore')

                        if countries_with_no_data:
                            col.info(f"Pour les indicateurs 'Population, total' et 'Population growth', les pays suivants ont été exclus en raison de l'absence de données : {', '.join(countries_with_no_data)}.")

                        if gdp_pivot_total.empty and gdp_pivot_growth.empty:
                            col.write("Aucune donnée disponible pour les pays sélectionnés après exclusion des pays sans données.")
                            continue

                        earliest_year_total = gdp_pivot_total.dropna().index.min() if not gdp_pivot_total.empty else None
                        earliest_year_growth = gdp_pivot_growth.dropna().index.min() if not gdp_pivot_growth.empty else None
                        earliest_year = min(filter(None, [earliest_year_total, earliest_year_growth]))
                        latest_year = max(
                            gdp_pivot_total.dropna().index.max() if not gdp_pivot_total.empty else 0,
                            gdp_pivot_growth.dropna().index.max() if not gdp_pivot_growth.empty else 0
                        )

                        fig = make_subplots(specs=[[{"secondary_y": True}]])

                        if not gdp_pivot_total.empty:
                            for country in gdp_pivot_total.columns:
                                fig.add_trace(
                                    go.Bar(
                                        x=gdp_pivot_total.index,
                                        y=gdp_pivot_total[country],
                                        name=f"{country} - Population Totale",
                                        opacity=0.6
                                    ),
                                    secondary_y=False,
                                )

                        if not gdp_pivot_growth.empty:
                            for country in gdp_pivot_growth.columns:
                                fig.add_trace(
                                    go.Scatter(
                                        x=gdp_pivot_growth.index,
                                        y=gdp_pivot_growth[country],
                                        mode="lines",
                                        name=f"{country} - Croissance de la Population",
                                        line=dict(width=2),
                                        hovertemplate='%{y}%'
                                    ),
                                    secondary_y=True,
                                )

                        fig.update_layout(
                            title_text="Population Totale et Croissance de la Population",
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,  
                                xanchor="center",
                                x=0.5
                            ),
                            template="plotly_white",
                            height=600,
                            margin=dict(r=50, t=100, l=50, b=80)
                        )

                        fig.update_yaxes(title_text="Population Totale", secondary_y=False)
                        fig.update_yaxes(title_text="Croissance de la Population (%)", secondary_y=True)

                        fig.update_xaxes(range=[earliest_year, end_year], dtick=2, title_text="Année")

                        col.plotly_chart(fig, use_container_width=True, key="combined_population_plot")

                        col.markdown(
                            """
                            **Population Totale et Croissance de la Population**

                            - **Population Totale**: Représente le nombre total d'habitants dans un pays à un moment donné. C'est une mesure clé de la taille démographique et a des implications sur le marché du travail, la demande de biens et services, et la planification des infrastructures.

                            - **Croissance de la Population**: Indique le taux auquel la population d'un pays augmente ou diminue chaque année. Une croissance positive peut signaler une expansion économique potentielle mais aussi des défis en termes de ressources et de services publics. Une croissance négative peut indiquer un vieillissement de la population ou des défis démographiques.
                            """
                        )
                        continue  

                    if indicator_id in rank_indicators:
                        plot_type = "bar"
                    else:
                        plot_type = "line"

                    df_ind = df_topic[df_topic["indicator_id"] == indicator_id]

                    gdp_pivot = df_ind.pivot(index="date", columns="country", values="value")

                    countries_with_no_data = gdp_pivot.columns[gdp_pivot.isna().all()].tolist()

                    gdp_pivot = gdp_pivot.drop(columns=countries_with_no_data, errors='ignore')

                    if countries_with_no_data:
                        col.info(f"Pour l'indicateur '{indicator_name}', les pays suivants ont été exclus en raison de l'absence de données : {', '.join(countries_with_no_data)}.")

                    if gdp_pivot.empty:
                        col.write("Aucune donnée disponible pour les pays sélectionnés après exclusion des pays sans données.")
                        continue

                    years_with_data = gdp_pivot.index[gdp_pivot.notna().any(axis=1)].tolist()

                    gdp_pivot_filtered = gdp_pivot.loc[years_with_data]

                    earliest_year = gdp_pivot_filtered.index.min()

                    fig = go.Figure()

                    if plot_type == "bar":
                        for country in gdp_pivot_filtered.columns:
                            fig.add_trace(
                                go.Bar(
                                    x=gdp_pivot_filtered.index,
                                    y=gdp_pivot_filtered[country],
                                    name=country
                                )
                            )
                        fig.update_layout(
                            yaxis_title=indicator_name,
                            barmode='group',
                            title={
                                'text': indicator_name,
                                'y':0.95,
                                'x':0.5,
                                'xanchor': 'center',
                                'yanchor': 'top'
                            },
                            xaxis=dict(
                                categoryorder='category ascending',
                                tickmode='array',
                                tickvals=years_with_data,
                                ticktext=[str(year) for year in years_with_data],
                                title_text="Année"
                            ),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,  
                                xanchor="center",
                                x=0.5
                            ),
                            template="plotly_white",
                            height=400,
                            margin=dict(r=0, t=80, l=0, b=80)
                        )
                    else:
                        for country in gdp_pivot_filtered.columns:
                            fig.add_trace(
                                go.Scatter(
                                    x=gdp_pivot_filtered.index,
                                    y=gdp_pivot_filtered[country],
                                    mode="lines",
                                    name=country,
                                    line=dict(width=2)
                                )
                            )
                        fig.update_layout(
                            yaxis_title=indicator_name,
                            title={
                                'text': indicator_name,
                                'y':0.95,
                                'x':0.5,
                                'xanchor': 'center',
                                'yanchor': 'top'
                            },
                            xaxis=dict(
                                range=[earliest_year, end_year],
                                dtick=2, 
                                title_text="Année"
                            ),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02, 
                                xanchor="center",
                                x=0.5
                            ),
                            template="plotly_white",
                            height=400,
                            margin=dict(r=0, t=80, l=0, b=80)
                        )

                    fig.update_layout(
                        legend_title_text="Pays",
                        xaxis_title="Année",
                        yaxis_title=indicator_name,
                        template="plotly_white",
                        height=400,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="center",
                            x=0.5
                        ),
                        margin=dict(r=0, t=80, l=0, b=80)
                    )

                    sanitized_topic = sanitize_key(topic)
                    sanitized_indicator = sanitize_key(indicator_name)
                    plot_key = f"plot_{sanitized_topic}_{sanitized_indicator}"

                    col.plotly_chart(fig, use_container_width=True, key=plot_key)

                    description = indicator_descriptions.get(indicator_id, "Description non disponible pour cet indicateur.")
                    col.markdown(
                        f"""
                        **{indicator_name}**

                        {description}
                        """
                    )


def ProjectionsTab():
    st.title("🔮 Projections Économiques")

    st.header("📥 Téléchargement des Données du World Economic Outlook (WEO)")

    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month
    desired_release_month = 10  

    def find_latest_release(year, desired_month):
        for month_offset in range(0, desired_release_month):
            release_month = desired_release_month - month_offset
            try:
                release_date = datetime.datetime(year, release_month, 1)
                release_str = release_date.strftime('%b')
                filename = f'weo_{year}_{release_str}.csv'
                weo.download(year=year, release=release_str, filename=filename)  
                return filename, release_str
            except Exception as e:
                st.warning(f"Échec du téléchargement pour {release_str} {year}: {e}")
                continue
        return None, None

    filename, release = find_latest_release(current_year, desired_release_month)

    if filename and release:
        st.success(f"Données WEO téléchargées avec succès: {filename} (Release: {release})")
    else:
        st.error("Impossible de télécharger les données WEO pour l'année en cours. Veuillez vérifier la disponibilité des releases.")
        return  

    st.header("📊 Sélection du Pays pour les Projections")

    try:
        weo_data = weo.WEO(filename)
    except Exception as e:
        st.error(f"Erreur lors du chargement des données WEO: {e}")
        return

    countries = weo_data.countries()
    if 'Country' not in countries.columns or 'ISO' not in countries.columns:
        st.error("Le fichier WEO ne contient pas les colonnes 'Country' ou 'ISO'. Veuillez vérifier le fichier téléchargé.")
        return

    country_list = countries['Country'].unique().tolist()
    selected_country = st.selectbox("Sélectionnez un pays :", options=country_list)

    if not selected_country:
        st.warning("Veuillez sélectionner un pays pour afficher les projections.")
        return

    try:
        country_ISO = str(countries[countries['Country'] == selected_country]['ISO'].iloc[0])
    except IndexError:
        st.error("Code ISO du pays non trouvé. Veuillez vérifier la sélection.")
        return

    st.header(f"📈 Projections Économiques pour {selected_country}")

    try:
        c = weo_data.country(country_ISO)
    except Exception as e:
        st.error(f"Erreur lors de l'extraction des données pour le pays {selected_country}: {e}")
        return

    df = pd.DataFrame()

    try:
        df["GDP"] = (c.NGDP_RPCH.dropna() / 100 + 1).cumprod() * 100
        df["CPI"] = c.PCPIPCH
        df["FX"] = c.NGDP / c.NGDPD
        df["DEFICIT"] = (c.GGR - c.GGX) / c.NGDP * 100
        df["CA"] = c.BCA / c.NGDPD * 100

        df["_GDEBT"] = (c.GGXWDG / c.NGDP) * 100
        df["_NDEBT"] = (c.GGXWDN / c.NGDP) * 100
    except AttributeError as e:
        st.error(f"Erreur lors de l'accès aux attributs des données WEO: {e}")
        return

    if isinstance(df.index, pd.PeriodIndex):
        df.index = df.index.to_timestamp()

    elif not pd.api.types.is_datetime64_any_dtype(df.index):
        df.index = df.index.astype(str)

    st.subheader(f"Projections Économiques pour {selected_country}")

    st.write(df)

    fig = make_subplots(
        rows=3, cols=3,
        vertical_spacing=0.1,
        horizontal_spacing=0.1
        )

    if "GDP" in df.columns and df["GDP"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["GDP"],
                mode="lines",
                name="Croissance du PIB",
                line=dict(color="#636EFA", width=2)
            ),
            row=1, col=1
        )

    if "CPI" in df.columns and df["CPI"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["CPI"],
                mode="lines",
                name="Inflation CPI",
                line=dict(color="#00CC96", width=2)
            ),
            row=1, col=2
        )

    if "CA" in df.columns and df["CA"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["CA"],
                mode="lines",
                name="Compte Courant",
                line=dict(color="#FFA15A", width=2)
            ),
            row=1, col=3
        )

    if "FX" in df.columns and df["FX"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["FX"],
                mode="lines",
                name="Taux de Change",
                line=dict(color="#AB63FA", width=2)
            ),
            row=2, col=1
        )

    if "DEFICIT" in df.columns and df["DEFICIT"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["DEFICIT"],
                mode="lines",
                name="Déficit Budgétaire",
                line=dict(color="#19D3F3", width=2)
            ),
            row=2, col=2
        )

    if "_GDEBT" in df.columns and df["_GDEBT"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["_GDEBT"],
                mode="lines",
                name="Dette Publique Brute",
                line=dict(color="#FF6692", width=2)
            ),
            row=2, col=3
        )

    if "_NDEBT" in df.columns and df["_NDEBT"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["_NDEBT"],
                mode="lines",
                name="Dette Publique Nette",
                line=dict(color="#B6E880", width=2)
            ),
            row=3, col=1
        )

    fig.update_layout(
        height=900,
        width=1200,
        showlegend=True,
        title_text=f"Projections Économiques pour {selected_country} ({release} Release {current_year})",
        template="plotly_white",
        margin=dict(r=50, t=100, l=50, b=50)
    )

    current_year_plot = datetime.datetime.now().year
    for i in range(1, 4):
        for j in range(1, 4):
            fig.add_vline(x=current_year_plot, line_dash="dash", line_color="lightblue", row=i, col=j)

    for i in range(1, 4):
        for j in range(1, 4):
            if j in [1, 2, 3]: 
                fig.add_hline(y=0, line_dash="dash", line_color="orange", row=i, col=j)

    st.plotly_chart(fig, use_container_width=True)

def main():
    tabs = st.tabs(["🔍 Analyse Économique", "🔮 Projections"])

    with tabs[0]:
        EconomicAnalysisTab()

    with tabs[1]:
        ProjectionsTab()

if __name__ == "__main__":
    main()
