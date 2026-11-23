# La base y el índice ya existen (los creaste con gcloud): se importan al estado.

import {
  to = google_firestore_database.default
  id = "projects/${var.project_id}/databases/(default)"
}

resource "google_firestore_database" "default" {
  name        = "(default)"
  location_id = var.firestore_location
  type        = "FIRESTORE_NATIVE"

  # Si alguien borra el recurso de Terraform, la base y sus datos se quedan.
  deletion_policy = "ABANDON"
}


resource "google_firestore_index" "chunks_embedding" {
  database    = google_firestore_database.default.name
  collection  = "chunks"
  query_scope = "COLLECTION"

  fields {
    field_path = "embedding"
    vector_config {
      dimension = 768
      flat {}
    }
  }

  # La API agrega campos implícitos (__name__) al índice creado con gcloud;
  # sin esto Terraform querría reemplazarlo en cada plan.
  lifecycle {
    ignore_changes = [fields]
  }
}