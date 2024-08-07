+++
title = 'Compile your Python code to Pycache on Upsun'
date = 2024-08-07T12:00:00+02:00
draft = false
+++

When the python interpretor executes python files, it compiles them to bytecode and saves it as files in a directory called `__pycache__` in the same directory as the code itself. You might have seen such files, here's an example from a Django project:

```bash
$ ls -1 __pycache__/
__init__.cpython-311.pyc
admin.cpython-311.pyc
apps.cpython-311.pyc
models.cpython-311.pyc
tests.cpython-311.pyc
views.cpython-311.pyc
```

This saves time by allowing the compile step to be skipped in subsequent executions. 

On Upsun, python code is deployed onto a read-only file system. The python interpretor won't be able to save the compiled bytecode onto that file system, and it would need to compile the python code every execution. This is wasteful.

You have two options for how to get the bytecode into place to gain the efficiency needed for production. 

1. Compile the python code and check the `__pycache__` directories into git.
2. Let Upsun compile the python code in the build hook.

The second option is superior because it is compiling on the system it will run on, and you won't get any unexpected errors due to mismatches in versions or operating systems.

First, prevent any `__pycache__` files from ever getting into git by adding this to your `.gitignore` file.

```bash
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class
```

To have Upsun compile the pytyon code in the build hook, your build hook should look something like this in `.upsun/config.yaml`:

```yaml
    hooks:
      build: |
        set -eux
        pip install -r requirements.txt

        # Compile python application code
        python -m compileall myproject
```

First the python requirements are installed. Then all of the python code in `myproject` is compiled. The file system is still writable during the build hook phase and all of the python code will be compiled. 

After this has been sent to your Upsun environment (`upsun push`) you can ssh into your application and check:

```bash
upsun ssh
find . -type d -name '__pycache__'
./__pycache__
./migrations/__pycache__
```

In my example the presence of two `__pycache__` directories shows that the command has worked. 

Thanks for reading the tutorial! If you have any questions, my email address is rob@robshouse.net and you can [find me on LinkedIn](https://www.linkedin.com/in/roberttdouglass/). There is also an [Upsun Discord forum](https://discord.gg/PkMc2pVCDV) where I hang out, and you're welcome to find me there.
