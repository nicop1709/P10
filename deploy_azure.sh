#!/bin/bash

# Script de déploiement Azure étape par étape (généré en grande partie par Cursor AgentIA)
# Guide interactif pour déployer le système de recommandation sur Azure Functions

set -e  # Arrêter en cas d'erreur
# Couleurs pour l'affichage (Généré avec Cursor Agent)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
print_step() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Vérifier les prérequis
check_prerequisites() {
    print_step "VÉRIFICATION DES PRÉREQUIS"
    
    # Vérifier Azure CLI
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI n'est pas installé"
        echo "Installez-le avec: brew install azure-cli (sur macOS)"
        exit 1
    fi
    print_success "Azure CLI installé"
    
    # Vérifier Azure Functions Core Tools
    if ! command -v func &> /dev/null; then
        print_error "Azure Functions Core Tools n'est pas installé"
        echo "Installez-le avec: npm install -g azure-functions-core-tools@4 --unsafe-perm true"
        exit 1
    fi
    print_success "Azure Functions Core Tools installé"
    
    # Vérifier la connexion Azure
    if ! az account show &> /dev/null; then
        print_warning "Vous n'êtes pas connecté à Azure"
        echo "Connexion à Azure..."
        az login
    else
        print_success "Connecté à Azure"
        az account show --query "{Name:name, SubscriptionId:id}" -o table
        
        # Vérifier l'état de l'abonnement
        SUBSCRIPTION_STATE=$(az account show --query state -o tsv 2>/dev/null || echo "Unknown")
        if [ "$SUBSCRIPTION_STATE" = "Enabled" ]; then
            print_success "Abonnement actif (état: $SUBSCRIPTION_STATE)"
        else
            print_warning "Abonnement dans l'état: $SUBSCRIPTION_STATE"
            print_warning "L'abonnement doit être 'Enabled' pour créer des ressources"
            print_info "Consultez TROUBLESHOOTING_AZURE.md pour plus d'informations"
        fi
    fi
    
    # Vérifier les fichiers de modèle
    print_info "Vérification des fichiers de modèle..."
    REQUIRED_FILES=("als_model.pkl" "metadata.pkl" "csr_train.pkl")
    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "$file" ]; then
            size=$(du -h "$file" | cut -f1)
            print_success "$file existe ($size)"
        else
            print_error "$file manquant"
            echo "Exécutez d'abord: python serialize_artifacts.py"
            exit 1
        fi
    done
}

