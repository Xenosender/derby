LAMBDA FUNCTION PROJECT TO MANAGE ALL SQS QUEUES USED TO ARTICULATE SYSTEMS
===================

This is lambda function which is called by updates on DynamoDB main table. It:
    - checks that all SQS queues declared in the variables.json file exist, and create those that don't
    - for each listed change in dynamoDB:
        - extract videoID, s3 bucket/key, and current process step (name and state)
        - send it to the correct SQS queue for the next process
    
This is done to automatically propagate changes on dynamoDB records



Files
-----
- _lambda_function.py_ : the python code of the lambda. AWS entry point is lambda_function.lambda_handler
- _Pipfile_ : configuration file for pipenv
- _variables.json_ : json file with variables used in the projects (symbolic link to ../variables.json)
- _deploy_to_AWS.sh_ : script to deploy the lambda


Relevant variables
-----------------

```json
  {
	"process_steps": ["upload", "human_detection", "team_detector"],                   // ordered steps in the system
	"aws_queues": {                                                                    // queue to use to trigger each step
		"human_detection": "derby-call-humandetector",
		"team_detection": "derby-call-teamdetector"
	}
  }
```


Local Configuration
------------
You need to have the AWS util installed, and Pipenv
To develop locally, use "pipenv install"


AWS setup
---------
- **lambda**: create a lambda with the name you want, in python 3.6. It should create the associated IAM role.
    - you can configure the trigger from there, from your input DynamoDB table
- **IAM**: add inline policies to the role associated to the lambda:
    - read on DynamoDB streams   (This will be added automatically if you create your lambda from the "create trigger" button in DynamoDB), and launch lambdas
    - read and write on SQS queues and messages


Deployment
----------
To deploy a lambda, it must come zipped with all its dependencies. However, locally we need boto3 to connect to AWS services, but on AWS it is on the python path.
For this reason, the script:
    
- uninstalls boto3 locally
- installs all dependencies in a local directory
- zips it and adds code to it
- uploads to AWS lambda
- cleans
- reinstall boto3 locally
    

To setup the name of the lambda to update, change AWS_LAMBDAFUNCTION_NAME in the deployment script.


IMPORTANT : To work once deployed, the python file *MUST NOT* have a "if __name__ == '__main__'"!


Author : Cyril Poulet, cyril.poulet@centraliens.net
April 2019