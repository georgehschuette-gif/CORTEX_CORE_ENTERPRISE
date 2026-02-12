#!/bin/bash

# Cortex Core Enterprise Deployment Script

set -e

echo "🚀 Deploying Cortex Core Enterprise"
echo "==================================="

# Configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
DOCKER_IMAGE="${DOCKER_IMAGE:-cortex-core:latest}"
KUBERNETES_NAMESPACE="${KUBERNETES_NAMESPACE:-cortex-core}"

# Functions
check_prerequisites() {
    echo "📋 Checking deployment prerequisites..."

    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is required but not installed."
        exit 1
    fi

    if ! command -v kubectl &> /dev/null; then
        echo "❌ kubectl is required but not installed."
        exit 1
    fi

    echo "✅ Prerequisites check passed"
}

build_docker_image() {
    echo "🐳 Building Docker image..."
    docker build -t $DOCKER_IMAGE .

    echo "🏷️ Tagging image..."
    docker tag $DOCKER_IMAGE cortex-core:$ENVIRONMENT
}

deploy_to_kubernetes() {
    echo "☸️ Deploying to Kubernetes..."

    # Create namespace if it doesn't exist
    kubectl create namespace $KUBERNETES_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

    # Deploy ConfigMap
    kubectl apply -f deployment/kubernetes/configmap.yaml -n $KUBERNETES_NAMESPACE

    # Deploy secrets (you should create these separately for security)
    # kubectl apply -f deployment/kubernetes/secrets.yaml -n $KUBERNETES_NAMESPACE

    # Deploy the application
    kubectl apply -f deployment/kubernetes/deployment.yaml -n $KUBERNETES_NAMESPACE
    kubectl apply -f deployment/kubernetes/service.yaml -n $KUBERNETES_NAMESPACE
    kubectl apply -f deployment/kubernetes/ingress.yaml -n $KUBERNETES_NAMESPACE

    echo "⏳ Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/cortex-core -n $KUBERNETES_NAMESPACE

    echo "✅ Deployment completed successfully"
}

run_health_checks() {
    echo "🏥 Running health checks..."

    # Get service URL
    SERVICE_URL=$(kubectl get svc cortex-core-api -n $KUBERNETES_NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

    if [ -z "$SERVICE_URL" ]; then
        echo "⚠️ Could not get service URL, skipping health checks"
        return
    fi

    # Wait for service to be ready
    echo "Waiting for service to be ready..."
    sleep 30

    # Check health endpoint
    if curl -f http://$SERVICE_URL/health; then
        echo "✅ Health check passed"
    else
        echo "❌ Health check failed"
        exit 1
    fi

    # Check API documentation
    if curl -f http://$SERVICE_URL/docs; then
        echo "✅ API documentation accessible"
    else
        echo "⚠️ API documentation not accessible"
    fi
}

show_deployment_info() {
    echo ""
    echo "📊 Deployment Information"
    echo "========================"

    echo "Namespace: $KUBERNETES_NAMESPACE"
    echo "Environment: $ENVIRONMENT"
    echo ""

    echo "Pods:"
    kubectl get pods -n $KUBERNETES_NAMESPACE -l app=cortex-core
    echo ""

    echo "Services:"
    kubectl get services -n $KUBERNETES_NAMESPACE
    echo ""

    echo "Ingress:"
    kubectl get ingress -n $KUBERNETES_NAMESPACE
    echo ""

    SERVICE_IP=$(kubectl get svc cortex-core-api -n $KUBERNETES_NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ ! -z "$SERVICE_IP" ]; then
        echo "Service URL: http://$SERVICE_IP"
        echo "API Docs: http://$SERVICE_IP/docs"
        echo "Health Check: http://$SERVICE_IP/health"
        echo "Metrics: http://$SERVICE_IP/metrics"
    fi
}

# Main deployment flow
main() {
    check_prerequisites
    build_docker_image
    deploy_to_kubernetes
    run_health_checks
    show_deployment_info

    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "Monitor your deployment with:"
    echo "  kubectl logs -f deployment/cortex-core -n $KUBERNETES_NAMESPACE"
    echo "  kubectl get events -n $KUBERNETES_NAMESPACE"
}

# Parse command line arguments
case "${1:-}" in
    "check")
        check_prerequisites
        ;;
    "build")
        build_docker_image
        ;;
    "deploy")
        deploy_to_kubernetes
        ;;
    "health")
        run_health_checks
        ;;
    "info")
        show_deployment_info
        ;;
    *)
        main
        ;;
esac