# Étape 1: Créer les ressources Azure
create_resources() {
    print_step "ÉTAPE 1: CRÉATION DES RESSOURCES AZURE"
    
    # Demander les informations
    echo ""
    read -p "Nom du Resource Group (défaut: rg-recommender): " RESOURCE_GROUP
    RESOURCE_GROUP=${RESOURCE_GROUP:-rg-recommender}
    
    read -p "Région Azure (défaut: westeurope): " LOCATION
    LOCATION=${LOCATION:-westeurope}
    
    # Générer des noms uniques avec timestamp
    TIMESTAMP=$(date +%s)
    STORAGE_ACCOUNT="strecommender${TIMESTAMP}"
    FUNCTION_APP="func-recommender-${TIMESTAMP}"
    
    print_info "Resource Group: $RESOURCE_GROUP"
    print_info "Région: $LOCATION"
    print_info "Storage Account: $STORAGE_ACCOUNT"
    print_info "Function App: $FUNCTION_APP"
    
    echo ""
    read -p "Continuer avec ces paramètres? (o/n): " confirm
    if [[ ! $confirm =~ ^[Oo]$ ]]; then
        print_warning "Opération annulée"
        exit 0
    fi
    
    # Vérifier et définir explicitement l'abonnement avant de créer des ressources
    print_info "Vérification de l'abonnement actif..."
    CURRENT_SUB_ID=$(az account show --query id -o tsv 2>/dev/null || echo "")
    if [ -z "$CURRENT_SUB_ID" ]; then
        print_error "Impossible de récupérer l'ID de l'abonnement"
        print_info "Essayez de vous reconnecter: az login"
        exit 1
    fi
    
    # Vérifier l'état de l'abonnement avant de continuer
    print_info "Vérification de l'état de l'abonnement..."
    SUBSCRIPTION_STATE=$(az account show --query state -o tsv 2>/dev/null || echo "Unknown")
    if [ "$SUBSCRIPTION_STATE" != "Enabled" ]; then
        print_error "L'abonnement n'est pas dans l'état 'Enabled' (état actuel: $SUBSCRIPTION_STATE)"
        print_warning "L'abonnement doit être activé pour créer des ressources"
        echo ""
        print_info "Solutions possibles:"
        echo "  1. Vérifiez l'état dans le Portail Azure: https://portal.azure.com"
        echo "  2. Réactivez l'abonnement si nécessaire"
        echo "  3. Créez un nouveau compte Azure gratuit: https://azure.microsoft.com/free/"
        echo "  4. Consultez TROUBLESHOOTING_AZURE.md pour plus de détails"
        echo ""
        read -p "Voulez-vous continuer quand même? (o/n): " continue_anyway
        if [[ ! $continue_anyway =~ ^[Oo]$ ]]; then
            print_warning "Opération annulée"
            exit 1
        fi
    else
        print_success "Abonnement actif (état: $SUBSCRIPTION_STATE)"
    fi
    
    # S'assurer que l'abonnement est bien défini avant de créer des ressources
    # Utiliser l'ID plutôt que le nom pour plus de fiabilité
    print_info "Définition explicite de l'abonnement (par ID)..."
    if ! az account set --subscription "$CURRENT_SUB_ID" &> /dev/null; then
        print_warning "Impossible de définir l'abonnement par ID, tentative par nom..."
        SUBSCRIPTION_NAME=$(az account show --query name -o tsv 2>/dev/null || echo "")
        if [ -n "$SUBSCRIPTION_NAME" ]; then
            az account set --subscription "$SUBSCRIPTION_NAME" &> /dev/null || true
        fi
    fi
    
    # Vérifier que l'abonnement est bien défini
    VERIFIED_SUB_ID=$(az account show --query id -o tsv 2>/dev/null || echo "")
    if [ "$VERIFIED_SUB_ID" != "$CURRENT_SUB_ID" ]; then
        print_warning "L'abonnement défini ne correspond pas à celui attendu"
        print_info "Exécutez: ./fix_subscription_notfound.sh pour corriger ce problème"
    fi
    
    # Vérifier que le Resource Group existe et est dans le bon abonnement
    print_info "Vérification du Resource Group..."
    if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
        print_warning "Resource Group existe déjà"
        # Vérifier que le RG est dans le bon abonnement
        RG_SUB_ID=$(az group show --name "$RESOURCE_GROUP" --query id -o tsv 2>/dev/null | cut -d'/' -f3 || echo "")
        if [ -n "$RG_SUB_ID" ] && [ "$RG_SUB_ID" != "$CURRENT_SUB_ID" ]; then
            print_error "Le Resource Group a été créé avec un autre abonnement!"
            print_info "Resource Group Subscription: $RG_SUB_ID"
            print_info "Abonnement actuel: $CURRENT_SUB_ID"
            echo ""
            print_warning "Solutions:"
            echo "  1. Supprimer le Resource Group: az group delete --name $RESOURCE_GROUP --yes"
            echo "  2. Changer d'abonnement: az account set --subscription $RG_SUB_ID"
            echo "  3. Exécuter le script de correction: ./fix_subscription_issue.sh"
            exit 1
        fi
    else
        # Créer le Resource Group
        print_info "Création du Resource Group..."
        az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
        print_success "Resource Group créé"
    fi
    
    # Créer le Storage Account
    print_info "Création du Storage Account..."
    if az storage account show --name "$STORAGE_ACCOUNT" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        print_warning "Storage Account existe déjà"
    else
        print_info "Création en cours (cela peut prendre 1-2 minutes)..."
        print_info "Veuillez patienter, cette opération peut prendre du temps..."
        
        # Créer le Storage Account avec affichage en temps réel
        if az storage account create \
            --name "$STORAGE_ACCOUNT" \
            --resource-group "$RESOURCE_GROUP" \
            --location "$LOCATION" \
            --sku Standard_LRS 2>&1 | tee /tmp/storage_create.log; then
            CREATE_EXIT_CODE=0
        else
            CREATE_EXIT_CODE=$?
            CREATE_OUTPUT=$(cat /tmp/storage_create.log 2>/dev/null || echo "")
        fi
        
        if [ $CREATE_EXIT_CODE -eq 0 ]; then
            # Vérifier que le Storage Account existe vraiment
            print_info "Vérification que le Storage Account a été créé..."
            sleep 5  # Attendre un peu pour que la création soit propagée
            
            RETRY_COUNT=0
            MAX_RETRIES=18  # Augmenté à 18 (3 minutes max)
            print_info "Vérification que le Storage Account est disponible..."
            
            while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
                if az storage account show --name "$STORAGE_ACCOUNT" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
                    print_success "Storage Account créé et vérifié"
                    break
                else
                    RETRY_COUNT=$((RETRY_COUNT + 1))
                    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                        # Afficher une progression avec des points
                        DOTS=$(printf '.%.0s' $(seq 1 $((RETRY_COUNT % 4))))
                        printf "\r${BLUE}ℹ️  Attente de la création du Storage Account... ($RETRY_COUNT/$MAX_RETRIES)${DOTS}   ${NC}"
                        sleep 10
                    else
                        echo ""  # Nouvelle ligne après la progression
                        print_error "Le Storage Account n'a pas été créé après plusieurs tentatives"
                        print_info "Vérifiez manuellement:"
                        echo "  az storage account show --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP"
                        echo "  az storage account list --resource-group $RESOURCE_GROUP --output table"
                        exit 1
                    fi
                fi
            done
            echo ""  # Nouvelle ligne après la progression
        else
            ERROR_MSG=$(cat /tmp/storage_create.log 2>/dev/null || echo "$CREATE_OUTPUT")
            rm -f /tmp/storage_create.log
            
            if echo "$ERROR_MSG" | grep -q "SubscriptionNotFound"; then
                print_error "Erreur: Abonnement non trouvé ou non accessible"
                echo ""
                print_warning "Votre abonnement apparaît dans la liste mais n'est pas accessible."
                echo ""
                print_info "Causes possibles:"
                echo "  - Abonnement désactivé ou expiré"
                echo "  - Abonnement en état 'Warned' ou 'Disabled'"
                echo "  - Problème de permissions"
                echo "  - Mismatch entre l'abonnement du Resource Group et l'abonnement actuel"
                echo ""
                print_info "Solutions:"
                echo "  1. Exécutez le script de correction spécifique: ./fix_subscription_notfound.sh"
                echo "  2. Ou le script de correction général: ./fix_subscription_issue.sh"
                echo "  3. Vérifiez l'état dans le Portail Azure: https://portal.azure.com"
                echo "  4. Vérifiez l'état avec: az account show --query state -o tsv"
                echo "  5. Essayez de définir l'abonnement par ID: az account set --subscription <ID>"
                echo "  6. Consultez RESOLUTION_RAPIDE.md pour une solution rapide"
                echo "  7. Consultez TROUBLESHOOTING_AZURE.md pour plus de détails"
                echo "  8. Créez un nouveau compte Azure gratuit si nécessaire"
                exit 1
            elif echo "$ERROR_MSG" | grep -q "already exists"; then
                print_warning "Le Storage Account existe peut-être déjà avec un autre nom"
                print_info "Vérification..."
                if az storage account show --name "$STORAGE_ACCOUNT" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
                    print_success "Storage Account trouvé"
                else
                    print_error "Le Storage Account n'existe pas. Erreur:"
                    echo "$ERROR_MSG"
                    exit 1
                fi
            else
                print_error "Erreur lors de la création du Storage Account"
                echo "$ERROR_MSG"
                echo ""
                print_info "Vérifiez:"
                echo "  - Que le nom du Storage Account est unique (doit être globalement unique)"
                echo "  - Que vous avez les permissions nécessaires"
                echo "  - Les quotas de votre abonnement"
                exit 1
            fi
        fi
    fi
    
    # Créer le conteneur pour les modèles
    print_info "Création du conteneur 'models'..."
    
    # Vérifier d'abord que le Storage Account existe
    if ! az storage account show --name "$STORAGE_ACCOUNT" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        print_error "Le Storage Account '$STORAGE_ACCOUNT' n'existe pas dans le Resource Group '$RESOURCE_GROUP'"
        print_info "Vérifiez les ressources existantes:"
        echo "  az storage account list --resource-group $RESOURCE_GROUP --output table"
        exit 1
    fi
    
    # Récupérer la clé du Storage Account
    print_info "Récupération de la clé du Storage Account..."
    STORAGE_KEY=$(az storage account keys list \
        --resource-group "$RESOURCE_GROUP" \
        --account-name "$STORAGE_ACCOUNT" \
        --query "[0].value" -o tsv 2>/dev/null)
    
    if [ -z "$STORAGE_KEY" ]; then
        print_error "Impossible de récupérer la clé du Storage Account"
        print_info "Vérifiez vos permissions:"
        echo "  az role assignment list --assignee \$(az account show --query user.name -o tsv) --output table"
        exit 1
    fi
    
    # Vérifier si le conteneur existe déjà
    if az storage container show --name models --account-name "$STORAGE_ACCOUNT" --account-key "$STORAGE_KEY" &> /dev/null; then
        print_warning "Conteneur 'models' existe déjà"
    else
        print_info "Création du conteneur..."
        if az storage container create \
            --name models \
            --account-name "$STORAGE_ACCOUNT" \
            --account-key "$STORAGE_KEY" 2>&1; then
            print_success "Conteneur 'models' créé"
        else
            print_error "Erreur lors de la création du conteneur"
            print_info "Vérifiez que le Storage Account est accessible"
            exit 1
        fi
    fi
    
    # Créer la Function App
    print_info "Création de la Function App..."
    if az functionapp show --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        print_warning "Function App existe déjà"
    else
        print_info "Python nécessite Linux pour les Azure Functions, création sur Linux..."
        print_info "Utilisation de Python 3.11 (3.9 n'est plus supporté)..."
        
        # Essayer avec Python 3.11 d'abord, puis 3.12, puis 3.10
        PYTHON_VERSIONS=("3.11" "3.12" "3.10")
        FUNCTION_CREATED=false
        
        for PYTHON_VERSION in "${PYTHON_VERSIONS[@]}"; do
            print_info "Tentative avec Python $PYTHON_VERSION..."
            
            if az functionapp create \
                --resource-group "$RESOURCE_GROUP" \
                --consumption-plan-location "$LOCATION" \
                --runtime python \
                --runtime-version "$PYTHON_VERSION" \
                --functions-version 4 \
                --name "$FUNCTION_APP" \
                --storage-account "$STORAGE_ACCOUNT" \
                --os-type Linux 2>&1 | tee /tmp/functionapp_create.log; then
                CREATE_FUNC_EXIT_CODE=0
            else
                CREATE_FUNC_EXIT_CODE=$?
            fi
            
            ERROR_MSG=$(cat /tmp/functionapp_create.log 2>/dev/null || echo "")
            
            # Vérifier si l'erreur concerne la version Python
            if echo "$ERROR_MSG" | grep -qi "end-of-life\|no longer supported\|version.*not.*supported"; then
                print_warning "Python $PYTHON_VERSION n'est pas supporté, essai avec une autre version..."
                continue
            fi
            
            # Vérifier que la Function App a bien été créée
            if [ $CREATE_FUNC_EXIT_CODE -eq 0 ]; then
                # Attendre un peu pour que la création soit propagée
                sleep 5
                
                # Vérifier que la Function App existe vraiment
                if az functionapp show --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
                    print_success "Function App créée avec Python $PYTHON_VERSION"
                    FUNCTION_CREATED=true
                    rm -f /tmp/functionapp_create.log
                    break
                else
                    print_warning "Function App créée mais pas encore disponible, attente..."
                    sleep 10
                    if az functionapp show --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
                        print_success "Function App créée avec Python $PYTHON_VERSION"
                        FUNCTION_CREATED=true
                        rm -f /tmp/functionapp_create.log
                        break
                    else
                        print_warning "Function App toujours non disponible, essai avec une autre version..."
                        continue
                    fi
                fi
            else
                if echo "$ERROR_MSG" | grep -q "Runtime python not supported for os windows"; then
                    print_error "Erreur: Python n'est pas supporté sur Windows"
                    print_info "Vérifiez que --os-type Linux est bien spécifié"
                else
                    print_warning "Erreur avec Python $PYTHON_VERSION: $ERROR_MSG"
                    print_info "Essai avec une autre version..."
                fi
                continue
            fi
        done
        
        if [ "$FUNCTION_CREATED" = false ]; then
            print_error "Impossible de créer la Function App avec les versions Python disponibles"
            print_info "Vérifiez les runtimes disponibles:"
            echo "  az functionapp list-runtimes --os-type Linux --query \"[?contains(name, 'python')]\" -o table"
            rm -f /tmp/functionapp_create.log
            exit 1
        fi
    fi
    
    # Vérification finale que la Function App existe
    if ! az functionapp show --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        print_error "La Function App n'existe pas après la création"
        print_info "Vérifiez manuellement:"
        echo "  az functionapp show --name $FUNCTION_APP --resource-group $RESOURCE_GROUP"
        exit 1
    fi
    
    # Sauvegarder les variables pour les étapes suivantes
    echo "$RESOURCE_GROUP" > .azure_deploy_vars
    echo "$LOCATION" >> .azure_deploy_vars
    echo "$STORAGE_ACCOUNT" >> .azure_deploy_vars
    echo "$FUNCTION_APP" >> .azure_deploy_vars
    echo "$STORAGE_KEY" >> .azure_deploy_vars
    
    print_success "Étape 1 terminée!"
}

