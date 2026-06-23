variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project name prefix for resources"
  type        = string
  default     = "painpoint"
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
  default     = "dev"
}

variable "mongodb_uri" {
  description = "MongoDB Atlas connection string"
  type        = string
  sensitive   = true
}

variable "gemini_api_key" {
  description = "Google Gemini API key"
  type        = string
  sensitive   = true
}

variable "firecrawl_api_key" {
  description = "Firecrawl API key"
  type        = string
  sensitive   = true
}

variable "admin_api_key" {
  description = "Optional admin API key for trigger-scrape endpoint"
  type        = string
  sensitive   = true
  default     = ""
}

variable "cors_origins" {
  description = "Comma-separated CORS origins"
  type        = string
  default     = "http://localhost:3000"
}

variable "clerk_issuer" {
  description = "Clerk JWT issuer URL (e.g. https://your-app.clerk.accounts.dev)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "lambda_zip_path" {
  description = "Path to the Lambda deployment package zip"
  type        = string
  default     = "../../build/api.zip"
}

variable "lambda_layer_zip_path" {
  description = "Path to the Lambda layer zip"
  type        = string
  default     = "../../build/layer.zip"
}
