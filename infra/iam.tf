# Cuenta de servicio con la que corre Cloud Run: solo lo que la app necesita.
resource "google_service_account" "run" {
  account_id   = "pinapedia-run"
  display_name = "PinaPedia runtime (Cloud Run)"
  depends_on   = [google_project_service.this]
}

resource "google_project_iam_member" "run" {
  for_each = toset([
    "roles/aiplatform.user", # Gemini y embeddings
    "roles/datastore.user",  # Firestore
    "roles/logging.logWriter",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.run.email}"
}

# Cuenta de servicio que usa GitHub Actions (vía WIF) para desplegar.
resource "google_service_account" "deployer" {
  account_id   = "pinapedia-deployer"
  display_name = "PinaPedia deployer (GitHub Actions)"
  depends_on   = [google_project_service.this]
}

resource "google_project_iam_member" "deployer" {
  for_each = toset([
    "roles/run.developer",
    "roles/artifactregistry.writer",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

# El deployer puede asignar la SA de runtime al servicio, y nada más.
resource "google_service_account_iam_member" "deployer_acts_as_run" {
  service_account_id = google_service_account.run.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deployer.email}"
}
