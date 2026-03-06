group "default" {
  targets = ["landscraper"]
}

variable "TAG" {
  default = "latest"
}

variable "REGISTRY" {
  default = "swarm1:5000"
}

target "landscraper" {
  context    = ".."
  dockerfile = "docker/Dockerfile"
  tags       = ["${REGISTRY}/landscraper:${TAG}", "${REGISTRY}/landscraper:latest"]
  platforms  = ["linux/amd64"]
}

target "landscraper-dev" {
  inherits = ["landscraper"]
  tags     = ["landscraper:dev"]
  cache-from = ["type=local,src=/tmp/.buildx-cache"]
  cache-to   = ["type=local,dest=/tmp/.buildx-cache"]
}
