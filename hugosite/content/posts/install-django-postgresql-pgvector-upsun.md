+++
title = 'Install Django with PostgreSQL and PGVector on Upsun'
date = 2024-07-17T11:00:00+02:00
draft = false
+++

In my article ["Install Django with SQLite on Upsun"](/posts/install-django-sqlite-upsun/), I explain why I love the [Upsun PaaS](https://upsun.com) and some of the great features you get when you use it. The next step in developing a production-worthy Django site on Upsun is to move to using an enterprise grade database, PostgreSQL. In this tutorial, I also show how to install and use the [PGVector](https://github.com/pgvector/pgvector) extension because the apps that I'm building need the ability to do semantic queries on vectors, in part to do Retrieval Augmented Generation (RAG) with Large Language Models (LLM) such as ChatGPT or Claude. 

Here is a summary of steps that I explained in the previous tutorial. 

## 1. Prepare the environment and start a Django project

```bash
mkdir upsun_django_postgresql
cd upsun_django_postgresql
python -m venv myenv
source myenv/bin/activate
pip install django
pip install gunicorn
pip install psycopg2
pip freeze > requirements.txt
django-admin startproject myproject
cd myproject
python manage.py startapp myapp
cd ..
```

## 2. Make the project compatible with Upsun

Assuming you have started an Upsun project and installed the Upsun CLI, run this in the root directory (`upsun_django_postgresql`):

```bash
upsun project:init
```

Use the arrow keys and space bar to select PosgreSQL. 

```bash
Welcome to Upsun!
Let's get started with a few questions.

We need to know a bit more about your project. This will only take a minute!

✓ Detected stack: Django
✓ Detected runtime: Python
✓ Detected dependency managers: Pip
Tell us your project's application name: [upsun_django_postgresql]


                       (\_/)
We’re almost done...  =(^.^)=

Last but not least, unless you’re creating a static website, your project uses services. Let’s define them:

Select all the services you are using:
Use arrows to move, space to select, type to filter
  [ ]  MariaDB
  [ ]  MySQL
> [x]  PostgreSQL
  [ ]  Redis
  [ ]  Redis Persistent
  [ ]  Memcached
  [ ]  OpenSearch
```

This command has done the following:

1. Added `.upsun/config.yaml` which is where Upsun settings live.
2. Added `myproject/myproject/settings_psh.py`, code which reads Upsun environmental variables.
3. Added a line at the end of `myproject/myproject/settings.py` to include the `settings_psh.py`.

This is a summary of the parts of `.upsun/config.yaml` that pertain to the PostgreSQL database. The important parts are the service definition, which results in a PostgreSQL database server running in its own container, and the `postgresql` relationship, which instructs Upsun to do everything needed to allow the Django app to connect to the database server.

```yaml
applications:
  upsun_django_postgresql:
    source:
      root: "/"

    type: "python:3.11"
    
    # Add a relationship.
    relationships:
      postgresql:

# Add a service.
services:
  postgresql:
    type: postgresql:15 
```


{{% notice info %}}
The `DATABASES` definition in `settings.py` will be overridden by the `DATABASES` definition in `settings_psh.py` if the environmental variable `PLATFORM_DB_RELATIONSHIP` is set and one of the compatible database engines is specified. The `config.yaml` example above meets both of these conditions, so the database configuration will come from the Upsun environment.
{{% /notice %}}


{{% notice warning %}}
As of 2024-07-17, `upsun project:init` has a bug when generating the `settings_psh.py` file. The variable seen on line 54 should be all lowercase.

```python
        # if PLATFORM_DB_RELATIONSHIP in PLATFORM_relationships:
        if PLATFORM_DB_RELATIONSHIP in platform_relationships:
```

![Error in settings_psh.py](/posts/install-django-postgresql-pgvector-upsun/01_settings_psh_error.png)

The bug has been reported and fixed upstream, and will be fixed in upcoming releases of the Upsun platform.

{{% /notice %}}

## 3. Put it in Git and Upsun it

```bash
git add .
git commit -m "Initial deployment of Django with PostgreSQL"
upsun project:set-remote # select the pre-created Upsun project from the list
upsun push
```

This will build a new Django site with PostgreSQL on Upsun. We can create the super user and confirm that the database has been populated with all of the initial tables.


```bash
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

```bash
python myproject/manage.py createsuperuser
exit
```

Now lets interact directly with the PostgreSQL database:

```bash
upsun sql
psql (16.3 (Debian 16.3-1.pgdg110+1), server 15.7 (Debian 15.7-1.pgdg110+1))
Type "help" for help.

main=> \dt
                  List of relations
 Schema |            Name            | Type  | Owner
--------+----------------------------+-------+-------
 public | auth_group                 | table | main
 public | auth_group_permissions     | table | main
 public | auth_permission            | table | main
 public | auth_user                  | table | main
 public | auth_user_groups           | table | main
 public | auth_user_user_permissions | table | main
 public | django_admin_log           | table | main
 public | django_content_type        | table | main
 public | django_migrations          | table | main
 public | django_session             | table | main
(10 rows)

main=> \q
Connection to ssh.eu-5.platform.sh closed.
```

## 4. Install the PGVector extension and test it

PostgreSQL has a [lot of extensions available](https://docs.upsun.com/add-services/postgresql.html#available-extensions). One that I'm particularly interested in is [PGVector](https://github.com/pgvector/pgvector). Vector databases in combination with Large Language Models (LLM), aka. "AI", have given developers new ways to search for semantically similar texts. This has application for many fields, especially any LLM-based applications that need Retrieval Augmented Generation (RAG). PostgreSQl on Upsun supports this perfectly, and this is how you configure it to be installed.  

In `.upsun/config.yaml`, update the `services` definition like this:

```yaml
services:
  postgresql:
    type: postgresql:16 # All available versions are: 15, 14, 13, 12, 11
    configuration:
        extensions:
            - vector
```

Note that Upsun will also run the follwing SQL command as superuser on your database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

{{% notice info %}}
The careful observer will note that I also bumped the PostgreSQL version from 15 to 16 in the above change. That's how easy it is to upgrade service versions on Upsun.
{{% /notice %}}


Below is a sequence of SQL commands to create a new table using `pgvector`, insert a few embeddings into it, and perform a similarity search query to test its functionality.

### Create a table with a vector column

First, create a table with a column for storing vector embeddings. Here, we'll create a table named `items` with an `id` and a `embedding` column.

```sql
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    embedding vector(3) -- Assuming the vectors have a dimensionality of 3
);
```

### Insert embeddings into the table

Next, insert some sample embeddings into the `items` table. Here, we add three example embeddings.

```sql
INSERT INTO items (embedding) VALUES 
    ('[0.1, 0.2, 0.3]'),
    ('[0.2, 0.1, 0.4]'),
    ('[0.4, 0.3, 0.1]');
