alter table members alter column rfid drop not null;
alter table members add column mms_id TEXT UNIQUE;
alter table members drop constraint "bodgery_rfid_full_name_key";
