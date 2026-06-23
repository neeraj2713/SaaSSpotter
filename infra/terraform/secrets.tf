resource "aws_secretsmanager_secret" "app" {
  name        = "${local.name_prefix}/app-secrets"
  description = "PainPoint.io application secrets"
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    MONGODB_URI                      = var.mongodb_uri
    MONGODB_DB_NAME                  = "dev"
    GEMINI_API_KEY                   = var.gemini_api_key
    GEMINI_MODEL                     = "gemini-2.0-flash"
    FIRECRAWL_API_KEY                = var.firecrawl_api_key
    CORS_ORIGINS                     = var.cors_origins
    ADMIN_API_KEY                    = var.admin_api_key
    STEP_FUNCTIONS_STATE_MACHINE_ARN = "arn:aws:states:${var.aws_region}:${data.aws_caller_identity.current.account_id}:stateMachine:${var.project_name}-${var.environment}-pipeline"
  })
}
