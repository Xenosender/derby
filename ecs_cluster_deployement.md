CLUSTER DEPLOYMENT
==================


Deploying a cluster is necessary to deploy container-based applications on AWS. 
AWS has a fully managed service for container called **Fargate**, but it does not yet support GPU requirement.

To create and launch the cluster, we use **aws cloudformation** which will create all the necessary resources for the cluster as described in the template.
This template is freely adapted from [this example](https://github.com/brentley/tensorflow-container/blob/master/cluster-cpu-gpu.yml), and is a minimal functionning cluster (no consideration has been put in security, for example)

The resources are:
	- a VPC with one subnet, an internet gateway and the network mapping
	- a cluster resource with the associated security group
	- an autoscaling group to manage the necessary EC2 instances, and the associated launch configuration (ie what the autoscaling group will launch and how) 
	- the IAM resources:
		- role for autoscaling
		- role for EC2 instances
		- role for ECS service
		- role for task execution (with access to s3, dynamoDB and SQS)

Deployement may take up to 10min to complete from the command to a running EC2 instance attached to the cluster.


IMPORTANT POINTS
----------------

1) The launch configuration contains **in "UserData" the launching script for the instances** :

```bash
	#!/bin/bash -x

	# Install the files and packages from the metadata
	sudo mkdir /etc/ecs/
	sudo chmod 777 /etc/ecs/
	echo ECS_CLUSTER=${ECSCluster} >> /etc/ecs/ecs.config

	# Signal the status from cfn-init
	yum install -y aws-cfn-bootstrap
	/opt/aws/bin/cfn-signal -e $? --stack ${AWS::StackName} --resource ECSGPUAutoScalingGroup --region ${AWS::Region}
```

This script is VERY important:
	- the first part declares that the instance is in the cluster (otherwise the instance will run, but won't be detected as a part of the cluster, which will therefore not see it as usable to run tasks)
	- the 2nd part signals the autoscaling group that the instance is correctly started (otherwise, the autoscaling group won't know that its action succeeded, and with rollback with the destruction of the instance as consequence)
If any of these parts fails, the deployement won't work and will rollback, so be careful toying with this script.


2) Once the cluster deployed, **you only pay for running EC2 instances**. As it is, it deploys p2xlarge instances, which are outside of free tier (they cost around 1$/hour). **If you want to toy while staying in the free tier, modify the template to launch t2micro instances**.


3) **Connecting to running instance**
To be able to connect to a running EC2 instance, it needs to be launched with an open ssh port config, and loaded with a ssh key. you have to **create a ssh key** in the [network & security part of EC2 service](https://eu-west-1.console.aws.amazon.com/ec2/v2/home?region=eu-west-1#KeyPairs:sort=keyName), **save it locally** to be able to use it, and **put the name of your key in the KeyName parameter of the yaml template**.

4) **logging**
The sections "cloudwatch:\*" and "logs:\*" in the IAM role descriptions are here to enable logging to cloudwatch. However, some services will automatically send their logs while others not (you will have to configure your containers to use aws logging agent).
 

Files
-----
- _ecs-cluster-def.yml_ : cloudformation template file
- _deploy_aws_ecs_cluster.sh_ : script calling aws cloudformation to create and launch the cluster


Local Configuration
------------
You need to have the AWS command line tool installed


AWS setup
---------
You need the rights to use cloudformation