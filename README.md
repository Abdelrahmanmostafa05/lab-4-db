# Lab 4 - Search Queries in SQL

Introduction to Database Systems - Fall 2026

## Requirements
- MySQL Server
- Python 3.10+
- MySQL Workbench (optional, for importing and inspecting the database)

## Folder
```
app.py                                                         (Flask application)
problem2_DDL.sql / problem2_DML.sql / problem2_Queries.sql     (Problem 2 - library)
requirements.txt                                               (Python dependencies)
website/templates/                                             (HTML templates)
website/static/style.css                                       (Stylesheet)
```

## Run the project on Windows
1. In MySQL Workbench, connect to your MySQL Server, open `problem2_DDL.sql`, and execute it. This drops and recreates the `library` database.
2. Open and execute `problem2_DML.sql` to insert the sample data.
3. In PowerShell, from the project folder, install the Python packages into your system Python:
   ```powershell
   py -m pip install -r .\requirements.txt
   ```
4. Start the website; it will prompt for your MySQL password without displaying it:
   ```powershell
   py .\app.py
   ```
   Alternatively, set credentials in the same PowerShell window before starting the website:
   ```powershell
   $env:DB_HOST = "localhost"
   $env:DB_USER = "root"
   $env:DB_PASS = "your_mysql_password"
   ```
   Then run `py .\app.py`.
   Keep the password private; do not save it in source files.
5. Open http://localhost:8000 in your browser. Keep the PowerShell window open while using the site.

## Add or edit books and authors
- Open **Manage** in the website navigation.
- Use the forms to add or edit a book or author. Existing entries have an **Edit** link.
- Use **Delete** beside an entry to remove it. Deleting a book also deletes its loan records; deleting an author deletes all of that author's books and their loan records. The website asks for confirmation first.
- The **Categories** list on the Manage page lets you delete categories that are not assigned to any books. Reassign or delete a category's books before deleting that category.
- In the book form, type or select an author, publisher, and category. Names not already in the lists are created automatically when the book is saved.
- Country fields are optional and are used only when creating a new author or publisher.

## Pages
| Page | URL | SQL used |
|------|------|----------|
| F2.1 Search books | `/search` | LIKE, BETWEEN, ORDER BY (parameterized query) |
| F2.2 Catalogue | `/catalogue` | JOIN of 4 tables |
| F2.3 Reports | `/reports` | GROUP BY, HAVING, aggregates |
| F2.4 Loans | `/loans` | JOIN, LEFT JOIN + IS NULL |
| F2.5 Most borrowed | `/most-borrowed` | GROUP BY, ORDER BY, LIMIT |
| F2.6 Authors and books | `/authors` | LEFT JOIN, JOIN |
| Manage collection | `/manage` | Add, edit, and delete books and authors; delete unused categories |
