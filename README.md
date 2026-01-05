


## get it all running
1. make sure you have a proper .env file
2. run docker compose up -d
3. create an inital user for the database

INSERT INTO admin_users (username, email, hashed_password, is_active, is_superuser, created_at)
VALUES (
    'admin',
    'admin@example.com',
    '$2b$12$YOUR_HASH_HERE',  -- Replace with hashed password (bcrypt) 
    true,
    true,
    NOW()
);

4. it runs at /docs/ 