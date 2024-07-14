+++
title = 'Install Django with SQLite Upsun'
date = 2024-07-12T16:58:24+02:00
draft = false
+++

## What is Upsun?

[Upsun](https://upsun.com) is a new Platform-as-a-Service (PaaS) offering from [Platform.sh](https://platform.sh). As a PaaS, it is for developers who want to focus on writing the application code and not on the infrastructure that runs it. Here are some of the features that you get with Upsun:

* [Support for many languages](https://docs.upsun.com/languages.html), including Python, PHP, Ruby, and many others. 
* [Support for many databases](https://docs.upsun.com/add-services.html#available-services), including PostgreSQL, MariaDB, MongoDB and others.
* [Support for other neat services](https://docs.upsun.com/add-services.html#available-services) like Redis, OpenSearch, Kafka, and Vault. 
* Git-based deployment: the only way to deploy code to Upsun is through `git push`.
* Instant clones of the entire infrastructure and their persistant data for the purpose of development and testing. 
* Automatic TLS certificates. 
* Blackfire.io integration for monitoring and profiling. 
* Sendgrid integration for sending mails. 
* Deploy into a wide range of AWS, GCP, or Azure regions. 
* Backups.
* Much more, [take a look](https://docs.upsun.com/). 

## What are we deploying?

We'll deploy Django running on Gunicorn with a SQLite database. This is the most basic setup for a Django project on Upsun and it will introduce the basic ideas. The instructions are for MacOS. 

You need to have the following installed already:

* git
* python3
* pip
* homebrew


## 1. Prepare the environment

```
mkdir upsun_django_sqlite
cd upsun_django_sqlite
python -m venv myenv
source myenv/bin/activate
pip install django
pip install gunicorn
pip freeze > requirements.txt
```

The above commands install the required python libraries and write them into a `requirements.txt` file. Upsun will use that file to install the python libraries into the server environment.

## 2. Start a Django project

```
django-admin startproject myproject
cd myproject
python manage.py startapp myapp
python manage.py runserver
```

This creates a Django project called `myproject` with an app called `myapp`, and it tests the basic install by starting the local server. You should see a message that ends similarly to this:

```
Django version 5.0.7, using settings 'myapp.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

And visiting http://127.0.0.1:8000/ should show you a screen like this. Quit the server with CONTROL-C.


{{< figure src="/on_upsun/images/03-upsun-django-running.png" title="Django running locally" >}}


## 3. Get it into Git

```
cd ..
pwd
/Users/robert/Code/myproject
```

You should be at the base directory of your project now.

```
git init
git add .
git commit -m "Initial Django installation."
```

## 4. Install the Upsun CLI tool

The Upsun [documentation for installing the CLI tool is here](https://docs.upsun.com/administration/cli.html#1-install). On Mac with Homebrew you do this:

```
brew install platformsh/tap/upsun-cli
```


## 5. Get an Upsun account and install the upsun CLI tool. 

[Visit Upsun and begin a free trial](https://upsun.com). You'll be asked to create an organization and set a path for that organization.

{{< figure src="on_upsun/images/01-upsun-organization.png" title="Create an Upsun organization" >}}

You'll be asked to start a new project. Choose "Deploy an existing Git repository". 

{{< figure src="images/02-upsun-new-project.png" title="Deploy an existing local git repository" >}}

Name your project and choose a region. Sweden has the lowest CO2 output per compute unit due to their low-emmission energy sources. 

<link rel="stylesheet" href="{{ "css/style.css" | absURL }}">
{{< figure src="/images/04-upsun-region.png" title="Your project details" >}}

On the "Prepare project locally" screen that follows, you've already done the first two steps, intalling the Upsun CLI and preparing your git repository locally. You need to wait for the third field, "Connect directory to Upsun" to populate as soon as your environment has been provisioned. 

{{< figure src="images/05-prepare-project-locally.png" title="Wait for the connection details" >}}

## 4. Authenticate the Upsun CLI and set the remote

When the third field populates it will have a command that includes your project ID. Make sure to use yours, not mine (as shown below).

```
upsun project:set-remote oes36x5dtgp2u
```

This will cause you to first authenticate the CLI by opening a browser window, and then it will add a git remote to the git repository and provision a key to let you interact with Upsun from the command line.

## 5. Use the Upsun CLI to add the Upsun configuration

Upsun needs information about your project to be able to run it properly. Fortunately for Django developers, there's a command that gets us most of the way there. 

```
upsun project:init
```

When you get to this part, just push Enter and don't add services for now. 

```
Select all the services you are using:
Use arrows to move, space to select, type to filter
> [ ]  MariaDB
  [ ]  MySQL
  [ ]  PostgreSQL
  [ ]  Redis
  [ ]  Redis Persistent
  [ ]  Memcached
  [ ]  OpenSearch
```

Upsun will claim to have done the follwing:

```

┌───────────────────────────────────────────────────┐
│   CONGRATULATIONS!                                │
│                                                   │
│   We have created the following files for your:   │
│     - .environment                                │
│     - .upsun/config.yaml                          │
│                                                   │
│   We’re jumping for joy! ⍢                        │
└───────────────────────────────────────────────────┘
         │ /
         │/
         │
  (\ /)
  ( . .)
  o (_(“)(“)
  ```

  To see all of the changes, use git:

  ```
   git status
On branch main
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   myproject/myproject/settings.py

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	.upsun/
	myproject/myproject/settings_psh.py
```

Let's add those to git.

```
git add .
git commit -m "upsun project:init"
[main 32ccfb6] upsun project:init
 3 files changed, 231 insertions(+)
 create mode 100644 .upsun/config.yaml
 create mode 100644 myproject/myproject/settings_psh.py
```

The change to your `settings.py` file is quite small, it just included the newly created `setting_psh.py` file which includes code to read variables out of the Upsun environment. 

## 6. Add a mount for the SQLite database

One step that Upsun misses if you are using SQLite is to add a mount for the database. This is important because all of the code and static assets that we've created so far will be deployed onto a read-only file system on Upsun. This is great for security and general good DevOps hygiene, but it means Django will fail if it doesn't have a place to write its data.

Open `.upsun/config.yaml` in your code editor and add the following:

```yaml
    mounts:
      "/db": 
        source: "storage"
        source_path: "db" 
```

## 7. Point Django to the mount for the database

At the top of your `./myproject/myproject/settings.py` file, add an import for the `os` package.

```python
import os
```

In your `./myproject/myproject/settings.py` file, find the `DATABASES` variable and replace it with the following, including the `DB_DIR` variable.

```python
# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# Set the DB_DIR to one level higher than BASE_DIR
DB_DIR = BASE_DIR.parent

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db/db.sqlite3',
        'NAME': os.path.join(DB_DIR, 'db', 'db.sqlite3'),
    }
}
```

## 8. Add it to Git and get it up to Upsun

```
git add .
git commit -m "Mount for SQLite"
upsun push
```

You should see a lot of terminal output at this point, and I'll dig into that in a moment. But the end should look like this:

```
...
            Applying auth.0011_update_proxy_permissions... OK
            Applying auth.0012_alter_user_first_name_max_length... OK
            Applying sessions.0001_initial... OK

        Opening environment
        Environment configuration
          upsun_django_sqlite (type: python:3.11, cpu: 0.5, memory: 224, disk: 512)

        Environment routes
          http://main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/ redirects to https://main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/
          http://www.main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/ redirects to https://www.main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/
          https://main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/ is served by application `upsun_django_sqlite`
          https://www.main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/ redirects to https://main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/

      Blackfire build scheduled


  To git.eu-5.platform.sh:oes36x5dtgp2u.git
   * [new branch]      HEAD -> main
```

If yours looks similar, congratulations, you have a Django app running. Let's open it up.

```
upsun url
```

You'll get a number of options. These are called `routes` in Upsun parlance. Pick any of them.

```
Enter a number to open a URL
  [0] https://main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/
  [1] https://www.main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/
  [2] http://main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/
  [3] http://www.main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/
```

{{< figure src="images/06-not-found.png" title="Not Found" >}}

Oops! Is that a mistake? No, this is expected. Try adding `/admin` to the end of the URL in the browser:

{{< figure src="images/07-admin.png" title="Django admin" >}}

That's better, but we don't have an admin user yet. Let's create one.

## 9. Create the admin user

Upsun has a lot of functionality built into its CLI. You can see the options by running `upsun list`. One of the great features is the ability to easiy open a shell on the environment that you're working on. Let's do that:

```
upsun ssh

 _   _
| | | |_ __ ____  _ _ _
| |_| | '_ (_-< || | ' \
 \___/| .__/__/\_,_|_||_|
      |_|

 Welcome to Upsun.

Environment: main-bvxea6i
Branch: main
Project: oes36x5dtgp2u

web@upsun_django_sqlite.0:~$
```

You're now on the command line of your web environment. You can interact with your Django environment now.

```
python myproject/manage.py createsuperuser
```

After entering your super user information you should be able to log into the admin area of your Django app in the browser.

## 10. Let's look at what happened when we deployed

When we ran `upsun push` a lot happened. Let's look at it all.

```
upsun push
[main 5f1e4af] Mount for SQLite
 2 files changed, 10 insertions(+), 2 deletions(-)
Selected project: Django SQLite (oes36x5dtgp2u)

Pushing HEAD to the environment main (type: production).

Are you sure you want to continue? [Y/n] y
```

Upsun can have many copies of your app in different environments. At the beginning, we've just got one production environment on the `main` branch, but we could eventually have many environments that are used for testing and developing. 

```

  Enumerating objects: 8317, done.
  Counting objects: 100% (8317/8317), done.
  Delta compression using up to 10 threads
  Compressing objects: 100% (5188/5188), done.
  Writing objects: 100% (8317/8317), 13.87 MiB | 9.28 MiB/s, done.
  Total 8317 (delta 2044), reused 8299 (delta 2037), pack-reused 0

  Validating submodules

  Validating configuration files

  Processing activity: Robert Douglass ROBSHOUSE pushed to Main
      Found 3 commits

      Configuring resources
        Using default resources
          Setting 'upsun_django_sqlite' resources to 0.5 CPU, 224MB RAM.
          Setting 'upsun_django_sqlite' disk to 512MB.

```

Based on our `.upsun/config.yaml` file, Upsun determined that we need one runtime environment with 0.5 CPU and 224MB RAM, and one disk mount with 512MB. You can read about how to [adjust these resources in the Upsun documentation](https://docs.upsun.com/manage-resources/adjust-resources.html).

```

      Building application 'upsun_django_sqlite' (runtime type: python:3.11, tree: 7e514d7)
        Generating runtime configuration.

        Executing build hook...
          W: + pip install -r requirements.txt
          Collecting asgiref==3.8.1
            Downloading asgiref-3.8.1-py3-none-any.whl (23 kB)
          Collecting Django==5.0.7
            Downloading Django-5.0.7-py3-none-any.whl (8.2 MB)
          Collecting gunicorn==22.0.0
            Downloading gunicorn-22.0.0-py3-none-any.whl (84 kB)
          Collecting packaging==24.1
            Downloading packaging-24.1-py3-none-any.whl (53 kB)
          Collecting sqlparse==0.5.0
            Downloading sqlparse-0.5.0-py3-none-any.whl (43 kB)
          Installing collected packages: sqlparse, packaging, asgiref, gunicorn, Django
          Successfully installed Django-5.0.7 asgiref-3.8.1 gunicorn-22.0.0 packaging-24.1 sqlparse-0.5.0
```

This is the part where Upsun uses `requirements.txt` to install your python libraries. This is done in the [Upsun build hook](https://docs.upsun.com/create-apps/hooks/hooks-comparison.html#build-hook). 

```
          W: + python myproject/manage.py collectstatic --noinput

          126 static files copied to '/app/static'.
```

Upsun just ran a command to collect the static assets from your project and put them into a read-only location `/app/static` where the server can serve them. This command is also in the build hook (see `.upsun/config.yaml`). 

```

        Executing pre-flight checks...

        Compressing application.
        Beaming package to its final destination.

      W: Route 'main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site' doesn't map to a domain of the project, using default development hostname.
      W: Route 'www.main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site' doesn't map to a domain of the project, using default development hostname.

```

Based on the `routes` part of `.upsun/config.yaml`, Upsun has created the above URLs to access your application.

```
      Provisioning certificates
        Validating 2 new domains
        Provisioned new certificate for 2 domains
        (Next refresh will be at 2024-09-12 15:19:54+00:00.)
        Certificates
        - certificate 57594b5: expiring on 2024-10-10 15:19:54+00:00, covering {,www}.main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site
```

Upsun provisioned LetsEncrypt certificates so that you're running on `https` by default.

```
      Blackfire configured for application upsun_django_sqlite
```

Upsun automatically [integrates with Blackfire.io for monitoring and profiling](https://docs.upsun.com/increase-observability/application-metrics/understanding.html#blackfire-deterministic-observability-for-php-and-python). 

```
      Creating environment main
        Starting environment
        Updating endpoints for upsun_django_sqlite
        Opening application upsun_django_sqlite and its relationships
        Executing deploy hook for application upsun_django_sqlite
          W: + python myproject/manage.py migrate
          Operations to perform:
            Apply all migrations: admin, auth, contenttypes, sessions
          Running migrations:
            Applying contenttypes.0001_initial... OK
            Applying auth.0001_initial... OK
            Applying admin.0001_initial... OK
            Applying admin.0002_logentry_remove_auto_add... OK
            Applying admin.0003_logentry_add_action_flag_choices... OK
            Applying contenttypes.0002_remove_content_type_name... OK
            Applying auth.0002_alter_permission_name_max_length... OK
            Applying auth.0003_alter_user_email_max_length... OK
            Applying auth.0004_alter_user_username_opts... OK
            Applying auth.0005_alter_user_last_login_null... OK
            Applying auth.0006_require_contenttypes_0002... OK
            Applying auth.0007_alter_validators_add_error_messages... OK
            Applying auth.0008_alter_user_username_max_length... OK
            Applying auth.0009_alter_user_last_name_max_length... OK
            Applying auth.0010_alter_group_name_max_length... OK
            Applying auth.0011_update_proxy_permissions... OK
            Applying auth.0012_alter_user_first_name_max_length... OK
            Applying sessions.0001_initial... OK
```

The [Upsun deploy hook](https://docs.upsun.com/create-apps/hooks/hooks-comparison.html#deploy-hook) is run after the application is in its environments but before requests are allowed to hit the webserver. In this case, Upsun has run the Django migrations which, on the first push, also creates and populates the SQLite database. 

```
        Opening environment
        Environment configuration
          upsun_django_sqlite (type: python:3.11, cpu: 0.5, memory: 224, disk: 512)

        Environment routes
          http://main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/ redirects to https://main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/
          http://www.main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/ redirects to https://www.main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/
          https://main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/ is served by application `upsun_django_sqlite`
          https://www.main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/ redirects to https://main-bvxea6i-oes36x5dtgp2u.eu-5.platformsh.site/

      Blackfire build scheduled


  To git.eu-5.platform.sh:oes36x5dtgp2u.git
   * [new branch]      HEAD -> main
```

Thanks for reading the tutorial! If you have any questions, my email address is rob@robshouse.net and you can [find me on LinkedIn](https://www.linkedin.com/in/roberttdouglass/). There is also an [Upsun Discord forum](https://discord.gg/PkMc2pVCDV) where I hang out, and you're welcome to find me there.
