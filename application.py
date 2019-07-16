import os
import json
import requests

from flask import Flask, session, render_template, url_for, request, flash, redirect, abort, jsonify # have I used all of these?
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

from helpers import login_required

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    """ default app route """
    
    # render the index welcome page
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """ request registration details, hash password, check not already registered, username unique and passwords match, add to user table """
    
    # error message variable declaration
    error = None
    
    # when user posts registration details from form on register.html run this code
    if request.method == "POST":
        
        # request registration form data values
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        passwordcheck = request.form.get("passwordcheck")
        
        # hash the given password, salt length will be default value 8
        hashed_password = generate_password_hash(password, "sha256")
        
        # check if a row exists with given email address, update error message if so
        if db.execute("SELECT * FROM users WHERE user_email = :email", {"email": email}).rowcount == 1:
            error = 'This email address is already registered.'
        
        # check if a row exists with given username, update error message if so
        elif db.execute("SELECT * FROM users WHERE user_username = :username", {"username": username}).rowcount == 1:
            error = 'This username is already in use. Please choose an alternative.'
        
        # check if the password and password confirmation values given by user match, update error message if so
        elif not password == passwordcheck:
            error = 'Passwords do not match. Please try again.'
        
        # if all error checks succeed then insert user details into the users table and redirect user to login 
        else:
            db.execute("INSERT INTO users (user_email, user_username, user_hashpw) VALUES (:email, :username, :hashed_password)", {"email": email, "username": username, "hashed_password": hashed_password})
            db.commit()
            flash('Registration complete! Please login.')
            return redirect(url_for('login'))
    
    # get request for register, render the registration page with the relevant error string if a previous attempt failed
    return render_template("register.html", error=error)
 
    
@app.route("/login", methods=["GET", "POST"])
def login():
    """ request username and pw, check if registered and password correct, update session variable """
    
    # error message variable declaration
    error = None
    
    # when user posts login details from form on login.html run this code
    if request.method == "POST":
        
        # request login form data values
        username = request.form.get("username")
        password = request.form.get("password")
        
        # select user hashed password from users tables where username matches given username
        user = db.execute("SELECT user_hashpw FROM users WHERE user_username = :username", {"username": username}).fetchone()
        
        # if no user is found or password check fails update error message
        if user is None or check_password_hash(user.user_hashpw, password) is False:
            error = 'Username or password incorrect. Please try again or register.'
        
        # if checks succeed update session variable "username" (for later logged in status check) and redirect user to search 
        else:
            session["username"] = username
            return redirect(url_for('search'))
    
    # get request for login, render the login page with error message if a previous attempt failed
    return render_template("login.html", error=error)
    
    
@app.route("/logout")
@login_required
def logout():
    """ clear the username session variable and render the logout confirmation page """
    
    # route redirects to login if login_required returns false 
    
    # update username session variable and render the logged out confirmation page
    session.pop("username", None)
    return render_template("logout.html")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """ request search value and use to query books table """
    
    # route redirects to login if login_required returns false 
    
    # error message variable declaration
    error = None
    
    # when user posts search value from form on search.html run this code
    if request.method == "POST":
        
        # request search from data value
        search_value = request.form.get("search_value")
        
        # add wildcard symbols to search value so partial matches can be found
        wild_value = "%" + search_value + "%"

        # query books table with the search value for any matches in the isbn, title or author fields
        results = db.execute("SELECT * FROM books WHERE book_isbn ILIKE :wild_value OR book_title ILIKE :wild_value OR book_author ILIKE :wild_value", {"wild_value": wild_value}).fetchall()

        # if length (no. of rows) of results is 0 then update error message
        if len(results) == 0:
            error = 'No search results found.'
        
        # else render the results page, passing the query results
        else:
            return render_template("results.html", results=results)
    
    # get request for search, render the search page with error message if a previous search found no matches
    return render_template("search.html", error=error)
       
    
