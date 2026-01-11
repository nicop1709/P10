#!/bin/bash

# Script spécifique pour corriger l'erreur SubscriptionNotFound
# quand l'abonnement apparaît dans la liste mais n'est pas accessible

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

print_step "CORRECTION - SubscriptionNotFound"

# Vérifier la connexion
print_info "Vérification de la connexion Azure..."
if ! az account show &> /dev/null; then
    print_warning "Vous n'êtes pas connecté à Azure"
    print_info "Connexion à Azure..."
    az login
fi

# Afficher l'abonnement actuel
print_step "ABONNEMENT ACTUEL"
CURRENT_SUB=$(az account show --query "{Name:name, State:state, SubscriptionId:id, TenantId:tenantId}" -o table 2>/dev/null || echo "")
if [ -z "$CURRENT_SUB" ]; then
    print_error "Impossible de récupérer les informations de l'abonnement"
    exit 1
fi
echo "$CURRENT_SUB"

SUBSCRIPTION_ID=$(az account show --query id -o tsv 2>/dev/null || echo "")
SUBSCRIPTION_NAME=$(az account show --query name -o tsv 2>/dev/null || echo "")

# Solution 1: Utiliser l'ID d'abonnement au lieu du nom
print_step "SOLUTION 1: Définir l'abonnement par ID"
print_info "Définition de l'abonnement avec l'ID: $SUBSCRIPTION_ID"
az account set --subscription "$SUBSCRIPTION_ID"
print_success "Abonnement défini par ID"

# Vérifier que ça fonctionne
print_info "Vérification..."
VERIFIED_SUB=$(az account show --query id -o tsv 2>/dev/null || echo "")
if [ "$VERIFIED_SUB" = "$SUBSCRIPTION_ID" ]; then
    print_success "Abonnement correctement défini"
else
    print_error "Problème lors de la définition de l'abonnement"
fi

# Solution 2: Vérifier le Resource Group
print_step "VÉRIFICATION DU RESOURCE GROUP"
RESOURCE_GROUP="rg-recommender"

if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "Resource Group '$RESOURCE_GROUP' existe déjà"
    
    # Récupérer l'ID complet du Resource Group
    RG_ID=$(az group show --name "$RESOURCE_GROUP" --query id -o tsv 2>/dev/null || echo "")
    if [ -n "$RG_ID" ]; then
        # Extraire l'ID d'abonnement du Resource Group
        RG_SUB_ID=$(echo "$RG_ID" | cut -d'/' -f3)
        print_info "Resource Group Subscription ID: $RG_SUB_ID"
        print_info "Abonnement actuel ID: $SUBSCRIPTION_ID"
        
        if [ "$RG_SUB_ID" != "$SUBSCRIPTION_ID" ]; then
            print_error "MISMATCH D'ABONNEMENT DÉTECTÉ!"
            echo ""
            print_warning "Le Resource Group a été créé avec un autre abonnement"
            echo ""
            print_info "Options:"
            echo "  1. Supprimer le Resource Group et recommencer"
            echo "  2. Changer d'abonnement pour correspondre au Resource Group"
            echo ""
            read -p "Voulez-vous supprimer le Resource Group et recommencer? (o/n): " delete_rg
            if [[ $delete_rg =~ ^[Oo]$ ]]; then
                print_info "Suppression du Resource Group..."
                az group delete --name "$RESOURCE_GROUP" --yes --no-wait
                print_success "Resource Group en cours de suppression"
                print_info "Attendez 30-60 secondes avant de relancer le déploiement"
                print_info "Puis exécutez: ./deploy_azure.sh"
                exit 0
            else
                print_info "Changement d'abonnement pour correspondre au Resource Group..."
                az account set --subscription "$RG_SUB_ID"
                print_success "Abonnement changé"
                print_info "Vérifiez l'état: az account show --query state -o tsv"
            fi
        else
            print_success "Le Resource Group est dans le bon abonnement"
        fi
    fi
else
    print_info "Resource Group '$RESOURCE_GROUP' n'existe pas (c'est normal si c'est un nouveau déploiement)"
fi

# Solution 3: Nettoyer le cache Azure CLI
print_step "SOLUTION 3: Nettoyer le cache Azure CLI"
print_info "Parfois le cache Azure CLI peut causer des problèmes"
print_warning "Cette opération va vous déconnecter d'Azure"
echo ""
read -p "Voulez-vous nettoyer le cache et vous reconnecter? (o/n): " clear_cache
if [[ $clear_cache =~ ^[Oo]$ ]]; then
    print_info "Déconnexion d'Azure..."
    az logout 2>/dev/null || true
    print_info "Nettoyage du cache..."
    rm -rf ~/.azure/accessTokens.json 2>/dev/null || true
    rm -rf ~/.azure/azureProfile.json 2>/dev/null || true
    print_info "Reconnexion à Azure..."
    az login
    print_success "Reconnecté à Azure"
    
    # Redéfinir l'abonnement
    if [ -n "$SUBSCRIPTION_ID" ]; then
        print_info "Redéfinition de l'abonnement..."
        az account set --subscription "$SUBSCRIPTION_ID"
        print_success "Abonnement redéfini"
    fi
fi

# Solution 4: Test de création
print_step "TEST DE CRÉATION"
print_info "Test de création d'un groupe de ressources de test..."
TEST_RG="rg-test-subscription-$(date +%s)"

if az group create --name "$TEST_RG" --location "westeurope" &> /dev/null; then
    print_success "✅ Test réussi: création de ressource possible"
    print_info "Suppression du groupe de test..."
    az group delete --name "$TEST_RG" --yes --no-wait &> /dev/null
    print_success "Le problème semble résolu!"
    echo ""
    print_info "Vous pouvez maintenant relancer le déploiement:"
    echo "  ./deploy_azure.sh"
else
    print_error "❌ Test échoué: impossible de créer une ressource"
    echo ""
    print_warning "Le problème persiste. Solutions supplémentaires:"
    echo ""
    print_info "1. Vérifiez dans le Portail Azure:"
    echo "   https://portal.azure.com/#blade/Microsoft_Azure_Billing/SubscriptionsBlade"
    echo ""
    print_info "2. Vérifiez les quotas de votre abonnement"
    echo ""
    print_info "3. Créez un nouveau compte Azure gratuit si nécessaire:"
    echo "   https://azure.microsoft.com/free/"
    echo ""
    print_info "4. Consultez TROUBLESHOOTING_AZURE.md pour plus de détails"
    exit 1
fi

# Résumé
print_step "RÉSUMÉ"
print_success "Correction terminée"
echo ""
print_info "Abonnement actuel:"
az account show --query "{Name:name, SubscriptionId:id, State:state}" -o table
echo ""
print_info "Prochaines étapes:"
echo "  1. Relancez le déploiement: ./deploy_azure.sh"
echo "  2. Si le problème persiste, consultez TROUBLESHOOTING_AZURE.md"
echo ""

