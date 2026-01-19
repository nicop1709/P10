# Application Streamlit (extrait autonome)

Ce dossier rassemble uniquement ce qu'il faut pour faire tourner l'app Streamlit du projet afin de la deplacer dans un depot separe.

## Contenu
- `app.py` : code Streamlit appelant l'Azure Function de recommandation
- `articles_metadata.csv` : metadonnees pour enrichir les recommandations
- `requirements.txt` : dependances necessaires
- `run_streamlit.sh` : script de lancement (charge `.env` et verifie `FUNCTION_KEY`)
- `.env.example` : modele pour fournir la cle d'API Azure Function

## Lancer l'app
1. (Optionnel) Creer/activer un venv Python.
2. Installer les dependances : `pip install -r requirements.txt`.
3. Copier `.env.example` en `.env` et renseigner `FUNCTION_KEY` (cle "code" de l'Azure Function).
4. Demarrer : `./run_streamlit.sh` ou `streamlit run app.py` depuis ce dossier.

## Notes
- L'URL de l'Azure Function est definie dans `app.py` (`AZURE_FUNCTION_URL`). Adaptez-la si vous deployeez une autre instance.
- Si `articles_metadata.csv` est absent, l'app reste fonctionnelle mais n'affichera pas les informations d'article enrichies.