```

### Perform a similarity search query

To test that the setup is working, perform a similarity search query. Here, we find the top 3 most similar embeddings to a given query vector `[0.2, 0.2, 0.2]`.

```sql
SELECT id, embedding
FROM items
ORDER BY embedding <-> '[0.2, 0.2, 0.2]'
LIMIT 3;
```

The `<->` operator calculates the Euclidean distance between the stored embeddings and the query vector, ordering the results by similarity (closest first).

### Full Sequence

Here's the full sequence of SQL commands:

```sql
-- Create the table
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    embedding vector(3)
);

-- Insert sample embeddings
INSERT INTO items (embedding) VALUES 
    ('[0.1, 0.2, 0.3]'),
    ('[0.2, 0.1, 0.4]'),
    ('[0.4, 0.3, 0.1]');

-- Perform a similarity search
SELECT id, embedding
FROM items
ORDER BY embedding <-> '[0.2, 0.2, 0.2]'
LIMIT 3;
```

Run these commands in your `psql` session, which you can open from the Upsun CLI with `upsun sql`. If everything is set up correctly, you should see the results of the similarity search based on the inserted embeddings.

```sql
 id |   embedding
----+---------------
  1 | [0.1,0.2,0.3]
  2 | [0.2,0.1,0.4]
  3 | [0.4,0.3,0.1]
(3 rows)

main=>
```

## Conclusion

This tutorial shows how to create a Django project to use PostgreSQL with the PGVector extension on the Upsun platform. You now have a robust, production-ready environment capable of handling semantic vector queries essential for advanced applications like Retrieval Augmented Generation with Large Language Models. 

Thanks for reading the tutorial! If you have any questions, my email address is rob@robshouse.net and you can [find me on LinkedIn](https://www.linkedin.com/in/roberttdouglass/). There is also an [Upsun Discord forum](https://discord.gg/PkMc2pVCDV) where I hang out, and you're welcome to find me there.
