// var upload_bucket_name = 'cp-derby-bucket';
// var bucket_region = 'eu-west-1';
// var identity_pool_id = 'eu-west-1:8920432b-cc7a-415b-a8aa-c5549432d049';
// var s3_upload_startkey = "upload";

var variables;
var s3;

function loadJSON(callback) {   

    var xobj = new XMLHttpRequest();
        xobj.overrideMimeType("application/json");
    xobj.open('GET', 'variables.json', true); // Replace 'my_data' with the path to your file
    xobj.onreadystatechange = function () {
          if (xobj.readyState == 4 && xobj.status == "200") {
            // Required use of an anonymous callback as .open will NOT return a value but simply returns undefined in asynchronous mode
            callback(xobj.responseText);
          }
    };
    xobj.send(null);  
}

function waitForVariablesLoading(){
    if(typeof variables !== "undefined"){
        //variable exists, do what you want
        AWS.config.update({
            region: variables.bucket_region,
            credentials: new AWS.CognitoIdentityCredentials({
                IdentityPoolId: variables.identity_pool_id
            })
        });

        s3 = new AWS.S3({
            apiVersion: '2006-03-01',
            params: {Bucket: variables.upload_bucket_name}
        });
    }
    else{
        setTimeout(waitForVariablesLoading, 250);
    }
}


function addVideo() {
    var files = document.getElementById('videoupload').files;
    if (!files.length) {
        return alert('Please choose a file to upload first.');
    }
    var file = files[0];
    var fileName = file.name;
    var albumPhotosKey = encodeURIComponent(variables.s3_upload_startkey) + '/';

    var photoKey = albumPhotosKey + fileName;
    s3.upload({
            Key: photoKey,
            Body: file,
            ACL: 'bucket-owner-full-control'
        }, 
        function(err, data) {
            if (err) {
                return alert('There was an error uploading your video: ' + err.message);
            }
            alert('Successfully uploaded video.');
        }
    );
}

loadJSON(function(response) {
  // Parse JSON string into object
    variables = JSON.parse(response);
    variables = variables.video_upload;
 });
waitForVariablesLoading()