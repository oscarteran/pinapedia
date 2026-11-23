resource "google_artifact_registry_repository" "docker" {
  location      = var.region
  repository_id = "pinapedia"
  format        = "DOCKER"
  description   = "Imágenes de PiñaPedia"

  cleanup_policy_dry_run = false

  # Conserva siempre las 3 versiones más recientes...
  cleanup_policies {
    id     = "conservar-3-recientes"
    action = "KEEP"
    most_recent_versions {
      keep_count = 3
    }
  }

  # ...y borra el resto cuando tenga más de 7 días.
  cleanup_policies {
    id     = "borrar-antiguas"
    action = "DELETE"
    condition {
      older_than = "604800s"
    }
  }

  depends_on = [google_project_service.this]
}
