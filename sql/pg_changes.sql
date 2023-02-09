ALTER TABLE members
    ADD COLUMN password_type TEXT;
ALTER TABLE members
    ADD COLUMN encoded_password TEXT;
