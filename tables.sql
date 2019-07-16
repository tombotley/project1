CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    user_email VARCHAR NOT NULL,
    user_username VARCHAR NOT NULL,
    user_hashpw VARCHAR NOT NULL
);

CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY,
    review_rating INTEGER NOT NULL,
    review_text VARCHAR,
    user_id INTEGER REFERENCES users,
    book_id INTEGER REFERENCES books
);