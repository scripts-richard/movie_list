#!/usr/bin/python3
# -------------------------------------------------------------------------------
# movies.py
# by Richard Mills
# Scrapes website for movies playing in Edmonton, fetches ratings
# and compiles list of high rated movies. Emails list
# !!!
# This product uses the TMDb API but is not endorsed or certified by TMDb.
# !!!
# -------------------------------------------------------------------------------

import bs4 as bs
# import json
import logging
import os
import requests
import urllib.request

import gmail_helper

from secrets import API_KEY

basedir = os.path.dirname(os.path.realpath(__file__))
emails_file = os.path.join(basedir, 'emails.txt')

logging.basicConfig(level=logging.ERROR,
                    format=' %(asctime)s - %(levelname)s - %(message)s')


def get_movie_data(movie, year):
    '''Retrieve TheMovieDB movie data, only returns movies with a rating
    higher or equal to 7.0
    '''
    logging.debug('Movie - ' + movie)
    logging.debug('Year - ' + year)
    url = 'https://api.themoviedb.org/3/search/movie?api_key=' + API_KEY
    url += '&language=en-US&query=' + movie.replace(' ', '%20')
    url += '&page=1&include_adult=false&primary_release_year=' + year
    logging.debug('URL - ' + url)
    r = requests.get(url)
    if r.status_code != 200:
        print(r.status_code)
        return False
    data = r.json()
    if data['total_results'] == 1:
        for result in data['results']:
            rating = result['vote_average']
            if rating >= 7.0:
                link = 'https://www.themoviedb.org/movie/'
                link += str(result['id'])
                # Movie Title, Rating, IMDB Link, and Plot
                return [movie, str(rating), link, result['overview']]
    return False


def get_movies():
    # Scrape website for movies playing in Edmonton using BeautifulSoup
    address = 'http://www.edmovieguide.com/movies/?sort=release-date'
    source = urllib.request.urlopen(address)
    soup = bs.BeautifulSoup(source, 'html.parser')
    movie_list = []

    for li in soup.find_all('li', class_='movie'):
        try:
            movie_name = li.find('a', class_='movie-title').text
            try:
                movie_date = li.find('p', class_='movie-date').text[-4:]
            except AttributeError:
                movie_date = ''
            movie_list.append([movie_name, movie_date])
        except AttributeError:
            print('WARNING: No movie list found...')
    return movie_list


def get_good_movies(movies):
    # Trim movie list using imdb_data()
    good_movies = []

    for movie in movies:
        movie_data = get_movie_data(movie[0], movie[1])
        if movie_data:
            good_movies.append(movie_data)
    return good_movies


def format_text(movies):
    # Formats text for email, plain text and html, returns both
    movie_text = ''
    movie_HTML = ''

    for movie in movies:
        movie_text += movie[0] + '     ' + movie[1] + '\n'
        movie_text += movie[3] + '\n'
        movie_HTML += '<tr><td><a href="%s">%s</a></td>' % (movie[2], movie[0])
        movie_HTML += "<td>%s</td></tr>" % movie[1]
        movie_HTML += "<tr><td>%s</td></tr>" % movie[3]

    text = "Top Rated Movies Playing in Edmonton!\n\n"
    text += movie_text
    html = """\
    <html>
        <head></head>
        <body>
            <h1>Top Rated Movies Playing in Edmonton!</h1>
            <br>
            <table>
                <tr><th>Movie</th><th>Rating</th></tr>
                %s
            </table>
        </body>
    </html>
    """ % movie_HTML

    return text, html


def main():
    movies = get_movies()
    good_movies = get_good_movies(movies)
    text, html = format_text(good_movies)
    sender, to = gmail_helper.get_emails(emails_file)
    gmail_helper.email(sender, to, 'Movie List', text, html)


if __name__ == "__main__":
    main()
