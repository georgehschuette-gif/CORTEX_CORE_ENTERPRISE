# Dedicated Instance for the PURE CORTEX CORE
resource "aws_instance" "cortex_core_pure" {
  ami           = "ami-0c55b159cbfafe1f0" # High-performance base
  instance_type = "t3.medium"             # Baseline for the initial 50-cycle proof

  tags = {
    Name    = "CORTEX_CORE_PURE"
    Project = "CORTEX_CORE_ENTERPRISE"
    Status  = "GOLD_STANDARD_VERIFICATION"
  }
}

# The Fortress Perimeter
resource "aws_security_group" "cortex_security" {
  name        = "cortex-pure-fortress"
  description = "Cloaking for Cortex System"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # We will narrow this to your IP once confirmed
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
