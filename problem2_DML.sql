-- ============================================================
-- Problem 2 : Library database (seed data)
-- Run: mysql -u root -p < problem2_DML.sql
-- ============================================================
USE library;

-- 5 authors: two from Egypt, one UK, one Brazil, one with NO books (Murakami)
INSERT INTO author (author_id, name, country) VALUES
(1, 'Naguib Mahfouz',  'Egypt'),
(2, 'Taha Hussein',    'Egypt'),
(3, 'George Orwell',   'UK'),
(4, 'Paulo Coelho',    'Brazil'),
(5, 'Haruki Murakami', 'Japan');

-- 3 publishers: Egypt and UK match author countries
INSERT INTO publisher (publisher_id, name, country) VALUES
(1, 'Dar El Shorouk', 'Egypt'),
(2, 'Penguin Books',  'UK'),
(3, 'HarperCollins',  'USA');

-- 3 categories
INSERT INTO category (category_id, name) VALUES
(1, 'Novel'),
(2, 'History'),
(3, 'Philosophy');

-- 10 books
-- price 15..20  : books 1, 4, 7, 8, 9
-- never borrowed: books 3, 4, 10
-- author with >=2 books: Mahfouz (4), Orwell (3), Coelho (2)
INSERT INTO book (book_id, title, price, publish_year, author_id, publisher_id, category_id) VALUES
(1,  'Palace Walk',            18.50, 1956, 1, 1, 1),
(2,  'Sugar Street',           22.00, 1957, 1, 1, 1),
(3,  'Children of the Alley',  25.00, 1959, 1, 2, 1),
(4,  'Midaq Alley',            15.50, 1947, 1, 1, 1),
(5,  'The Days',               14.00, 1929, 2, 1, 2),
(6,  'Animal Farm',            12.50, 1945, 3, 2, 1),
(7,  '1984',                   19.99, 1949, 3, 2, 1),
(8,  'Homage to Catalonia',    16.75, 1938, 3, 2, 2),
(9,  'The Alchemist',          17.75, 1988, 4, 3, 3),
(10, 'Brida',                  21.00, 1990, 4, 3, 3);

-- 5 members: member 5 has NO loans
INSERT INTO `member` (member_id, name, email, join_date) VALUES
(1, 'Ahmed Hassan',  'ahmed@example.com',  '2026-01-10'),
(2, 'Mona Ali',      'mona@example.com',   '2026-02-15'),
(3, 'Omar Khaled',   'omar@example.com',   '2026-03-20'),
(4, 'Sara Mostafa',  'sara@example.com',   '2026-05-05'),
(5, 'Youssef Adel',  'youssef@example.com','2026-06-30');

-- 12 loans: loans 5, 9, 11 are NOT returned yet (return_date = NULL)
INSERT INTO loan (loan_id, book_id, member_id, loan_date, return_date) VALUES
(1,  1, 1, '2026-09-01', '2026-09-10'),
(2,  1, 2, '2026-09-12', '2026-09-20'),
(3,  1, 3, '2026-10-01', '2026-10-09'),
(4,  7, 1, '2026-09-05', '2026-09-15'),
(5,  7, 2, '2026-10-03', NULL),
(6,  7, 4, '2026-10-15', '2026-10-25'),
(7,  6, 1, '2026-09-20', '2026-09-28'),
(8,  2, 2, '2026-10-05', '2026-10-14'),
(9,  9, 3, '2026-10-10', NULL),
(10, 2, 3, '2026-10-20', '2026-10-28'),
(11, 5, 4, '2026-11-01', NULL),
(12, 8, 2, '2026-11-03', '2026-11-10');
