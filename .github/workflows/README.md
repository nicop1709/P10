# GitHub Actions Workflows

Ce dossier contient les workflows GitHub Actions pour l'automatisation du déploiement et des tests.

## Workflows Disponibles

### 1. `azure-function-deploy.yml` - Déploiement Automatique

**Déclenchement**:
- Push sur la branche `main`
- Modifications dans `azure_function/`
- Déclenchement manuel via GitHub Actions

**Actions**:
- ✅ Installe Python 3.11
- ✅ Installe les dépendances
- ✅ Exécute les tests (si disponibles)
- ✅ Déploie sur Azure Functions
- ✅ Vérifie le déploiement

**Durée**: ~3-5 minutes

### 2. `azure-function-test.yml` - Tests sur Pull Requests

**Déclenchement**: Pull Request vers `main`

Ce workflow teste le code **sans déployer**:
- ✅ Vérifie le formatage du code (black)
- ✅ Analyse le code (pylint)
- ✅ Exécute les tests (pytest)
- ✅ Utilise le cache pour accélérer les builds

## Configuration

Voir le guide complet: [../../CI_CD_SETUP.md](../../CI_CD_SETUP.md)

### Quick Start

```bash
# Configurer automatiquement
cd ../..
./setup_azure_credentials.sh
```

## Badges de Statut

Ajoutez ces badges à votre README.md:

```markdown
![Deploy Status](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/azure-function-deploy.yml/badge.svg)
![Test Status](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/azure-function-test.yml/badge.svg)
```

## Monitoring

Vérifiez les déploiements sur:
- https://github.com/YOUR_USERNAME/YOUR_REPO/actions

## Troubleshooting

### Le workflow ne se déclenche pas

**Vérifiez**:
1. Les workflows sont bien committés dans `.github/workflows/`
2. Vous avez push sur la branche `main`
3. Vous avez modifié des fichiers dans `azure_function/`

### Erreur "Authentication failed"

**Solution**:
```bash
# Régénérer et réajouter les credentials
./setup_azure_credentials.sh
```

### Le déploiement réussit mais la fonction ne fonctionne pas

**Checklist**:
1. ✅ Les modèles sont-ils uploadés sur Blob Storage?
2. ✅ La configuration `AzureWebJobsStorage` est-elle correcte?
3. ✅ Le `function.json` a-t-il `"dataType": "binary"` pour les blobs?

## Commandes Utiles

```bash
# Voir les runs récents
gh run list

# Voir les logs d'un run
gh run view <run-id> --log

# Relancer un workflow failed
gh run rerun <run-id>

# Déclencher manuellement un workflow
gh workflow run azure-function-deploy.yml
```
