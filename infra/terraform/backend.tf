terraform {
  backend "s3" {
    bucket         = "saasspotter-terraform-state-159036647480"
    key            = "dev/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "saasspotter-terraform-locks"
    encrypt        = true
  }
}
