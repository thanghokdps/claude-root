terraform {
  required_version = ">= 1.5"
}

provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "exports" {
  bucket = "acme-${var.env}-exports"

  tags = {
    env     = var.env
    service = "exports"
  }
}

resource "aws_s3_bucket_versioning" "exports" {
  bucket = aws_s3_bucket.exports.id

  versioning_configuration {
    status = "Enabled"
  }
}
