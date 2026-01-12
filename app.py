"""
Application Streamlit pour démontrer le système de recommandation d'articles
"""
import streamlit as st
import requests
import json
import pandas as pd
import time
import os

# Configuration
AZURE_FUNCTION_URL = "https://func-recommender-1768155564.azurewebsites.net/api/recommendarticle"

# Récupérer la clé depuis les variables d'environnement
AZURE_FUNCTION_KEY = os.environ.get('AZURE_FUNCTION_KEY')

# Tarification Azure Functions (Consumption Plan - Pay-as-you-go)
# Source: https://azure.microsoft.com/en-us/pricing/details/functions/
COST_PER_EXECUTION = 0.20 / 1_000_000  # $0.20 per million executions
COST_PER_GB_SECOND = 0.000016  # $0.000016 per GB-second
ESTIMATED_MEMORY_GB = 0.512  # Estimation: 512 MB de mémoire utilisée
FREE_EXECUTIONS_PER_MONTH = 1_000_000  # Premier million d'exécutions gratuit
FREE_GB_SECONDS_PER_MONTH = 400_000  # Premiers 400,000 GB-s gratuits

# Configuration de la page
st.set_page_config(
    page_title="Système de Recommandation d'Articles",
    page_icon="📰",
    layout="wide"
)

# Titre principal
st.title("📰 Système de Recommandation d'Articles")
st.markdown("---")

# Description
st.markdown("""
Cette application démontre le système de recommandation d'articles déployé sur Azure.
Sélectionnez un utilisateur pour obtenir 5 recommandations d'articles personnalisées.
""")

# Fonction pour calculer le coût Azure
def calculate_azure_cost(execution_time_seconds):
    """
    Calcule le coût estimé d'une exécution Azure Function

    Args:
        execution_time_seconds: Temps d'exécution en secondes

    Returns:
        dict: Détails du coût (total, exécution, mémoire)
    """
    # Coût d'exécution
    execution_cost = COST_PER_EXECUTION

    # Coût de mémoire (GB-seconds)
    gb_seconds = ESTIMATED_MEMORY_GB * execution_time_seconds
    memory_cost = gb_seconds * COST_PER_GB_SECOND

    # Coût total
    total_cost = execution_cost + memory_cost

    return {
        'total': total_cost,
        'execution': execution_cost,
        'memory': memory_cost,
        'gb_seconds': gb_seconds
    }

# Charger les métadonnées des articles si disponibles
@st.cache_data
def load_articles_metadata():
    """Charge les métadonnées des articles"""
    try:
        df = pd.read_csv('articles_metadata.csv')
        return df
    except Exception as e:
        st.warning(f"Impossible de charger les métadonnées des articles: {e}")
        return None

# Fonction pour appeler l'Azure Function
def get_recommendations(user_id):
    """
    Appelle l'Azure Function pour obtenir les recommandations

    Args:
        user_id: ID de l'utilisateur

    Returns:
        dict: Réponse de l'API ou None en cas d'erreur
    """
    if not AZURE_FUNCTION_KEY:
        st.error("❌ Clé Azure Function non configurée. Définissez la variable d'environnement AZURE_FUNCTION_KEY.")
        st.info("💡 Utilisez: `export AZURE_FUNCTION_KEY='votre_cle'` ou exécutez `source set_api_key.sh`")
        return None
    
    try:
        # Mesurer le temps de réponse
        start_time = time.time()

        # Appel à l'API avec la clé d'authentification
        response = requests.post(
            AZURE_FUNCTION_URL,
            json={"user_id": user_id},
            params={"code": AZURE_FUNCTION_KEY},
            timeout=30
        )

        elapsed_time = time.time() - start_time

        # Vérifier le statut
        if response.status_code == 200:
            result = response.json()
            result['elapsed_time'] = elapsed_time
            return result
        else:
            st.error(f"Erreur HTTP {response.status_code}: {response.text}")
            return None

    except requests.exceptions.Timeout:
        st.error("La requête a expiré. L'Azure Function met trop de temps à répondre.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de l'appel à l'API: {e}")
        return None
    except Exception as e:
        st.error(f"Erreur inattendue: {e}")
        return None

# Interface utilisateur
st.markdown("## 👤 Sélection de l'utilisateur")

col1, col2 = st.columns([2, 3])

with col1:
    # Liste de quelques user_ids pour la démo
    # On propose quelques IDs d'utilisateurs courants
    user_id_input = st.number_input(
        "Entrez l'ID de l'utilisateur",
        min_value=0,
        max_value=1000000,
        value=0,
        step=1,
        help="Entrez un ID d'utilisateur (ex: 0, 1, 100, etc.)"
    )

    # Bouton pour lancer la recommandation
    recommend_button = st.button("🔍 Obtenir les recommandations", type="primary", use_container_width=True)

with col2:
    st.info("""
    **💡 Exemples d'utilisateurs:**
    - **User 0**: Nouvel utilisateur (recommandations par popularité)
    - **User 1-1000**: Utilisateurs actifs avec historique
    - Essayez différents IDs pour voir les variations!
    """)

# Ligne de séparation
st.markdown("---")

