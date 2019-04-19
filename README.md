README
======


Prerequisite
-----------
- you're supposed to know a minimum about AWS, and how to use its CLI. You must also have enough rights to work on various services.
- you must have AWS commant tool installed
- you must have pipenv installed


Wiki
----

check the wiki for the description of the project.

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

