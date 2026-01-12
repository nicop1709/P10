"""
Application Streamlit pour démontrer le système de recommandation d'articles
"""
import streamlit as st
import requests
import json
import pandas as pd
import time

# Configuration
AZURE_FUNCTION_URL = "https://func-recommender-1768155564.azurewebsites.net/api/recommendarticle"

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
    try:
        # Mesurer le temps de réponse
        start_time = time.time()

        # Appel à l'API
        response = requests.post(
            AZURE_FUNCTION_URL,
            json={"user_id": user_id},
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
        # Afficher les informations
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("User ID", result['user_id'])
        with col2:
            st.metric("Nombre de recommandations", result['count'])
        with col3:
            st.metric("Temps de réponse", f"{result['elapsed_time']:.2f}s")

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

        # Message de succès
        st.success("✅ Recommandations récupérées avec succès!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Système de recommandation basé sur Collaborative Filtering (ALS)</p>
    <p>Déployé sur Azure Functions | Développé avec Streamlit</p>
</div>
""", unsafe_allow_html=True)
