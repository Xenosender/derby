UPLOAD PAGE PROJECT
===================

This is a very simple upload page to a s3 bucket.

Files
-----
- _upload.html_ : html page with "choose video" and "upload video" buttons
- _app.js_ : javascript code for s3 connection and upload
- _variables.json_ : json file with variables used in the projects (symbolic link to ../variables.json)
- _deploy_to_AWS.sh_ : script to deploy to the chosen bucket


Relevant variables
-----------------

```json
    "video_upload": {
    	"upload_bucket_name": "cp-derby-bucket",                                // destination of the upload
    	"bucket_region": "eu-west-1",                                           // region of the bucket
    	"s3_upload_startkey": "upload",                                         // path to upload directory in the bucket
    	"identity_pool_id": "eu-west-1:8920432b-cc7a-415b-a8aa-c5549432d049"    // Cogito pooled id used to connect to s3
    }
```


AWS setup
---------
Here I made the choice of static hosting via a s3 bucket : simple, cheap, worldwide accessibility, serverless. If you need a more complicated site, you'll have to use EC2 servers.

- **S3**: you need 2 buckets:
    
    - a bucket hosting the website : 
        - the property "bucket hosting" must be enabled (you can then use cloudfront to use a better url than the one automatically attributed, but this is not covered here)
        - it must be readable by the public. For that, you need to set the Permissions.bucket_policy to :
        
        ```json
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::your-page-bucket/*"
                }
            ]
        }
        ```
        This also needs to set "Block public and cross-account access if bucket has public policies" to False in Permissions.Public_access_settings
    
        - a bucket for uploaded videos. This one should be private, so you can keep the default configuration.
        
- **Cogito** : you need to setup a federated identity to upload to the bucket
- **IAM** : you need to create a role to give the federated identity you created the rights to write to the bucket

For these 2 last steps, you can use the tutorial here : [AWS Tutorial](https://docs.aws.amazon.com/sdk-for-javascript/v2/developer-guide/s3-example-photo-album.html)


Deployment
----------
The deployment is only a push to a s3 bucket hosting the site as a static site.

Change the WEBPAGE_S3_BUCKET variable in the script to the correct bucket name.
It should not be the video upload directory, for correct access management


Possible improvements
--------------------
- the page is VERY SIMPLE: you can do much to improve the look of it!
- access to website : if you want a broader access to your page, you can use cloudfront to create a better url or integrate it in your web domain
- security : access policy to the files of the website should be more fine-grained (public read access to the html page only)
