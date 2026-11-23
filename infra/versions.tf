terraform {
  required_version = ">= 1.6"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0"
    }
  }

  # El bucket se pasa al iniciar:
  #   terraform init -backend-config="bucket=<project_id>-tfstate"
  backend "gcs" {
    prefix = "pinapedia"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region

  # Necesario para la API de presupuestos con credenciales de usuario (ADC).
  billing_project       = var.project_id
  user_project_override = true
}
