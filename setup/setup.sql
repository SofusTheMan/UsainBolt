DROP TABLE IF EXISTS runs;
DROP TABLE IF EXISTS users;



CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username_lower VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(255) NOT NULL,
    profile_picture BYTEA,
    profile_picture_mime VARCHAR(50)
);

CREATE TABLE runs (
    run_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    description TEXT,
    time_seconds FLOAT NOT NULL,
    run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    video_data BYTEA,
    video_mime VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);



