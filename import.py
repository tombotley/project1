import os
import csv
 
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind = engine))

# create book metadata container object
bookdata = MetaData()


def main():
    """ create books table in PostgreSQL database and import books metadata from csv file """
      
    # define table
    books = Table('books', bookdata,
            Column('book_id', Integer, primary_key = True),
            Column('book_isbn', String, nullable = False),
            Column('book_title', String, nullable = False),
            Column('book_author', String, nullable = False),
            Column('book_year', Integer, nullable = False),
            )
    
    # create table
    books.create(engine)
     
    # open and read csv file
    b = open("books.csv")
    reader = csv.reader(b)
    
    # skip header row
    next(reader)
    
    # loop through csv file and insert data into books table
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (book_isbn, book_title, book_author, book_year) VALUES (:isbn, :title, :author, :year)", {"isbn": isbn, "title": title, "author": author, "year": year})
    db.commit()

    
if __name__ == "__main__":
    main()