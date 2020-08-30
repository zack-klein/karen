terraform {

  backend "s3" {
    bucket = "zacharyjklein-state"
    key    = "state/fantasy-football.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region  = "us-east-1"
  version = "~> 2.60"
}

module "instance" {
  source         = "github.com/zack-klein/ec2-instance"
  instance_name  = "fantasy-football"
  user_data_path = "./user-data.sh"
  vpc_id         = "vpc-792b4b03"
  subnets        = ["subnet-bc9fcee0", "subnet-21237746", "subnet-7b91c255"]
  ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCBIu48ryZCZZlufVF9AgjBrEmjau3Hmb20Aah75SYQTAhA5+9E5MuXJ1UwlDBXUPDIv/VFgu+/AmyT1kk1+8N9OE8I2kVcr8nAsFV7c7PNG60zxMXtCiCA8KgzQw/JeUceCmSZnGTCY5pgkXFvTAVaPtNywaEuKU9sICi+J+jm6WBk+IbX+GQYCJCTjGugbH0SOqivyBj/xiVgXQAdDKybvSQkWZqlERnfpbI0vSGEVqzlia+D54TlxaL5tnI76KoR6toWBmp81Y4JVHNAMW7LMerbQuor9gEUWWY1pdY/NikY9Sy1YMPOiYtAqbi/x3rm03tsr1mEAsu7o29g+oID"
  instance_profile = aws_iam_instance_profile.profile.name
}

resource "aws_s3_bucket" "b" {
  bucket = "fantasy-football-streamlit"
  acl    = "private"
}

resource "aws_iam_instance_profile" "profile" {
  name = "fantasy-football-profile"
  role = aws_iam_role.role.name
}

resource "aws_iam_role" "role" {
  name = "fantasy-football-role"
  path = "/"

  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": "sts:AssumeRole",
            "Principal": {
               "Service": "ec2.amazonaws.com"
            },
            "Effect": "Allow",
            "Sid": ""
        }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "secretsmanager" {
  role       = aws_iam_role.role.name
  policy_arn = "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
}

resource "aws_iam_role_policy_attachment" "s3" {
  role       = aws_iam_role.role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}