# Étape 2: Uploader les artefacts
upload_artifacts() {
    print_step "ÉTAPE 2: UPLOAD DES ARTEFACTS VERS BLOB STORAGE"
    
    if [ ! -f .azure_deploy_vars ]; then
        print_error "Variables de déploiement non trouvées. Exécutez d'abord l'étape 1."
        exit 1
    fi
    
    # Charger les variables
    RESOURCE_GROUP=$(sed -n '1p' .azure_deploy_vars)
    STORAGE_ACCOUNT=$(sed -n '3p' .azure_deploy_vars)
    STORAGE_KEY=$(sed -n '5p' .azure_deploy_vars)
    
    print_info "Upload des fichiers vers le conteneur 'models'..."
    
    # Uploader chaque fichier
    FILES=("als_model.pkl" "metadata.pkl" "csr_train.pkl")
    for file in "${FILES[@]}"; do
        if [ -f "$file" ]; then
            print_info "Upload de $file..."
            az storage blob upload \
                --container-name models \
                --name "$file" \
                --file "$file" \
                --account-name "$STORAGE_ACCOUNT" \
                --account-key "$STORAGE_KEY" \
                --overwrite
            print_success "$file uploadé"
        else
            print_error "$file non trouvé"
        fi
    done
    
    print_success "Étape 2 terminée!"
}

