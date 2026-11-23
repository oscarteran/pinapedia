variable "project_id" {
  description = "ID del proyecto de GCP."
  type        = string
}

variable "region" {
  description = "Región de Cloud Run y Artifact Registry."
  type        = string
  default     = "us-central1"
}

variable "github_repo" {
  description = "Repositorio autorizado para desplegar vía WIF, formato owner/repo."
  type        = string
  default     = "oscarhdzteran/pinapedia-adk"
}

variable "firestore_location" {
  description = "Ubicación de la base (default) de Firestore; debe coincidir con la que ya creaste."
  type        = string
  default     = "nam5"
}

variable "firestore_index_id" {
  description = "ID del índice vectorial creado con gcloud (último segmento de su name)."
  type        = string
}

variable "billing_account" {
  description = "ID de la cuenta de facturación, formato XXXXXX-XXXXXX-XXXXXX."
  type        = string
}

variable "budget_amount" {
  description = "Presupuesto mensual en la moneda de tu cuenta de facturación (5 si es USD, ~100 si es MXN)."
  type        = number
  default     = 5
}

variable "model" {
  description = "Modelo de Gemini para los agentes."
  type        = string
  default     = "gemini-3.5-flash-lite"
}

variable "model_location" {
  description = "Ubicación del endpoint de Gemini (us-central1 o global, la que te funcionó en local)."
  type        = string
  default     = "us-central1"
}
