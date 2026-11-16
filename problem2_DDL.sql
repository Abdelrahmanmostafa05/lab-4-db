-- ============================================================
-- Problem 2 : Library database (DDL)
-- Run: mysql -u root -p < problem2_DDL.sql
-- ============================================================
DROP DATABASE IF EXISTS library;
CREATE DATABASE library CHARACTER SET utf8mb4;
USE library;

CREATE TABLE author (
    author_id INT          AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(100) NOT NULL,
    country   VARCHAR(50)
);

CREATE TABLE publisher (
    publisher_id INT          AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    country      VARCHAR(50)
);

CREATE TABLE category (
    category_id INT          AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(50)  NOT NULL
);

CREATE TABLE book (
    book_id      INT           AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(150)  NOT NULL,
    price        DECIMAL(8,2)  NOT NULL,
    publish_year INT,
    author_id    INT           NOT NULL,
    publisher_id INT           NOT NULL,
    category_id  INT           NOT NULL,
    -- deleting an author deletes all of his/her books (as in Lab 3)
    FOREIGN KEY (author_id)    REFERENCES author(author_id)       ON DELETE CASCADE,
    FOREIGN KEY (publisher_id) REFERENCES publisher(publisher_id),
    FOREIGN KEY (category_id)  REFERENCES category(category_id)
);

CREATE TABLE `member` (
    member_id INT          AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(100) NOT NULL,
    email     VARCHAR(100) UNIQUE,
    join_date DATE
);

CREATE TABLE loan (
    loan_id     INT  AUTO_INCREMENT PRIMARY KEY,
    book_id     INT  NOT NULL,
    member_id   INT  NOT NULL,
    loan_date   DATE NOT NULL,
    return_date DATE NULL,                -- NULL = still borrowed
    -- deleting a book deletes its loans
    FOREIGN KEY (book_id)   REFERENCES book(book_id)       ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES `member`(member_id)
);
