ALTER TABLE members ADD COLUMN password_type TEXT;
ALTER TABLE members ADD COLUMN encoded_password TEXT;
ALTER TABLE members ADD COLUMN username TEXT;


CREATE TABLE roles (
    id SERIAL PRIMARY KEY NOT NULL,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE role_members (
    member_id INT REFERENCES members (id),
    role_id INT REFERENCES roles (id),

    PRIMARY KEY( member_id, role_id )
);
CREATE INDEX ON role_members (member_id);
CREATE INDEX ON role_members (role_id);

CREATE TABLE permissions (
    id SERIAL PRIMARY KEY NOT NULL,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE role_permissions (
    role_id INT REFERENCES roles (id),
    permission_id INT REFERENCES permissions(id),

    PRIMARY KEY( role_id, permission_id )
);
CREATE INDEX ON role_permissions (role_id);
CREATE INDEX ON role_permissions (permission_id);
