terraform {
  required_version = ">= 1.10.0, < 2.0.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.38.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "2.17.0"
    }
  }
  # No explicit backend: local by default. See IMPORT.md before adoption.
}
