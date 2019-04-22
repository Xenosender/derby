README
======


Prerequisite
-----------
- you're supposed to know a minimum about AWS, and how to use its CLI. You must also have enough rights to work on various services.
- you must have AWS commant tool installed
- you must have pipenv installed


Motivation
----------
I aim at creating a collection of automated systems that will allow to automatically generate from one or more videos of a given derby match a drawn representation of the track and the position of each player on it at all times during the match, aligned with the videos to make analysis easier for players and coaches.

I also aim at deploying this system on AWS, as I recently got my AWS associate architect AWS certification. This certification gave me knowledge of AWS services, but not much hands-on, which is why I intend to use AWS packages to train myself.


Wiki
----

check the wiki for more info on the description of the project.

```bash
cd wiki && pipenv install && pipenv shell && ./launch_wiki.sh 
```

Project structure
--------------
Each part of the project has been separated in "microservices" orchestrated around S3 for storage and DynamoDB for data handling.

See each subproject README for details


Deployment
----------
All projects have a deployment script (deploy_to_AWS.sh).

For commodity, and provided that you have setup each subproject, you can use *deploy_all_systems_to_AWS.sh* to call in turn all deployment scripts.



Author : Cyril Poulet, cyril.poulet@centraliens.net
April 2019
