# DT_Workshop - Frontier Agents Demo

A small 3-tier web application ("Order Service") on AWS, used to demonstrate
three AWS frontier agents in a single scenario:

- **AWS DevOps Agent** - reliability / incident response
- **AWS Continuum** - security
- **AWS FinOps Agent** - cost

## Architecture

```
Internet -> ALB (public subnets) -> EC2 Auto Scaling Group (private subnets) -> RDS MySQL (private subnets)
```

- **Region:** us-east-1 (N. Virginia)
- **App:** Python / Flask, served by gunicorn on port 8080
- **Deploy:** AWS CodeDeploy (in-place, EC2/on-prem compute platform)

## Repository layout

| Path | Purpose |
|------|---------|
| `infrastructure/network.yaml` | CloudFormation: VPC, subnets, NAT, routing |
| `infrastructure/app.yaml` | CloudFormation: ALB, EC2 ASG, RDS, CodeDeploy, IAM |
| `app/` | Flask application + systemd unit |
| `appspec.yml` | CodeDeploy deployment spec |
| `scripts/` | CodeDeploy lifecycle hook scripts |
| `docs/` | Deployment guides |

## Deployment

See `docs/01-infrastructure-deployment.md` for the step-by-step AWS Console
deployment guide for the network and app CloudFormation stacks.
