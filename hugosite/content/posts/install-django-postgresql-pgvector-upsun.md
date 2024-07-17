+++
title = 'Install Django with PostgreSQL and PGVector on Upsun'
date = 2024-07-17T11:00:00+02:00
draft = true
+++

The order of the imports and settings in your settings.py file determines which settings take precedence. In Django, settings defined later override earlier settings. Given this, the final definition of DATABASES will depend on whether PLATFORM_DB_RELATIONSHIP is set and the Upsun environment variables are present.

Here is a summary of how the precedence works:

Initial Definition in settings.py: Your initial database settings are defined in the main settings.py file.
Override in settings_psh.py: If PLATFORM_DB_RELATIONSHIP is set and the Upsun environment variables are present, settings_psh.py will override the initial DATABASES definition.

```bash
source myenv/bin/activate
pip install psycopg2

pip freeze > requirements.txt

cat requirements.txt
asgiref==3.8.1
Django==5.0.7
gunicorn==22.0.0
packaging==24.1
psycopg2==2.9.9
sqlparse==0.5.0
```

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

{{% notice warning %}}
As of 2024-07-17, `upsun project:init` has a bug when generating the `settings_psh.py` file. The variable seen on line 54 should be all lowercase.

```python
        # if PLATFORM_DB_RELATIONSHIP in PLATFORM_relationships:
        if PLATFORM_DB_RELATIONSHIP in platform_relationships:
```

![Error in settings_psh.py](/posts/install-django-postgresql-pgvector-upsun/01_settings_psh_error.png)

The bug has been reported and fixed upstream, and will be fixed in upcoming releases of the Upsun platform.

{{% /notice %}}


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

### Step 1: Create a Table with a Vector Column

First, create a table with a column for storing vector embeddings. Here, we'll create a table named `items` with an `id` and a `embedding` column.

```sql
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    embedding vector(3) -- Assuming the vectors have a dimensionality of 3
);
```

### Step 2: Insert Embeddings into the Table

Next, insert some sample embeddings into the `items` table. Here, we add three example embeddings.

```sql
INSERT INTO items (embedding) VALUES 
    ('[0.1, 0.2, 0.3]'),
    ('[0.2, 0.1, 0.4]'),
    ('[0.4, 0.3, 0.1]');
```

### Step 3: Perform a Similarity Search Query

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