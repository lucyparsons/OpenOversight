# Contributing Guide
First, thanks for being interested in helping us out! If you find an issue you're interested in, feel free to make a comment about how you're thinking of approaching implementing it in the issue and we can give you feedback.  Please also read our [code of conduct](/CODE_OF_CONDUCT.md) before getting started.

## Submitting a Pull Request (PR)
When you come to implement your new feature, clone the repository and then create a branch off `develop` locally and add commits to implement your feature.

If your git history is not so clean, please do rewrite before you submit your PR - if you're not sure if you need to do this, go ahead and submit and we can let you know when you submit.

To submit your changes for review you have to fork the repository, push your new branch there and then create a Pull Request with `OpenOversight:develop` as the target.

Use [pull_request_template.md](/.github/pull_request_template.md) to create the description for your PR! (The template should populate automatically when you go to open the pull request.)

### Recommended privacy settings
Whenever you make a commit with `git` the name and email saved locally is stored with that commit and will become part of the public history of the project. This can be an unwanted, for example when using a work computer. We recommend changing the email-settings in the github account at https://github.com/settings/emails and selecting "Keep my email addresses private" as well as "Block command line pushes that expose my email". Also find your github-email address of the form `<id>+<username>@users.noreply.github.com` in that section. Then you can change the email and username stored with your commits by running the following commands
```shell
git config user.email "<your-github-email>"
git config user.name "<your-github-username>"
```
This will make sure that all commits you make locally are associated with your github account and do not contain any additional identifying information. More detailed information on this topic can be found [here](https://docs.github.com/en/free-pro-team@latest/github/setting-up-and-managing-your-github-user-account/setting-your-commit-email-address).

### Linting / Style Checks
We use [pre-commit](https://pre-commit.com/) for automated linting and style checks. Be sure to [install pre-commit](https://pre-commit.com/#installation) and run `pre-commit install` in your local version of the repository to install our pre-commit checks. This will make sure your commits are always formatted correctly.

You can run `pre-commit run --all-files` or `make lint` to run pre-commit over your local codebase, or `pre-commit run` to run it only over the currently stages files.

## Development Environment
You can use our Docker-compose environment to stand up a development OpenOversight.

You will need to have Docker installed in order to use the Docker development environment.

To build and run the development environment, simply `make dev`. Whenever you want to rebuild the containers, `make build` (you should need to do this rarely).

Tests are executed via `make test`. If you're switching between the Docker and Vagrant/VirtualBox environments and having trouble getting tests running, make sure to delete any remaining `.pyc` files and `__pycache__` directories.

To hop into the postgres container, you can do the following:

```shell
$ docker exec -it openoversight-postgres-1 bash
# psql -d openoversight-dev -U openoversight
```

or run `make attach`.

Similarly to hop into the web container:

```shell
$ docker exec -it openoversight-web-1 bash
```

Once you're done, `make stop` and `make clean` to stop and remove the containers respectively.

## Setting Up Email
OpenOversight tries to auto-detect which email implementation to use based on which of the following is configured (in this order):
* Google: `service_account_key.json` exists and is not empty
* SMTP: `MAIL_SERVER` and `MAIL_PORT` environment variables are set
* Simulated: If neither of the previous 2 implementations are configured, emails will only be logged

### GSuite
To send email using a GSuite email account, you will need a [Google Cloud Platform service account](https://cloud.google.com/iam/docs/service-account-overview) that is attached to that email address. Here are some general tips for working with service accounts: [Link](https://support.google.com/a/answer/7378726?hl=en).
We would suggest that you do not use a personal email address, but instead one that is used strictly for sending out OpenOversight emails.

You will need to do these two things for the service account to work as a Gmail bot:
1. Enable domain-wide delegation for the service account: [Link](https://support.google.com/a/answer/162106?hl=en)
2. Enable the `https://www.googleapis.com/auth/gmail.send` scope in the Gmail API for your service account: [Link](https://developers.google.com/gmail/api/auth/scopes#scopes)
3. Save the service account key file in OpenOversight's base folder as `service_account_key.json`. The file is in the `.gitignore` file GitHub will not allow you to save it, provided you've named it correctly.

### SMTP
To send email using SMTP, set the following environment variables in your docker-compose.yml file or .env file:
* `MAIL_SERVER`
* `MAIL_PORT`
* `MAIL_USE_TLS`
* `MAIL_USERNAME`
* `MAIL_PASSWORD`

For more information about these settings, please see the [Flask-Mail](https://flask-mail.readthedocs.io/en/latest/) documentation.

### Setting email aliases
Regardless of implementation, save the email address associated with your service account to a variable named `OO_SERVICE_EMAIL` in a `.env` file in the base directory of this repository. For development and testing, update the `OO_SERVICE_EMAIL` variable in the `docker-compose.yml` file.

Example `.env` variable:
```shell
OO_SERVICE_EMAIL="sample_email@domain.com"
```

In addition to needing a service account email, you also need an admin email address so that users have someone to reach out to if an action is taken on their account that needs to be reversed or addressed.
For production, save the email address associated with your admin account to a variable named `OO_HELP_EMAIL` in a `.env` file in the base directory of this repository. For development and testing, update the `OO_HELP_EMAIL` variable in the `docker-compose.yml` file.

Example `.env` variable:
```shell
OO_HELP_EMAIL="sample_admin_email@domain.com"
```

## Testing S3 Functionality
We use an S3 bucket for image uploads. If you are working on functionality involving image uploads,
then you should follow the "S3 Image Hosting" section in [DEPLOY.md](/DEPLOY.md) to make a test S3 bucket
on Amazon Web Services.

Once you have done this, you can put your AWS credentials in the following environmental variables:

```shell
$ export S3_BUCKET_NAME=openoversight-test
$ export AWS_ACCESS_KEY_ID=testtest
$ export AWS_SECRET_ACCESS_KEY=testtest
$ export AWS_DEFAULT_REGION=us-east-1
```

Now when you run `make dev` as usual in the same session, you will be able to submit images to
your test bucket.

## Database commands
Running `make dev` will create the database and persist it into your local filesystem.

You can access your PostgreSQL development database via psql using:

```shell
psql  -h localhost -d openoversight-dev -U openoversight --password
```

with the password `terriblepassword`.

In the event that you need to create or delete the test data, you can do that with
`$ python test_data.py --populate` to create the data
or
`$ python test_data.py --cleanup` to delete the data

Within the database we use [`timestamptz`](https://stackoverflow.com/a/48069726) fields for timestamps. To make sure that you are setting timestamps in the correct timezone, set the environment variable `TIMEZONE` to your respective [Olson-style timezone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#list) so that you can make sure any DST conversions are handled by PostgreSQL.

### Migrating the Database
You'll first have to start the Docker instance for the OpenOversight app using the command `make start`. To do this, you'll need to be in the base folder of the repository (the one that houses the `Makefile`).

```shell
$ make start
docker-compose build
...
docker-compose up -d
[+] Running 2/0
 ✔ Container openoversight-postgres-1  Running                                                                                                                                                             0.0s
 ✔ Container openoversight-web-1       Running
```

From here on out, we'll be using the Flask CLI. First we need to 'stamp' the current version of the database:

```shell
$ docker exec -it openoversight-web-1 bash # 'openoversight-web-1' is the name of the app container seen in the step above
$ flask db stamp head
$ flask db migrate -m "[THE NAME OF YOUR MIGRATION]" # NOTE: Slugs are limited to 40 characters and will be truncated after the limit
```

(Hint: If you get errors when running `flask` commands, e.g. because of differing Python versions, you may need to run the commands in the docker container by prefacing them as so: `docker exec -it openoversight_web_1 flask db stamp head`)

Next make your changes to the database models in `OpenOversight/app/models/database.py`. You'll then generate the migrations:

```shell
$ flask db migrate -m "[what does this migration do in all lower case"
```

And then you should inspect/edit the migrations. You can then apply the migrations:

```shell
$ flask db upgrade
```

You can also downgrade the database using:

```shell
flask db downgrade
```

## Using a Virtual Environment
One way to avoid hitting version incompatibility errors when running `flask` commands is to use a virtualenv.  See [Python Packaging user guidelines](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/) for instructions on installing virtualenv.  After installing virtualenv, you can create a virtual environment by navigating to the OpenOversight directory and running the below

```shell
python3 -m virtualenv env
```

Confirm you're in the virtualenv by running

```shell
which python
```

The response should point to your `env` directory.
If you want to exit the virtualenv, run

```shell
deactivate
```

To reactivate the virtualenv, run

```shell
source env/bin/activate
```

While in the virtualenv, you can install project dependencies by running

```shell
pip install -r requirements.txt
```

and

```shell
pip install -r dev-requirements.txt
```

## OpenOversight Management Interface
In addition to generating database migrations, the Flask CLI can be used to run additional commands:

```shell
$ flask --help
Usage: flask [OPTIONS] COMMAND [ARGS]...

  A general utility script for Flask applications.

  Provides commands from Flask, extensions, and the application. Loads the
  application defined in the FLASK_APP environment variable, or from a
  wsgi.py file. Setting the ENV environment variable to 'development'
  will enable debug mode.

    $ export FLASK_APP=hello.py
    $ export ENV=development
    $ flask run

Options:
  --version  Show the flask version
  --help     Show this message and exit.

Commands:
  bulk-add-officers            Bulk adds officers.
  db                           Perform database migrations.
  link-images-to-department    Link existing images to first department
  link-officers-to-department  Links officers and units to first department
  make-admin-user              Add confirmed administrator account
  routes                       Show the routes for the app.
  run                          Runs a development server.
  shell                        Runs a shell in the app context.
```

In development, you can make an administrator account without having to confirm your email:

```shell
$ flask make-admin-user
Username: redshiftzero
Email: jen@redshiftzero.com
Password:
Type your password again:
Administrator redshiftzero successfully added
```

## Debugging OpenOversight - Use pdb with the app itself
In `docker-compose.yml`, below the line specifying the port number, add the following lines to the `web` service:
```yml
   stdin_open: true
   tty: true
```
Also in `docker-compose.yml`, below the line specifying the `ENV`, add the following to the `environment` portion of the `web` service:
```yml
  FLASK_DEBUG: 0
```
The above line disables the werkzeug reloader, which can otherwise cause a bug when you place a breakpoint in code that loads at import time, such as classes.  The werkzeug reloader will start one pdb process at import time and one when you navigate to the class.  This makes it impossible to interact with the pdb prompt, but we can fix it by disabling the reloader.

To set a breakpoint in OpenOversight, first import the pdb module by adding `import pdb` to the file you want to debug.  Call `pdb.set_trace()` on its own line wherever you want to break for debugging.
Next, in your terminal run `docker ps` to find the container id of the `openoversight_web` image, then run `docker attach ${container_id}` to connect to the debugger in your terminal.  You can now use pdb prompts to step through the app.

## Debugging OpenOversight - Use pdb with a test
If you want to run an individual test in debug mode, use the below command.
```shell
docker-compose run --rm web pytest --pdb -v tests/ -k <test_name_here>
```

where `<test_name_here>` is the name of a single test function, such as `test_ac_cannot_add_new_officer_not_in_their_dept`

Similarly, you can run all the tests in a file by specifying the file path:

```shell
docker-compose run --rm web pytest --pdb -v path/to/test/file
```

where `path/to/test/file` is the relative file path, minus the initial `OpenOversight`, such as
`tests/routes/test_officer_and_department.py`.

Again, add `import pdb` to the file you want to debug, then write `pdb.set_trace()` wherever you want to drop a breakpoint.  Once the test is up and running in your terminal, you can debug it using pdb prompts.
