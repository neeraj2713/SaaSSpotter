variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
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

variable "reddit_client_id" {
  description = "Reddit API client ID"
  type        = string
  sensitive   = true
}

variable "reddit_client_secret" {
  description = "Reddit API client secret"
  type        = string
  sensitive   = true
}

variable "reddit_user_agent" {
  description = "Reddit API user agent"
  type        = string
  default     = "PainPoint.io/1.0"
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
