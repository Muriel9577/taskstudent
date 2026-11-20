DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    pass_score REAL NOT NULL DEFAULT 0 CHECK (pass_score >= 0)
);

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    deadline TEXT,
    max_score REAL NOT NULL CHECK (max_score > 0),
    status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'done')),
    score REAL CHECK (score IS NULL OR (score >= 0 AND score <= max_score))
);
