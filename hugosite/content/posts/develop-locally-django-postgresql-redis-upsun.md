+++
title = 'Develop Django Locally - PostgreSQL and Redis on Upsun'
date = 2024-07-29T16:58:24+02:00
draft = false
+++

This post shows how to develop Django locally using the PostgreSQL and Redis servers in the cloud, [on Upsun](https://upsun.com).

There are several reasons why a developer would want to develop without installing a copy of the services on their local computer:

1. Time and effort: why install services you don't need if they're available elsewhere?
2. Data: If you're working on a production site, there's likely production data that influences how the app works. Synchronizing this data to your local machine can be burdensome.
3. Context switching: If you work on mutiple projects, switching between them can be cumbersome.

Connecting your local Django installation to the databases in the cloud solves these. Doing it on Upsun brings further advantages, though. 

1. Instant cloning of production data into development environments.
2. Connect to databases of your choice with 2 local commands.
3. Share databases with other devs working on the same branch.

To start, deploy the File Uploader example app onto Upsun. 

```bash
git clone git@github.com:robertDouglass/on_upsun.git
cd on_upsun/03_django_redis_celery
upsun project:create
# name your project and choose a region, and set the remote to the repository
git init
git add .
git commit -m "File Uploader"
upsun push
``` 

At this point you have a running Django app on Upsun, and you have the code for that app locally. Let's test it and get some data into it. 

```bash
upsun url
```
Pick any of the URLs and you should end up on this very simple screen where you can upload a file or two. 

![File Uploader](/posts/develop-locally-django-postgresql-redis-upsun/01_file_upload.png)

Upload a file or two so that you have data in the database. Then you can test that data:

```bash
upsun sql "select * from uploads_uploadedfile;"
```

## Make a development branch

Now pretend that the version of the app that you interacted with, on the `main` branch, is your production environment. You don't want to work directly on that, so let's make a development environment.

```bash
 upsun environment:branch dev
 ```

You now have two copies of your app on Upsun, and they have exactly the same code and a copy of the same data. You're ready to develop. Make sure your local git repo is also on the new dev branch:

```bash
git pull upsun dev
git checkout dev
```
{{% notice info %}}
You will need to create a python virtual environment and `pip install -r requirements.txt` to actually run the application locally.
{{% /notice %}}

### Tunnels to the Upsun Services

Open tunnels to the Upsun services:

```bash
upsun tunnel:open
SSH tunnel opened to postgresql at: pgsql://main:main@127.0.0.1:30000/main
SSH tunnel opened to redis at: redis://127.0.0.1:30001

Logs are written to: /Users/robert/.upsun-cli/tunnels.log

List tunnels with: upsun tunnels
View tunnel details with: upsun tunnel:info
Close tunnels with: upsun tunnel:close

Save encoded tunnel details to the PLATFORM_RELATIONSHIPS variable using:
  export PLATFORM_RELATIONSHIPS="$(upsun tunnel:info --encode)"
```

The `upsun tunnel:open` creates local endpoints to the PostgreSQL and Redis servers. You can inspect them with:

```bash
upsun tunnel:info
```

And you can use those credentials in your local development by exporting them:
```bash
export PLATFORM_RELATIONSHIPS="$(upsun tunnel:info --encode)"
```
Due to the way the `settings_psh.py` is written in this demo app, we also need to set an application name:
```bash
export PLATFORM_APPLICATION_NAME="uploader"
```

Now you're ready to run Django locally using the PostgreSQL and Redis servers in the cloud:

```bash
python manage.py runserver
```

## Make a change and merge into Production

To complete this example, let's make a change to our app. I made a change to my template:

```diff
diff --git a/uploads/templates/uploads/upload.html b/uploads/templates/uploads/upload.html
index ed97d3a..7625353 100644
--- a/uploads/templates/uploads/upload.html
+++ b/uploads/templates/uploads/upload.html
 </head>
 <body>
-    <h1>File Upload</h1>
+    <h1>Awesome File Upload</h1>
     <form>
 ```
 
 Then we can:
 ```bash
 git add .
 git commit -m "improve the heading"
 upsun push
 ```

 Once you've tested the change on the `dev` branch, you can safely merge it into production. 

 ```bash
upsun merge
Are you sure you want to merge dev into its parent, main? [Y/n]
```

That's it! You've now developed a Django app locally while using the databases provided by Upsun on an environment specifically for development. After making the changes, you merged them into production.

Thanks for reading the tutorial! If you have any questions, my email address is rob@robshouse.net and you can [find me on LinkedIn](https://www.linkedin.com/in/roberttdouglass/). There is also an [Upsun Discord forum](https://discord.gg/PkMc2pVCDV) where I hang out, and you're welcome to find me there.








