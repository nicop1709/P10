"""
Script pour préparer le déploiement Azure Function
Copie les fichiers nécessaires dans le dossier azure_function
"""

import shutil
from pathlib import Path

def prepare_deployment():
    """Prépare les fichiers pour le déploiement"""
    print("=== PRÉPARATION DU DÉPLOIEMENT ===")
    
    base_dir = Path(__file__).parent
    azure_function_dir = base_dir / "azure_function"
    recommend_article_dir = azure_function_dir / "RecommendArticle"
    
    # Fichiers à copier
    files_to_copy = {
        'recommender.py': recommend_article_dir / 'recommender.py',
    }
    
    # Vérifier que les fichiers source existent
    print("\n1. Vérification des fichiers source...")
    for source_file, dest_file in files_to_copy.items():
        source_path = base_dir / source_file
        if not source_path.exists():
            print(f"   ⚠️  Fichier manquant: {source_path}")
        else:
            print(f"   ✅ {source_file}")
    
    # Copier les fichiers
    print("\n2. Copie des fichiers...")
    for source_file, dest_file in files_to_copy.items():
        source_path = base_dir / source_file
        if source_path.exists():
            shutil.copy2(source_path, dest_file)
            print(f"   ✅ Copié: {source_file} -> {dest_file.relative_to(base_dir)}")
    
    # Vérifier les artefacts
    print("\n3. Vérification des artefacts...")
    artifacts = ['als_model.pkl', 'metadata.pkl', 'csr_train.pkl']
    for artifact in artifacts:
        artifact_path = base_dir / artifact
        if artifact_path.exists():
            size_mb = artifact_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ {artifact} ({size_mb:.2f} MB)")
        else:
            print(f"   ⚠️  {artifact} manquant - Exécutez d'abord serialize_artifacts.py")
    
    print("\n=== PRÉPARATION TERMINÉE ===")
    print("\nProchaines étapes:")
    print("1. Vérifiez que les artefacts sont générés (serialize_artifacts.py)")
    print("2. Testez localement: cd azure_function && func start")
    print("3. Déployez: func azure functionapp publish <function-app-name>")

if __name__ == "__main__":
    prepare_deployment()