# Traitement de la recommandation
if recommend_button:
    st.markdown("## 📊 Résultats")

    with st.spinner(f"⏳ Récupération des recommandations pour l'utilisateur {user_id_input}..."):
        result = get_recommendations(user_id_input)

    if result:
        # Calculer le coût Azure
        cost_details = calculate_azure_cost(result['elapsed_time'])

        # Afficher les informations
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("User ID", result['user_id'])
        with col2:
            st.metric("Recommandations", result['count'])
        with col3:
            st.metric("Temps de réponse", f"{result['elapsed_time']:.2f}s")
        with col4:
            # Afficher le coût en micro-dollars pour plus de lisibilité
            cost_micro = cost_details['total'] * 1_000_000
            st.metric("Coût estimé", f"${cost_details['total']:.6f}",
                     help=f"≈ {cost_micro:.2f} µ$ (micro-dollars)\n\n"
                          f"Détails:\n"
                          f"• Exécution: ${cost_details['execution']:.8f}\n"
                          f"• Mémoire ({cost_details['gb_seconds']:.3f} GB-s): ${cost_details['memory']:.8f}\n\n"
                          f"Note: Les premiers {FREE_EXECUTIONS_PER_MONTH:,} exécutions/mois "
                          f"et {FREE_GB_SECONDS_PER_MONTH:,} GB-s/mois sont gratuits.")

        st.markdown("### 🎯 Articles recommandés")

        # Charger les métadonnées si disponibles
        articles_df = load_articles_metadata()

        # Créer un DataFrame pour afficher les recommandations
        recommendations = result['recommendations']

        if articles_df is not None:
            # Enrichir avec les métadonnées
            reco_data = []
            for idx, article_id in enumerate(recommendations, 1):
                article_info = articles_df[articles_df['article_id'] == article_id]
                if not article_info.empty:
                    reco_data.append({
                        'Rang': idx,
                        'Article ID': article_id,
                        'Catégorie': article_info.iloc[0]['category_id'],
                        'Éditeur': article_info.iloc[0]['publisher_id'],
                        'Nombre de mots': article_info.iloc[0]['words_count']
                    })
                else:
                    reco_data.append({
                        'Rang': idx,
                        'Article ID': article_id,
                        'Catégorie': 'N/A',
                        'Éditeur': 'N/A',
                        'Nombre de mots': 'N/A'
                    })

            reco_df = pd.DataFrame(reco_data)

            # Afficher le tableau avec style
            st.dataframe(
                reco_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            # Affichage simple sans métadonnées
            reco_data = []
            for idx, article_id in enumerate(recommendations, 1):
                reco_data.append({
                    'Rang': idx,
                    'Article ID': article_id
                })

            reco_df = pd.DataFrame(reco_data)
            st.dataframe(
                reco_df,
                use_container_width=True,
                hide_index=True
            )

        # Afficher la réponse JSON brute (optionnel, pour le debug)
        with st.expander("🔍 Voir la réponse JSON complète"):
            st.json(result)

        # Afficher les détails des coûts
        with st.expander("💰 Détails du coût Azure (Consumption Plan)"):
            st.markdown("### Coût de cette requête")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                **Coût total**: ${cost_details['total']:.8f} (≈ {cost_micro:.2f} µ$)

                **Détail**:
                - Coût d'exécution: ${cost_details['execution']:.8f}
                - Coût mémoire: ${cost_details['memory']:.8f}
                - GB-secondes: {cost_details['gb_seconds']:.3f}
                """)

            with col2:
                st.markdown(f"""
                **Tarification Azure**:
                - Exécutions: $0.20 / million
                - Mémoire: $0.000016 / GB-s
                - Mémoire estimée: {ESTIMATED_MEMORY_GB*1024:.0f} MB

                **Offre gratuite**: ✅
                - 1M exécutions/mois
                - 400,000 GB-s/mois
                """)

            st.markdown("### 📊 Projections de coût")

            # Calculer les coûts pour différentes charges
            scenarios = [
                ("100 requêtes/jour", 100 * 30),
                ("1,000 requêtes/jour", 1_000 * 30),
                ("10,000 requêtes/jour", 10_000 * 30),
                ("100,000 requêtes/jour", 100_000 * 30),
            ]

            projections = []
            for scenario_name, monthly_requests in scenarios:
                monthly_cost = monthly_requests * cost_details['total']
                # Soustraire l'offre gratuite
                free_cost_executions = min(monthly_requests, FREE_EXECUTIONS_PER_MONTH) * COST_PER_EXECUTION
                free_cost_gb_s = min(monthly_requests * cost_details['gb_seconds'], FREE_GB_SECONDS_PER_MONTH) * COST_PER_GB_SECOND
                free_cost_total = free_cost_executions + free_cost_gb_s

                actual_cost = max(0, monthly_cost - free_cost_total)

                projections.append({
                    'Scénario': scenario_name,
                    'Requêtes/mois': f"{monthly_requests:,}",
                    'Coût brut': f"${monthly_cost:.4f}",
                    'Offre gratuite': f"-${free_cost_total:.4f}",
                    'Coût réel': f"${actual_cost:.4f}"
                })

            proj_df = pd.DataFrame(projections)
            st.dataframe(proj_df, use_container_width=True, hide_index=True)

            st.info("""
            💡 **Note importante**:
            Ces calculs sont des estimations basées sur le temps d'exécution observé et une mémoire estimée de 512 MB.
            Le coût réel peut varier selon la charge du système et la complexité des requêtes.
            Avec l'offre gratuite Azure, vous pouvez servir jusqu'à **1 million de requêtes par mois gratuitement**!
            """)

        # Message de succès
        st.success("✅ Recommandations récupérées avec succès!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Système de recommandation basé sur Collaborative Filtering (ALS)</p>
    <p>Déployé sur Azure Functions (Consumption Plan) | Développé avec Streamlit</p>
    <p style='font-size: 0.9em;'>💰 Coût estimé: ~$0.000025 par requête | 1M requêtes/mois gratuites</p>
</div>
""", unsafe_allow_html=True)
