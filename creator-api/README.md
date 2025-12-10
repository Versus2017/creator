Install [`pipenv`](https://pipenv.readthedocs.io/en/latest/) with `pip install --user pipenv` or `brew install pipenv`.

```shell

cd creator/creator-api

# create virtual env & install dependencies
make install

# active venv
pipenv shell

# create local_config.py if it's not exists
# creator-api/creator/local_config.py
JWT_SECRET_KEY = 'jwt_secret_key'
JWT_COOKIE_SECURE = False
SECRET_KEY = 'secret_key'

# create db
createdb creator 

# migrate db
make upgrade-db


# initial testing user & role

# create role admin
python ./creator/cli.py bo_create_role -n admin

# create user admin
python ./creator/cli.py bo_create_user -n admin

# assign admin role to admin user
python ./creator/cli.py bo_set_role -u admin -r admin

# assign permissions for role admin
python ./creator/cli.py bo_set_perm -r admin -p all


# run in dev mode
make run

# run test
make test

```
Translations(Optionally)

-   init babel: `make babel-init LANG=zh`
-   mark translation strings with [gettext](https://docs.python.org/3/library/gettext.html#gettext) functions
-   extract translation strings: `make babel-update`
-   update translations and finally compile them for use: `make babel-compile`
