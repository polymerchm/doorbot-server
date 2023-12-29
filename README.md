# Bodgery Access Control

Backend and management interface for setting access control for Bodgery keyfobs.

## Setup

* Create a new PostgreSQL database named `bodgery_members`
* Against that database, create the tables by running the SQL in `sql/pg.sql`
** Example: `psql -f sql/pg.sql bodgery_members`
* Copy `config.yml.example` to `config.yml`
* Edit `config.yml`. In particular, modify:
** Database credentials under `postgresql`
** Session cookie key in `session.key` (see command in the example doc)
* Run tests with `./all_tests.sh`
* Start with `flask run`
* Create a new user in PostgreSQL using the `psql` command
** Run something like: 

```
INSERT INTO members (
    full_name,
    rfid,
    username,
    password_type,
    encoded_password,
    phone,
    email,
    entry_type,
)
VALUES (
    'Timm Murray',
    '1234',
    'tmurray',
    'plaintext',
    'Foobar123',
    '',
    '',
    ''
);
```

Replacing the values as you see fit

* You should now be able to login with the browser frontend
