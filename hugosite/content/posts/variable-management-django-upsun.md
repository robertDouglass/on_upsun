+++
title = 'Variable Management for Django on Upsun'
date = 2024-08-08T09:00:00+02:00
draft = false
+++

## Why Upsun for Django?

Upsun stands out as a comprehensive platform for Django developers that addresses many common pain points in Django deployment and development.

- Ready-to-use services: Redis, PostgreSQL, Kafka, Elastic Search, Open Search and more
- Environment cloning for testing and development (great for teams working together)
- Infrastructure as code for version-controlled server setups
- Local development boost through service tunneling
- Integrated Blackfire profiling for performance optimization

These features collectively create an ecosystem that streamlines Django development, from local coding to production deployment.

## The Importance of Variable Management

While Upsun's features are powerful, their effective use hinges on mastering variable management. Proper variable handling is crucial because it:
- Prevents security breaches by keeping sensitive information out of your codebase
- Maintains environment integrity, ensuring development doesn't interfere with production
- Clarifies system architecture, making your project more maintainable
- Reduces debugging time by minimizing configuration-related issues

Consider this example of secure variable usage:
```python
# Insecure
SECRET_KEY = "actual_secret_key_here"  # Exposed in code

# Secure
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")  # Secured in environment
```

## Understanding Upsun's Variable System

Upsun employs a hierarchical variable system that offers flexibility and security across different project scopes. Understanding this system is key to leveraging Upsun's full potential.

Upsun uses three types of variables:
1. Project variables: Apply across all environments in a project
2. Environment variables: Specific to individual environments (e.g., development, staging, production)
3. Application variables: Defined in `.upsun/config.yaml`, specific to each application

These variables follow a precedence order: Environment > Project > Application. This hierarchy allows for fine-grained control over your configuration.

For example, you might set a default DEBUG value in your application variables:
```yaml
# .upsun/config.yaml
applications:
    myapp:
        variables:
            env:
                DEBUG: false
```
But then override it for a specific environment using the Upsun console or CLI.

Upsun also provides `PLATFORM_*` variables that give you insights into your runtime environment. These are particularly useful for dynamic configuration:

```python
import json
import base64

relationships = json.loads(base64.b64decode(os.environ['PLATFORM_RELATIONSHIPS']))
db_settings = relationships['database'][0]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_settings['path'],
        'USER': db_settings['username'],
        'PASSWORD': db_settings['password'],
        'HOST': db_settings['host'],
        'PORT': db_settings['port'],
    }
}
```

This setup automatically configures your database connection based on the current environment, eliminating the need for manual configuration across different deployments.

## Managing Sensitive Data: OPENAI_API_KEY

Handling sensitive data, like API keys, requires extra care. Let's use the OPENAI_API_KEY as an example to illustrate best practices across different environments.

1. Local Development:
   Create a `.env` file (remember to add it to `.gitignore`):
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

   Then in `settings.py`:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
   ```

   This approach keeps your key secure during local development.

2. Upsun Environments:
   Use the Upsun CLI to securely set the variable:
   ```
   upsun variable:create --level environment --name OPENAI_API_KEY --value your_api_key
   ```

   This command sets the variable for a specific environment, allowing you to use different keys for staging and production.

3. Accessing in Django:
   ```python
   from django.conf import settings
   import openai

   openai.api_key = settings.OPENAI_API_KEY
   ```

   By accessing the key through settings, you maintain a consistent interface regardless of where the key is stored.

## Best Practices and Tips

1. Differentiate Environments:
   Use `PLATFORM_ENVIRONMENT` and `PLATFORM_ENVIRONMENT_TYPE` to adjust settings based on the current environment:
   ```python
   import os

   env_name = os.getenv('PLATFORM_ENVIRONMENT', 'local')
   env_type = os.getenv('PLATFORM_ENVIRONMENT_TYPE', 'development')

   if env_type == 'production':
       DEBUG = False
       ALLOWED_HOSTS = ['www.example.com']
   elif env_type == 'staging':
       DEBUG = True
       ALLOWED_HOSTS = ['staging.example.com']
   else:
       DEBUG = True
       ALLOWED_HOSTS = ['localhost', '127.0.0.1']

   # You can also use env_name for more specific environment handling
   if env_name == 'main':
       # Special configuration for the main environment
       pass
   ```

   This approach allows you to maintain a single settings file while still customizing behavior per environment type and name.

2. Use Upsun-provided variables:
   ```python
   import os
   import json
   import base64

   # Access the application configuration
   app_config = json.loads(base64.b64decode(os.environ['PLATFORM_APPLICATION']).decode('utf-8'))

   # Use PLATFORM_PROJECT_ENTROPY for secret key
   SECRET_KEY = os.environ['PLATFORM_PROJECT_ENTROPY']

   # Set the static root using PLATFORM_APP_DIR
   STATIC_ROOT = os.path.join(os.environ['PLATFORM_APP_DIR'], 'static')

   # Configure database using PLATFORM_RELATIONSHIPS
   if os.environ.get('PLATFORM_RELATIONSHIPS'):
       relationships = json.loads(base64.b64decode(os.environ['PLATFORM_RELATIONSHIPS']).decode('utf-8'))
       db_settings = relationships['database'][0]
       DATABASES = {
           'default': {
               'ENGINE': 'django.db.backends.postgresql',
               'NAME': db_settings['path'],
               'USER': db_settings['username'],
               'PASSWORD': db_settings['password'],
               'HOST': db_settings['host'],
               'PORT': db_settings['port'],
           }
       }
   ```

3. Handle Sensitive Data:
   For highly sensitive information, use Upsun's encrypted variables:
   ```
   upsun variable:create --level project --name SUPER_SECRET --value "sensitive_data" --sensitive true
   ```

   Access these variables through `PLATFORM_VARIABLES`:
   ```python
   import os
   import json
   import base64

   platform_vars = json.loads(base64.b64decode(os.environ['PLATFORM_VARIABLES']).decode('utf-8'))
   SUPER_SECRET = platform_vars.get('SUPER_SECRET')
   ```

4. Debug Variable Issues:
   - Always redeploy after changing variables
   - Use `upsun ssh` to check environment variables directly on the server
   - Review Upsun's activity log for recent changes
   - Use `PLATFORM_TREE_ID` for build-specific logging or debugging

## Conclusion

Upsun's variable management system is a powerful tool for creating flexible, secure, and maintainable Django deployments. By effectively using project, environment, and application variables, you can create a robust configuration setup that adapts to different environments while keeping sensitive data secure.

Remember these key points:
- Leverage Upsun's variable hierarchy for flexible configurations
- Keep sensitive data out of your codebase
- Use `PLATFORM_*` variables for environment-specific settings
- Regularly audit and rotate sensitive variables

Mastering Upsun's variable management not only enhances your project's security but also streamlines your development workflow. It allows you to focus on what truly matters - building exceptional Django applications - while Upsun handles the intricacies of deployment and environment management.

Thanks for reading the tutorial! If you have any questions, my email address is rob@robshouse.net and you can [find me on LinkedIn](https://www.linkedin.com/in/roberttdouglass/). There is also an [Upsun Discord forum](https://discord.gg/PkMc2pVCDV) where I hang out, and you're welcome to find me there.
