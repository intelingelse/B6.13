from datetime import date

import sqlalchemy as sql
from bottle import route, run, HTTPError, request
from sqlalchemy import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_PATH = "sqlite:///albums.sqlite3"
Base = declarative_base()


class Album(Base):
    """
    class that describes album table in the database
    """
    __tablename__ = "album"
    id = sql.Column(sql.INTEGER, primary_key=True, autoincrement=True)
    year = sql.Column(sql.INTEGER)
    artist = sql.Column(sql.TEXT)
    genre = sql.Column(sql.TEXT)
    album = sql.Column(sql.TEXT)


def connect_db():
    """
    Устанавливает соединение к базе данных, создает таблицы, если их еще нет и возвращает объект сессии
    :return: session object
    """
    engine = sql.create_engine(DB_PATH)
    Base.metadata.create_all(engine)
    session = sessionmaker(engine)
    return session()


def is_exists(session, album):
    """
    :param session: session for query
    :param album: request album
    :return: True if the album already exists in the database, False if it doesn't
    """
    check_query = session.query(Album).filter(Album.album == album.album)

    check_query = check_query.first()

    return True if check_query else False


def is_missing(year, artist, genre, album):
    """
    function returns http error if any parameter is missing
    :param year: request year
    :param artist: request artist
    :param genre: request genre
    :param album: request album
    :return: False if everything is ok, HTTPError if something is missing or date is invalid
    """
    if not year:
        return HTTPError(status=422, body="Missing `year` parameter")
    elif not artist:
        return HTTPError(status=422, body="Missing `artist` parameter")
    elif not genre:
        return HTTPError(status=422, body="Missing `genre` parameter")
    elif not album:
        return HTTPError(status=422, body="Missing `album` parameter")
    else:
        return False


def is_invalid_year(year):
    """
    :param year:
    :return: returns False if everything is ok, HTTPError if year is invalid
    """
    if year:
        try:
            year = int(year)
        except ValueError:
            return HTTPError(status=422,
                             body="Invalid `year` value. `year` should be numerical value"
                             )
        else:
            if year > date.today().year or year < 1700:
                return HTTPError(status=422,
                                 body="Invalid `year` value. `year` should be between"
                                      "current year and 1700 inclusively."
                                 )
            else:
                return False


@route("/albums/<artist>")
def print_artist_albums(artist):
    """
    function that prints list of an albums of an artist
    :param artist:
    :return:
    """
    find_session = connect_db()
    artist_query = find_session.query(Album).filter(text(f'artist == "{artist}"')).all()
    find_session.close()
    if not artist_query:
        return HTTPError(404, f'Artist "{artist}" does not exist in the database.')
    else:
        artist_albums = ["<li>" + album.album + "</li>" for album in artist_query]
        artist_albums = " ".join([str(album) for album in artist_albums])
        return "<ul>" + f"<p>Albums of {artist}:</p>" + f"{artist_albums}"


@route("/albums", method="POST")
def create_album():
    """
    creates new album entry in the database
    """
    # creating new session for creating an album
    create_album_session = connect_db()

    # getting values from post request
    year = request.forms.get("year")
    artist = request.forms.get("artist")
    genre = request.forms.get("genre")
    album = request.forms.get("album")

    # if is_missing returns HTTPError return this function
    if is_missing(year=year, artist=artist, genre=genre, album=album):

        return is_missing(year=year, artist=artist, genre=genre, album=album)

    # else create a new instance of an album
    else:

        new_album = Album(
            year=year,
            artist=artist,
            genre=genre,
            album=album,
        )

    # if is_invalid returns HTTPError return this function
    if is_invalid_year(year):
        return is_invalid_year(year)

    # if is_exists returns True return HTTPError
    if is_exists(create_album_session, new_album):
        return HTTPError(422, "Album already exists.")

    create_album_session.add(new_album)
    create_album_session.commit()

    return f"new album has been added with id: {new_album.id}"


if __name__ == "__main__":
    run(host="localhost", port=8080, debug=True)
