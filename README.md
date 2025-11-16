# Cloud Tellobase repository

This repository was created with the goal of guarding test scripts
for interactions between tellobase code and cloud service storage 
(probably Google Drive)

## Initial setup

First of all, clone this repository in your machine.

Then, Acquire all the needed packages with the command:

```pip3 install -r ./requeriments.txt```

## Project creation

Before following this guide, ensure there is NO project linked to this application,
or if a change of project is needed.

1.Access the following link to create your google project:

https://console.cloud.google.com/apis/credentials

2.Then, create your project, with EXTERNAL access to the public;

3.Create the OAuth client ID, with type DESKTOP (or COMPUTER APP) and put the name of the application;

4.Download the client_secrets.json;

5.In the page "Test Users", put the email account that will have access to this project;

6.Go to "API and Services" tab and enable the Google Drive API in your project.

With this, adjust your code, client_secrets.json and credentials.json to work with your
project.

If there is no credentials.json initially: execute the main script one time, and it will
open a login screen, in which you will choose a google account that should have access to
the project. 
