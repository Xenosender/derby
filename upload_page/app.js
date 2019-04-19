//Copyright 2019 Cyril Poulet, cyril.poulet@centraliens.net
//
//This program is free software: you can redistribute it and/or modify
//it under the terms of the GNU General Public License as published by
//the Free Software Foundation, either version 3 of the License, or
//(at your option) any later version.
//
//This program is distributed in the hope that it will be useful,
//but WITHOUT ANY WARRANTY; without even the implied warranty of
//MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//GNU General Public License for more details.
//
//You should have received a copy of the GNU General Public License
//along with this program.  If not, see <https://www.gnu.org/licenses/>.

var variables;
var s3;

function loadJSON(callback) {   
    /* function to load a local json file */
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
    /* function waiting for "variables" to be loaded, then using them to initialize AWS config and "s3" object */
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
    /* send to AWS the video file picked by the user */
    var files = document.getElementById('videoupload').files;
    if (!files.length) {
        return alert('Please choose a file to upload first.');
    }
    var file = files[0];
    var fileName = file.name;
    var videoDirectory = encodeURIComponent(variables.s3_upload_startkey) + '/';

    var videoKey = videoDirectory + fileName;
    s3.upload({
            Key: videoKey,
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

// load variables from local file
loadJSON(function(response) {
  // Parse JSON string into object
    variables = JSON.parse(response);
    variables = variables.video_upload;
 });
 // initialize connection to AWS
waitForVariablesLoading()