@app.route("/book/<isbn>", methods=["GET", "POST"])
@login_required
def book(isbn):
    """ display book details for the given isbn (incl. Goodreads rating info) and any user reviews, allow current user to add review """
    
    # route redirects to login if login_required returns false
    
    # review count and avergae variable declarations
    rev_count = None
    rev_avg = None
    
    # if route receives posted form data which includes "review" then run this code
    if "review" in request.form:
        
        # request review form data values
        review = request.form.get("review")
        rating = request.form.get("rating")
        
        # select the book_id where book_isbn matches this function's isbn parameter value, to be used for later insert
        book = db.execute("SELECT book_id FROM books WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()
        
        # select the user_id for the session user, to be used for later insert
        user = db.execute("SELECT user_id FROM users WHERE user_username = :username", {"username": session["username"]}).fetchone()
        
        # insert review into reviews table
        db.execute("INSERT INTO reviews (review_text, review_rating, user_id, book_id) VALUES (:review, :rating, :user, :book)", {"review": review, "rating": rating, "user": user[0], "book": book[0]})
        db.commit()
        
        # redirect user to page confirming review has been submitted
        return redirect(url_for('submitted'))
    
    # select details for book with ISBN matching this functions isbn parameter value
    book = db.execute("SELECT book_isbn, book_title, book_author, book_year FROM books WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()
    
    # if query returns none then isbn was not found in books table, render error page with given message 
    if book is None:
        return render_template("error.html", message="ISBN not found.")
    
    # set key and isbn parameters for goodreads api request, then make get request
    params = {"key": "a2yG8Km4Ic43fptlWtPw", "isbns": book.book_isbn}
    goodreads_data = requests.get("https://www.goodreads.com/book/review_counts.json", params=params)
    
    # parse data from goodreads request !!! was this necessary? !!!
    goodreads_parse = goodreads_data.json()
    
    # retrieve required rating data from json object
    ratings_count = goodreads_parse["books"][0]["ratings_count"]
    average_rating = goodreads_parse["books"][0]["average_rating"]
    
    # select reviews for book_isbn matching this functions isbn parameter value, using a join to retrieve reviewer username, limit of four rows returned
    reviews = db.execute("SELECT user_username, review_text, review_rating FROM users JOIN reviews USING (user_id) JOIN books USING (book_id) WHERE book_isbn = :isbn  ORDER BY review_id DESC LIMIT 2", {"isbn": isbn}).fetchall()
    
    # if there are reviews found calculate the rating count and average
    if len(reviews) > 0:
        r_count = db.execute("SELECT COUNT(*) FROM reviews JOIN books USING (book_id) WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()
        r_avg = db.execute("SELECT AVG(review_rating) FROM reviews JOIN books USING (book_id) WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()   
        rev_count = r_count[0]
        rev_avg = round(r_avg[0], 2)

    # check if the current user has left a review for this book and set reviewed variable to true if so, this will hide the review form on the page    
    reviewed = False
    if db.execute("SELECT * FROM books JOIN reviews USING (book_id) JOIN users USING (user_id) WHERE book_isbn = :isbn AND user_username = :username", {"isbn": isbn, "username": session["username"]}).rowcount == 1:
        reviewed = True    

    # render the book page, passing all the book and review information    
    return render_template("book.html", book=book, reviews=reviews, ratings_count=ratings_count, average_rating=average_rating, reviewed=reviewed, rev_count=rev_count, rev_avg=rev_avg)


@app.route("/submitted")
@login_required
def submitted():
    """ confirmation page when a review submitted """
    
    # when redirected after a successful review submission, render the confirmation page
    return render_template("reviewed.html")


@app.route("/reviews/<isbn>", methods=["GET", "POST"])
@login_required
def reviews(isbn):
    """ query for a full list of reviews, not limited to 4 like the book route """
    
    # route redirects to login if login_required returns false
    
    # select details for book with ISBN matching this functions isbn parameter value
    book = db.execute("SELECT book_isbn, book_title, book_author, book_year FROM books WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()
    
    # select reviews for book_isbn matching this functions isbn parameter value, using a join to retrieve reviewer username
    reviews = db.execute("SELECT user_username, review_text, review_rating FROM users JOIN reviews USING (user_id) JOIN books USING (book_id) WHERE book_isbn = :isbn", {"isbn": isbn}).fetchall()
    
    # if there are reviews found calculate the rating count and average
    if len(reviews) > 0:
        r_count = db.execute("SELECT COUNT(*) FROM reviews JOIN books USING (book_id) WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()
        r_avg = db.execute("SELECT AVG(review_rating) FROM reviews JOIN books USING (book_id) WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()   
        rev_count = r_count[0]
        rev_avg = round(r_avg[0], 2)        
    
    # else render error page with given message
    else:
        return render_template("error.html", message="No reviews found for that ISBN.")

    # render reviews page, passing all the book and review information  
    return render_template("reviews.html", book=book, reviews=reviews, rev_count=rev_count, rev_avg=rev_avg)


@app.route("/myreviews")
@login_required
def myreviews():
    """ query and return all reviews by the user """
    
    reviews = db.execute("SELECT book_isbn, book_title, book_author, review_text, review_rating FROM books JOIN reviews USING (book_id) JOIN users USING (user_id) WHERE user_username = :username", {"username": session["username"]}).fetchall()
    
    return render_template("myreviews.html", reviews=reviews)


@app.route("/reviewedby/<username>")
@login_required
def reviewedby(username):
    """ query and return all reviews by the given user """
    
    if db.execute("SELECT * FROM users WHERE user_username = :username", {"username": username}).rowcount == 0:
        return render_template("error.html", message="404 - not found.")
    
    reviews = db.execute("SELECT book_isbn, book_title, book_author, review_text, review_rating FROM books JOIN reviews USING (book_id) JOIN users USING (user_id) WHERE user_username = :username", {"username": username}).fetchall()
    
    return render_template("reviewedby.html", reviews=reviews, username=username)


@app.route("/api/<isbn>") 
def api(isbn):
    """ api route to return JSON response for provided ISBN """
    
    # select details for book with ISBN matching this functions isbn parameter value     
    book = db.execute("SELECT book_title, book_author, book_year, book_isbn FROM books WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()
    
    # if query result is none then render error page indicating a 404 error
    if book is None:
        return render_template("error.html", message="404 - not found.")
    
    # query the book's rating count and average
    r_count = db.execute("SELECT COUNT(*) FROM reviews JOIN books USING (book_id) WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()
    r_avg = db.execute("SELECT AVG(review_rating) FROM reviews JOIN books USING (book_id) WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()   
    rev_count = r_count[0]
    if rev_count > 0:
        rev_avg = str(round(r_avg[0], 2))
    else:
        rev_avg = "n/a"
    
    # return json object
    return jsonify({
        "title": book.book_title,
        "author": book.book_author,
        "year": book.book_year,
        "isbn": book.book_isbn,
        "review_count": rev_count,
        "average_score": rev_avg
        })