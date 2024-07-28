# On Upsun

Welcome to the "On Upsun" project! This repository contains Hugo pages that illustrate how to set up and deploy Django projects on the Upsun Platform-as-a-Service (PaaS) by Platform.sh. The tutorials cover various configurations, including using SQLite and PostgreSQL with the PGVector extension for advanced database functionalities.

## Contents

- **Install Django with SQLite on Upsun**: Basic setup of Django using SQLite on Upsun.
- **Install Django with PostgreSQL and PGVector on Upsun**: Advanced setup with PostgreSQL and PGVector for semantic queries and Retrieval Augmented Generation (RAG) with Large Language Models (LLM).

## Prerequisites

- Git
- Python 3
- Pip
- Homebrew (for macOS users)
- Upsun CLI

## Tutorials

### 1. Install Django with SQLite on Upsun

This tutorial walks you through setting up a basic Django project with a SQLite database on Upsun. It covers:
- Environment preparation
- Django project setup
- Git integration
- Upsun CLI installation
- Configuring Upsun for deployment
- Creating an admin user

For detailed steps, refer to the [Install Django with SQLite on Upsun tutorial](https://robertdouglass.github.io/on_upsun/posts/install-django-sqlite-upsun/).

### 2. Install Django with PostgreSQL and PGVector on Upsun

This advanced tutorial demonstrates how to configure a Django project to use PostgreSQL and the PGVector extension on Upsun. It includes:
- Environment setup and project initialization
- Making the project compatible with Upsun
- Using Git for deployment
- Interacting with PostgreSQL
- Installing and testing the PGVector extension

For detailed steps, refer to the [Install Django with PostgreSQL and PGVector on Upsun tutorial](https://robertdouglass.github.io/on_upsun/posts/install-django-postgresql-pgvector-upsun/).

### 3. Background Tasks using Celery with Redis in Django on Upsun

This tutorial shows the [power of using Celery background tasks in Upsun workers](https://robertdouglass.github.io/on_upsun/posts/django-redis-celery/). It covers:

- Setting up a minimal Django application on Upsun
- Using PostgreSQL database, Python Gunicorn application server, and Redis
- Implementing a file upload feature with background processing
- Extending Django behavior with Signals
- Using Celery Queue and Beat for background tasks
- Creating Workers with shared file system mounts on Upsun
- Running Redis on Upsun
- Configuring Django settings for Celery and Redis
- Monitoring Celery tasks in action
- Interacting with Redis using the CLI on Upsun

## Contact me

If you have any questions, my email address is rob@robshouse.net and you can [find me on LinkedIn](https://www.linkedin.com/in/roberttdouglass/). There is also an [Upsun Discord forum](https://discord.gg/PkMc2pVCDV) where I hang out, and you're welcome to find me there.