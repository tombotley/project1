# Project 1

Web Programming with Python and JavaScript

Project 1 Books

Screencast presentation: https://youtu.be/mYGERBonF4w


Objectives

•	Become more comfortable with Python.

•	Gain experience with Flask.

•	Learn to use SQL to interact with databases.



Requirements

•	Users should be able to register and login with a username and password.

•	Logged in users should be able to log out of the site.

•	Import book details from books.csv with a Python file called import.py (separate from web application) into a PostgreSQL database.

•	Book search page for logged in users. Users should be able to type in the ISBN, title or author of a book and be presented with a list of matching results including partial matches.

•	When users click on a book from the results of their search they should be taken to a book page, with details about the book: its title, author, publication year, ISBN number, and any reviews that users have left on the website.

•	On the book page, users should be able to submit a review: consisting of a rating on a scale of 1 to 5, as well as a text component to the review where the user can write their opinion about a book. Users should not be able to submit multiple reviews for the same book.

•	On the book page, the average rating and number of ratings the work has received from Goodreads should be displayed if available.

•	API Access: If users make a GET request to the website’s /api/<isbn> route, where <isbn> is an ISBN number, the website should return a JSON response containing the book’s title, author, publication date, ISBN number, review count, and average score. The resulting JSON should follow the format:
    
{

    "title": "Memory",
    
    "author": "Doug Lloyd",
    
    "year": 2015,
    
    "isbn": "1632168146",
    
    "review_count": 28,
    
    "average_score": 5.0
    
}

•	If the requested ISBN number isn’t in the database, the website should return a 404 error.

•	Raw SQL commands (as via SQLAlchemy’s execute method) should be used in order to make database queries. SQLAlchemy ORM should not be used for this project.


What I have implemented

Application.py

This is my Python application file. To assist my application I have imported werkzeug.security for password hashing and a login_required wrapper function from my helpers.py file.

Route decorators

"/"

The default route function renders index.html. On this page a visitor is prompted to log in or register an account.

"/register"

The register route function renders register.html upon receiving a get request and on this page a new user can enter their registration details into a registration form. For post requests (upon submission of registration form) the function takes the form values, performs hashing with salt on the password, and then performs several checks on the submitted values. If a query of the users table returns any rows where the submitted email address matches an address in the table the register.html page is rendered again with an error message passed as an argument of the render_template function. If a query returns any rows with a username matching the submitted name the register.html is rendered again with an error message argument. Lastly if the password and password confirmation do not match the register.html is rendered again with an error message argument. If all these checks find no errors then the submitted user details are inserted into the users table and the user is redirected to “/login”.

“/login”

The login route renders login.html upon a get request and on this page an existing user can login to the site by entering their credentials into a login form. For post requests (upon submission of login form) the function takes the form values and queries the users table for the hashed password where the username matches the submitted username. If no row is returned or the check_password_hash function determines the passwords do not match then the login.html page is rendered again and an error message indicating an incorrect username or password is passed as an argument. If the login details are correct the session variable “username” is set to the submitted username and the user is redirected to “/search”.

“/logout”

The logout route uses the login_required wrapper function so that only users who are logged in are able to logout. When the logout function is called the session variable “username” is set to none and the logout.html page is rendered.

“/search”

The search route uses the login_required wrapper function so that only users who are logged in are able to access the search page. Upon a get request the search.html page is rendered where the user can enter a value with which to search the books table. For post requests (upon submission of search form) the function takes the search value, adds wildcard characters to each end and searches the database for any ISBN, author or title that match or partially match the value. If the number of rows returned is 0 then the search.html page is rendered again with an error message indicating no results were found, else the results.html page is rendered with the search results passed as an argument. Search results are rendered so that each is an anchor element and upon clicking on a particular result the user is taken to the book route and the book’s ISBN is passed as a route variable.

“/book/isbn”
    
The book route uses the login_required wrapper function so that only users who are logged in are able to access the book page. This route is called if the user clicks on a book listed in the results of a search or if the route is manually typed into the browser with a valid ISBN passed as the route variable. If an invalid ISBN is manually entered then the function will render error.html with an error message explaining that the ISBN was not found. If a post request is made containing a value named review (upon submission of the book review form) then the function fetches the book id for the routes ISBN value and the user id for the session user and inserts these values along with the submitted review data into the reviews table. The user is then redirected to “/submitted”. Otherwise the function uses the ISBN value to fetch the book details from the books table, any reviews for that book from the reviews table (with a limit of two rows fetched) and the Goodreads API review data. A check is made to see if the current user has reviewed the book already which determines if a variable called ‘reviewed’ is set to true or false and this will determine whether the book review form is displayed when the book.html page is rendered. Once all the book and review data have been retrieved the book.html page is rendered with the book/review data passed as arguments. 

“/submitted”

This is the route used when a review is successfully submitted and renders the reviewed.html page.

“/reviews/isbn”
    
The reviews route uses the login_required wrapper function so that only users who are logged in are able to access the reviews page. This page is rendered if the user clicks on ‘see all reviews’ on the book.html page (when a book has more than two reviews) or if the route is manually typed into the browser with a valid ISBN passed as the route variable. If an invalid ISBN is manually entered then the function will render error.html with an error message explaining that there were no reviews found for that ISBN. The function uses the ISBN to fetch the book details from the books table and any reviews for that book from the reviews table. The reviews.html is then rendered with the book/review data is passed as arguments.

“/myreviews”

The myreviews route uses the login_required wrapper function so that only users who are logged in are able to access the myreviews page. This page is rendered if the user clicks on ‘my reviews’ item on their header navigation bar. The function will fetch all reviews left by the current user and pass them as an argument when rendering the reviewedby.html page.

“/reviewedby/username”
    
The reviewedby route uses the login_required wrapper function so that only users who are logged in are able to access the reviewedby page. This page displays all reviews left by a particular user and is rendered when a reviewer name is clicked on any page that displays user reviews or if the route is manually entered into the browser with a valid username passed as the route variable. If an invlaid username is manually entered then the function will render error.html with a ‘404 not found’ message. Otherwise the username is used to fetch all reviews by that user and they are passed as an argument when the reviewdby.html page is rendered.

“/api/isbn”
    
The api route is used to return a JSON object containing details of a book matching the ISBN passed as the route variable. This route is accessed by manually typing the route and an ISBN into the browser. If no rows are fetched from the books table then the function will render error.html with a ‘404 not found’ message. Otherwise the function returns a JSON object by using the jsonify function the pair keys with the values retrieved from the database.


Additional Python files

Helpers.py

This is the Python file containing the login_required function used to determine if a user is logged in. The function wraps any route functions that require a user to be logged in and checks that the session variable “username” is not none. If none the user is redirected to “/login”, otherwise the wrapped function is run as normal.

Import.py

This is the Python file used to import data into a PostgreSQL database from a file called books.csv. The main function defines a books table to store the imported book data and then creates it at the given database location. A connection is then opened to the csv file and the contents read with the csv.reader function. After skipping the header line of the csv file which provides the key for each comma separated value, a for loop is used to read each subsequent line and insert a row into the books table, matching the values to the relevant database column using a Python dictionary.   
