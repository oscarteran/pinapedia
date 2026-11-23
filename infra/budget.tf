data "google_project" "this" {}

# Las alertas llegan por correo a los administradores de la cuenta de facturación.
# La moneda es la de tu cuenta de facturación (no se especifica aquí).
resource "google_billing_budget" "mensual" {
  billing_account = var.billing_account
  display_name    = "pinapedia-mensual"

  budget_filter {
    projects = ["projects/${data.google_project.this.number}"]
  }

  amount {
    specified_amount {
      units = tostring(var.budget_amount)
    }
  }

  threshold_rules {
    threshold_percent = 0.5
  }
  threshold_rules {
    threshold_percent = 0.9
  }
  threshold_rules {
    threshold_percent = 1.0
  }

  depends_on = [google_project_service.this]
}
