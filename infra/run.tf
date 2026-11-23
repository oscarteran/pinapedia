# Servicio de Cloud Run.
# Terraform administra la configuración; GitHub Actions solo cambia la imagen.

resource "google_cloud_run_v2_service" "pinapedia" {
  name                = "pinapedia"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account                  = google_service_account.run.email
    max_instance_request_concurrency = 10
    timeout                          = "120s"

    scaling {
      min_instance_count = 0 # escala a cero: sin tráfico, sin costo
      max_instance_count = 1 # tope duro de cómputo; el rate limit vive en memoria
    }

    containers {
      # Imagen pública de ejemplo de Google solo para crear el servicio;
      # el primer deploy de GitHub Actions la reemplaza (ver lifecycle).
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
        cpu_idle          = true # solo cobra CPU mientras atiende peticiones
        startup_cpu_boost = true
      }

      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "TRUE"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.model_location
      }
      env {
        name  = "PINAPEDIA_MODEL"
        value = var.model
      }
      env {
        name  = "EMBED_LOCATION"
        value = var.region
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image, # la cambia GitHub Actions en cada deploy
      client,
      client_version,
    ]
  }

  depends_on = [google_project_service.this]
}

# Demo pública: cualquiera puede invocar el servicio (el guard limita el uso).
resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.pinapedia.name
  location = google_cloud_run_v2_service.pinapedia.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "service_url" {
  value = google_cloud_run_v2_service.pinapedia.uri
}