# Étape 3: Configurer la connexion Azure Storage
configure_storage() {
    print_step "ÉTAPE 3: CONFIGURATION DE LA CONNEXION AZURE STORAGE"
    
    if [ ! -f .azure_deploy_vars ]; then
        print_error "Variables de déploiement non trouvées."
        exit 1
    fi
    
    RESOURCE_GROUP=$(sed -n '1p' .azure_deploy_vars)
    STORAGE_ACCOUNT=$(sed -n '3p' .azure_deploy_vars)
    FUNCTION_APP=$(sed -n '4p' .azure_deploy_vars)
    
    print_info "Récupération de la chaîne de connexion..."
    CONNECTION_STRING=$(az storage account show-connection-string \
        --name "$STORAGE_ACCOUNT" \
        --resource-group "$RESOURCE_GROUP" \
        --query connectionString -o tsv)
    
    # Vérifier que la Function App existe avant de configurer
    print_info "Vérification que la Function App existe..."
    if ! az functionapp show --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        print_error "La Function App '$FUNCTION_APP' n'existe pas dans le Resource Group '$RESOURCE_GROUP'"
        print_info "Vérifiez les ressources existantes:"
        echo "  az functionapp list --resource-group $RESOURCE_GROUP --output table"
        print_info "Ou créez-la d'abord avec l'option 2 (Étape 1: Créer les ressources Azure)"
        exit 1
    fi
    
    print_info "Configuration de AzureWebJobsStorage..."
    if az functionapp config appsettings set \
        --name "$FUNCTION_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --settings "AzureWebJobsStorage=$CONNECTION_STRING" 2>&1; then
        print_success "Configuration AzureWebJobsStorage réussie"
    else
        print_error "Erreur lors de la configuration de AzureWebJobsStorage"
        exit 1
    fi
    
    print_success "Étape 3 terminée!"
}

