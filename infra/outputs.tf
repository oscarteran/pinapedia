output "run_service_account" {
  value = google_service_account.run.email
}

output "deployer_service_account" {
  value = google_service_account.deployer.email
}

output "wif_provider" {
  description = "Va en el workflow de GitHub Actions (workload_identity_provider)."
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "image_repo" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}"
}
