import getpass
import hmac
import os
import re
import secrets
from decimal import Decimal, InvalidOperation

import mysql.connector
from flask import Flask, abort, redirect, render_template, request, session, url_for


app = Flask(
    __name__,
    template_folder="website/templates",
    static_folder="website/static",
)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.urandom(32)


def _connect_database():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", "Body_2005#"),
        database=os.getenv("DB_NAME", "library"),
        connection_timeout=5,
    )


def query_all(sql: str, params: tuple = ()) -> list[dict]:
    connection = _connect_database()
    try:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, params)
            return cursor.fetchall()
        finally:
            cursor.close()
    finally:
        connection.close()


def execute_write(sql: str, params: tuple = ()) -> int:
    connection = _connect_database()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(sql, params)
            connection.commit()
            return cursor.lastrowid
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
    finally:
        connection.close()


def save_book_record(
    title: str,
    price: Decimal,
    year: int | None,
    author_name: str,
    author_country: str,
    publisher_name: str,
    publisher_country: str,
    category_name: str,
    book_id: int | None,
) -> None:
    connection = _connect_database()
    try:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT author_id FROM author
                   WHERE LOWER(name) = LOWER(%s)
                   ORDER BY author_id LIMIT 1""",
                (author_name,),
            )
            author = cursor.fetchone()
            if author:
                author_id = author["author_id"]
            else:
                cursor.execute(
                    "INSERT INTO author (name, country) VALUES (%s, %s)",
                    (author_name, author_country or None),
                )
                author_id = cursor.lastrowid

            cursor.execute(
                """SELECT publisher_id FROM publisher
                   WHERE LOWER(name) = LOWER(%s)
                   ORDER BY publisher_id LIMIT 1""",
                (publisher_name,),
            )
            publisher = cursor.fetchone()
            if publisher:
                publisher_id = publisher["publisher_id"]
            else:
                cursor.execute(
                    "INSERT INTO publisher (name, country) VALUES (%s, %s)",
                    (publisher_name, publisher_country or None),
                )
                publisher_id = cursor.lastrowid

            cursor.execute(
                """SELECT category_id FROM category
                   WHERE LOWER(name) = LOWER(%s)
                   ORDER BY category_id LIMIT 1""",
                (category_name,),
            )
            category = cursor.fetchone()
            if category:
                category_id = category["category_id"]
            else:
                cursor.execute(
                    "INSERT INTO category (name) VALUES (%s)",
                    (category_name,),
                )
                category_id = cursor.lastrowid

            values = (
                title,
                price,
                year,
                author_id,
                publisher_id,
                category_id,
            )
            if book_id:
                cursor.execute(
                    """UPDATE book
                       SET title = %s, price = %s, publish_year = %s,
                           author_id = %s, publisher_id = %s, category_id = %s
                       WHERE book_id = %s""",
                    (*values, book_id),
                )
            else:
                cursor.execute(
                    """INSERT INTO book
                       (title, price, publish_year, author_id, publisher_id, category_id)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    values,
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
    finally:
        connection.close()