# Étape 4: Déployer la fonction
deploy_function() {
    print_step "ÉTAPE 4: DÉPLOIEMENT DE LA FONCTION"
    
    if [ ! -f .azure_deploy_vars ]; then
        print_error "Variables de déploiement non trouvées."
        exit 1
    fi
    
    FUNCTION_APP=$(sed -n '4p' .azure_deploy_vars)
    
    # Vérifier que nous sommes dans le bon répertoire
    if [ ! -d "azure_function" ]; then
        print_error "Le dossier azure_function n'existe pas"
        exit 1
    fi
    
    print_info "Préparation du déploiement..."
    cd azure_function
    
    # Vérifier les dépendances
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt non trouvé"
        exit 1
    fi
    
    print_info "Déploiement vers $FUNCTION_APP..."
    func azure functionapp publish "$FUNCTION_APP"
    
    cd ..
    
    print_success "Étape 4 terminée!"
}

# Étape 5: Tester le déploiement
test_deployment() {
    print_step "ÉTAPE 5: TEST DU DÉPLOIEMENT"
    
    if [ ! -f .azure_deploy_vars ]; then
        print_error "Variables de déploiement non trouvées."
        exit 1
    fi
    
    FUNCTION_APP=$(sed -n '4p' .azure_deploy_vars)
    RESOURCE_GROUP=$(sed -n '1p' .azure_deploy_vars)
    
    print_info "Récupération de l'URL de la fonction..."
    
    # Attendre un peu pour que le déploiement soit terminé
    sleep 5
    
    FUNCTION_URL=$(az functionapp function show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP" \
        --function-name RecommendArticle \
        --query invokeUrlTemplate -o tsv 2>/dev/null || echo "")
    
    if [ -z "$FUNCTION_URL" ]; then
        print_warning "Impossible de récupérer l'URL automatiquement"
        FUNCTION_URL="https://${FUNCTION_APP}.azurewebsites.net/api/RecommendArticle"
        print_info "URL probable: $FUNCTION_URL"
    else
        print_success "URL récupérée: $FUNCTION_URL"
    fi
    
    echo ""
    print_info "Test de la fonction avec user_id=0..."
    echo ""
    
    # Note: L'authLevel est "function", donc il faut une clé
    print_warning "Note: L'authentification est activée (authLevel: function)"
    print_info "Pour obtenir la clé de fonction:"
    echo "  az functionapp function keys list --name $FUNCTION_APP --resource-group $RESOURCE_GROUP --function-name RecommendArticle"
    echo ""
    print_info "Pour tester avec curl:"
    echo "  curl \"$FUNCTION_URL?code=<FUNCTION_KEY>&user_id=0\""
    
    print_success "Étape 5 terminée!"
}

# Afficher le résumé
show_summary() {
    print_step "RÉSUMÉ DU DÉPLOIEMENT"
    
    if [ ! -f .azure_deploy_vars ]; then
        print_error "Variables de déploiement non trouvées."
        return
    fi
    
    RESOURCE_GROUP=$(sed -n '1p' .azure_deploy_vars)
    STORAGE_ACCOUNT=$(sed -n '3p' .azure_deploy_vars)
    FUNCTION_APP=$(sed -n '4p' .azure_deploy_vars)
    
    echo ""
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Storage Account: $STORAGE_ACCOUNT"
    echo "Function App: $FUNCTION_APP"
    echo "URL: https://${FUNCTION_APP}.azurewebsites.net/api/RecommendArticle"
    echo ""
    
    print_info "Pour obtenir la clé de fonction:"
    echo "  az functionapp function keys list --name $FUNCTION_APP --resource-group $RESOURCE_GROUP --function-name RecommendArticle"
    echo ""
    print_info "Pour voir les logs:"
    echo "  func azure functionapp logstream $FUNCTION_APP"
    echo ""
    print_info "Pour redémarrer la Function App:"
    echo "  az functionapp restart --name $FUNCTION_APP --resource-group $RESOURCE_GROUP"
}

# Menu principal
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  Guide de Déploiement Azure Functions - Recommandation   ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Vérifier les prérequis
    check_prerequisites
    
    echo ""
    echo "Choisissez une option:"
    echo "1) Déploiement complet (toutes les étapes)"
    echo "2) Étape 1: Créer les ressources Azure"
    echo "3) Étape 2: Uploader les artefacts"
    echo "4) Étape 3: Configurer la connexion Storage"
    echo "5) Étape 4: Déployer la fonction"
    echo "6) Étape 5: Tester le déploiement"
    echo "7) Afficher le résumé"
    echo "0) Quitter"
    echo ""
    read -p "Votre choix: " choice
    
    case $choice in
        1)
            create_resources
            upload_artifacts
            configure_storage
            deploy_function
            test_deployment
            show_summary
            ;;
        2)
            create_resources
            ;;
        3)
            upload_artifacts
            ;;
        4)
            configure_storage
            ;;
        5)
            deploy_function
            ;;
        6)
            test_deployment
            ;;
        7)
            show_summary
            ;;
        0)
            print_info "Au revoir!"
            exit 0
            ;;
        *)
            print_error "Choix invalide"
            exit 1
            ;;
    esac
}

# Exécuter le script
main

