# Standard Terraform block
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# The AWS Provider - TFC will handle the authentication
provider "aws" {
  region = "us-east-1"
}

# This data source just "calls" AWS to confirm the connection works
data "aws_caller_identity" "current" {}

# This will print your AWS Account ID in the Terraform log to prove it worked
output "account_id" {
  value = data.aws_caller_identity.current.account_id
}