def _csrf_token() -> str:
    token = session.get("csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def _validate_csrf() -> None:
    token = request.form.get("csrf_token", "")
    expected = session.get("csrf_token", "")
    if not expected or not hmac.compare_digest(token, expected):
        abort(400, description="This form expired. Reload the page and try again.")


def _parse_price(value: str) -> Decimal | None:
    if not value:
        return None
    try:
        price = Decimal(value)
    except InvalidOperation:
        return None
    return price if price.is_finite() else None


@app.route("/")
def index():
    return render_template("index.html", title="Library")


@app.route("/search")
def search():
    keyword = request.args.get("keyword", "").strip()
    minimum = request.args.get("min", "")
    maximum = request.args.get("max", "")
    category = request.args.get("category", "")
    categories = query_all(
        "SELECT category_id, name FROM category ORDER BY name"
    )

    min_price = _parse_price(minimum)
    max_price = _parse_price(maximum)
    search_error = None
    if minimum and min_price is None:
        search_error = "Enter a valid minimum price."
    elif maximum and max_price is None:
        search_error = "Enter a valid maximum price."
    elif min_price is not None and max_price is not None and min_price > max_price:
        search_error = "Minimum price must be less than or equal to maximum price."
    elif category and not re.fullmatch(r"\d+", category):
        search_error = "Choose a valid category."

    books = []
    if search_error is None:
        sql = """
            SELECT b.book_id, b.title, b.price, b.publish_year, c.name AS category
            FROM book b
            JOIN category c ON b.category_id = c.category_id
            WHERE b.title LIKE %s
              AND b.price BETWEEN %s AND %s
        """
        params = [
            f"%{keyword}%",
            str(min_price) if min_price is not None else "0",
            str(max_price) if max_price is not None else "999999.99",
        ]
        if category:
            sql += " AND b.category_id = %s"
            params.append(int(category))
        sql += " ORDER BY b.price ASC"
        books = query_all(sql, tuple(params))

    return render_template(
        "search.html",
        title="F2.1 Search books",
        keyword=keyword,
        minimum=minimum,
        maximum=maximum,
        selected_category=category,
        categories=categories,
        rows=books,
        search_error=search_error,
    )


@app.route("/catalogue")
def catalogue():
    rows = query_all("""
        SELECT b.book_id, b.title, b.price, b.publish_year,
               a.name AS author, p.name AS publisher, c.name AS category
        FROM book b
        JOIN author a ON b.author_id = a.author_id
        JOIN publisher p ON b.publisher_id = p.publisher_id
        JOIN category c ON b.category_id = c.category_id
        ORDER BY b.book_id
    """)
    return render_template("catalogue.html", title="F2.2 Catalogue", rows=rows)


def _manage_page(
    *,
    book_draft: dict | None = None,
    author_draft: dict | None = None,
    error: str | None = None,
    status: int = 200,
):
    authors_list = query_all(
        "SELECT author_id, name, country FROM author ORDER BY name"
    )
    publishers = query_all(
        "SELECT publisher_id, name FROM publisher ORDER BY name"
    )
    categories = query_all(
        """SELECT c.category_id, c.name, COUNT(b.book_id) AS book_count
           FROM category c
           LEFT JOIN book b ON b.category_id = c.category_id
           GROUP BY c.category_id, c.name
           ORDER BY c.name"""
    )
    books = query_all("""
        SELECT b.book_id, b.title, b.price, b.publish_year,
               a.name AS author, p.name AS publisher, c.name AS category
        FROM book b
        JOIN author a ON b.author_id = a.author_id
        JOIN publisher p ON b.publisher_id = p.publisher_id
        JOIN category c ON b.category_id = c.category_id
        ORDER BY b.title
    """)
    return render_template(
        "manage.html",
        title="Manage the collection",
        authors=authors_list,
        publishers=publishers,
        categories=categories,
        books=books,
        book_draft=book_draft or {},
        author_draft=author_draft or {},
        error=error,
        saved=request.args.get("saved"),
        deleted=request.args.get("deleted"),
        csrf_token=_csrf_token(),
    ), status


@app.route("/manage")
def manage():
    book_draft = None
    author_draft = None
    book_id = request.args.get("edit_book", "")
    author_id = request.args.get("edit_author", "")

    if book_id:
        if not re.fullmatch(r"\d+", book_id):
            abort(404)
        rows = query_all(
            """SELECT b.book_id, b.title, b.price, b.publish_year,
                      a.name AS author_name, a.country AS author_country,
                      p.name AS publisher_name, p.country AS publisher_country,
                      c.name AS category_name
               FROM book b
               JOIN author a ON a.author_id = b.author_id
               JOIN publisher p ON p.publisher_id = b.publisher_id
               JOIN category c ON c.category_id = b.category_id
               WHERE b.book_id = %s""",
            (int(book_id),),
        )
        if not rows:
            abort(404)
        book_draft = rows[0]

    if author_id:
        if not re.fullmatch(r"\d+", author_id):
            abort(404)
        rows = query_all(
            "SELECT author_id, name, country FROM author WHERE author_id = %s",
            (int(author_id),),
        )
        if not rows:
            abort(404)
        author_draft = rows[0]

    return _manage_page(book_draft=book_draft, author_draft=author_draft)


@app.route("/manage/books", methods=["POST"])
def save_book():
    _validate_csrf()
    raw_id = request.form.get("book_id", "").strip()
    title = request.form.get("title", "").strip()
    raw_price = request.form.get("price", "").strip()
    raw_year = request.form.get("publish_year", "").strip()
    author_name = request.form.get("author_name", "").strip()
    author_country = request.form.get("author_country", "").strip()
    publisher_name = request.form.get("publisher_name", "").strip()
    publisher_country = request.form.get("publisher_country", "").strip()
    category_name = request.form.get("category_name", "").strip()

    errors = []
    price = _parse_price(raw_price)
    if not title or len(title) > 150:
        errors.append("Enter a book title between 1 and 150 characters.")
    if not author_name or len(author_name) > 100:
        errors.append("Enter an author name between 1 and 100 characters.")
    if len(author_country) > 50:
        errors.append("Author country must be 50 characters or fewer.")
    if not publisher_name or len(publisher_name) > 100:
        errors.append("Enter a publisher name between 1 and 100 characters.")
    if len(publisher_country) > 50:
        errors.append("Publisher country must be 50 characters or fewer.")
    if not category_name or len(category_name) > 50:
        errors.append("Enter a category name between 1 and 50 characters.")
    if (
        price is None
        or price < 0
        or price > Decimal("999999.99")
        or price.as_tuple().exponent < -2
    ):
        errors.append("Enter a price from 0 to 999999.99 with at most two decimal places.")

    year = None
    if raw_year:
        if not re.fullmatch(r"\d{1,4}", raw_year):
            errors.append("Enter a publication year between 0 and 9999.")
        else:
            year = int(raw_year)

    existing_book_id = None
    if raw_id:
        if re.fullmatch(r"\d+", raw_id) and int(raw_id) > 0:
            existing_book_id = int(raw_id)
            if not query_all(
                "SELECT book_id FROM book WHERE book_id = %s",
                (existing_book_id,),
            ):
                abort(404)
        else:
            errors.append("The book selection is invalid.")

    if errors:
        return _manage_page(
            book_draft={
                "book_id": existing_book_id or "",
                "title": title,
                "price": raw_price,
                "publish_year": raw_year,
                "author_name": author_name,
                "author_country": author_country,
                "publisher_name": publisher_name,
                "publisher_country": publisher_country,
                "category_name": category_name,
            },
            error=" ".join(errors),
            status=400,
        )

    save_book_record(
        title,
        price,
        year,
        author_name,
        author_country,
        publisher_name,
        publisher_country,
        category_name,
        existing_book_id,
    )
    return redirect(url_for("manage", saved="book"))


@app.route("/manage/authors", methods=["POST"])
def save_author():
    _validate_csrf()
    raw_id = request.form.get("author_id", "").strip()
    name = request.form.get("name", "").strip()
    country = request.form.get("country", "").strip()
    errors = []

    if not name or len(name) > 100:
        errors.append("Enter an author name between 1 and 100 characters.")
    if len(country) > 50:
        errors.append("Country must be 50 characters or fewer.")

    existing_author_id = None
    if raw_id:
        if re.fullmatch(r"\d+", raw_id) and int(raw_id) > 0:
            existing_author_id = int(raw_id)
            if not query_all(
                "SELECT author_id FROM author WHERE author_id = %s",
                (existing_author_id,),
            ):
                abort(404)
        else:
            errors.append("The author selection is invalid.")

    if errors:
        return _manage_page(
            author_draft={
                "author_id": existing_author_id or "",
                "name": name,
                "country": country,
            },
            error=" ".join(errors),
            status=400,
        )

    if existing_author_id:
        execute_write(
            "UPDATE author SET name = %s, country = %s WHERE author_id = %s",
            (name, country or None, existing_author_id),
        )
    else:
        execute_write(
            "INSERT INTO author (name, country) VALUES (%s, %s)",
            (name, country or None),
        )
    return redirect(url_for("manage", saved="author"))


@app.route("/manage/books/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id: int):
    _validate_csrf()
    if not query_all("SELECT book_id FROM book WHERE book_id = %s", (book_id,)):
        abort(404)
    execute_write("DELETE FROM book WHERE book_id = %s", (book_id,))
    return redirect(url_for("manage", deleted="book"))


@app.route("/manage/authors/<int:author_id>/delete", methods=["POST"])
def delete_author(author_id: int):
    _validate_csrf()
    author = query_all(
        "SELECT author_id FROM author WHERE author_id = %s",
        (author_id,),
    )
    if not author:
        abort(404)
    execute_write("DELETE FROM author WHERE author_id = %s", (author_id,))
    return redirect(url_for("manage", deleted="author"))


@app.route("/manage/categories/<int:category_id>/delete", methods=["POST"])
def delete_category(category_id: int):
    _validate_csrf()
    category = query_all(
        "SELECT category_id FROM category WHERE category_id = %s",
        (category_id,),
    )
    if not category:
        abort(404)

    books = query_all(
        "SELECT COUNT(*) AS book_count FROM book WHERE category_id = %s",
        (category_id,),
    )
    if books[0]["book_count"]:
        return _manage_page(
            error="This category is in use. Reassign or delete its books before deleting the category.",
            status=400,
        )

    execute_write("DELETE FROM category WHERE category_id = %s", (category_id,))
    return redirect(url_for("manage", deleted="category"))


@app.route("/reports")
def reports():
    category_report = query_all("""
        SELECT c.name AS category, COUNT(b.book_id) AS books,
               ROUND(AVG(b.price), 2) AS average_price
        FROM category c
        LEFT JOIN book b ON b.category_id = c.category_id
        GROUP BY c.category_id, c.name
    """)
    author_report = query_all("""
        SELECT a.name AS author, COUNT(*) AS books
        FROM author a
        JOIN book b ON b.author_id = a.author_id
        GROUP BY a.author_id, a.name
        HAVING COUNT(*) >= 2
    """)
    price_report = query_all("""
        SELECT SUM(price) AS total_price, MIN(price) AS smallest_price,
               MAX(price) AS largest_price
        FROM book
    """)
    return render_template(
        "reports.html",
        title="F2.3 Reports",
        category_report=category_report,
        author_report=author_report,
        price_report=price_report,
    )


@app.route("/loans")
def loans():
    open_loans = query_all("""
        SELECT l.loan_id, b.title AS book, m.name AS member, l.loan_date
        FROM loan l
        JOIN book b ON l.book_id = b.book_id
        JOIN `member` m ON l.member_id = m.member_id
        WHERE l.return_date IS NULL
    """)
    members_without_loans = query_all("""
        SELECT m.member_id, m.name, m.email
        FROM `member` m
        LEFT JOIN loan l ON l.member_id = m.member_id
        WHERE l.loan_id IS NULL
    """)
    books_without_loans = query_all("""
        SELECT b.book_id, b.title
        FROM book b
        LEFT JOIN loan l ON l.book_id = b.book_id
        WHERE l.loan_id IS NULL
    """)
    return render_template(
        "loans.html",
        title="F2.4 Loans",
        open_loans=open_loans,
        members_without_loans=members_without_loans,
        books_without_loans=books_without_loans,
    )


@app.route("/most-borrowed")
def most_borrowed():
    books = query_all("""
        SELECT b.title, COUNT(*) AS loans
        FROM book b
        JOIN loan l ON l.book_id = b.book_id
        GROUP BY b.book_id, b.title
        ORDER BY loans DESC, b.title
        LIMIT 3
    """)
    members = query_all("""
        SELECT m.name, COUNT(*) AS loans
        FROM `member` m
        JOIN loan l ON l.member_id = m.member_id
        GROUP BY m.member_id, m.name
        ORDER BY loans DESC, m.name
        LIMIT 1
    """)
    return render_template(
        "most_borrowed.html",
        title="F2.5 Most borrowed",
        books=books,
        members=members,
    )


@app.route("/authors")
def authors():
    author_counts = query_all("""
        SELECT a.name AS author, COUNT(b.book_id) AS books
        FROM author a
        LEFT JOIN book b ON b.author_id = a.author_id
        GROUP BY a.author_id, a.name
        ORDER BY books DESC, a.name
    """)
    matching_countries = query_all("""
        SELECT b.title, a.name AS author, p.name AS publisher, a.country
        FROM book b
        JOIN author a ON b.author_id = a.author_id
        JOIN publisher p ON b.publisher_id = p.publisher_id
        WHERE a.country = p.country
    """)
    return render_template(
        "authors.html",
        title="F2.6 Authors and books",
        author_counts=author_counts,
        matching_countries=matching_countries,
    )


@app.errorhandler(mysql.connector.Error)
def handle_database_error(error):
    app.logger.exception("Database request failed: %s", error)
    return render_template(
        "database_error.html",
        title="Database connection problem",
    ), 503


if __name__ == "__main__":
    if "DB_PASS" not in os.environ:
        os.environ["DB_PASS"] = getpass.getpass("MySQL password: ")
    app.run(host="127.0.0.1", port=8000, debug=False)
