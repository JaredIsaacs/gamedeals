import os
import requests, json
from flask import Flask, request, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField
from wtforms.validators import NumberRange, InputRequired

#https://apidocs.cheapshark.com/#intro

DEFAULT_MIN_PRICE = 0
DEFAULT_MAX_PRICE = 60
BASE_URL = 'https://www.cheapshark.com/api/1.0/'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

class Menus(FlaskForm):
    global DEFAULT_MIN_PRICE, DEFAULT_MAX_PRICE

    name = StringField('Name')
    min_price = DecimalField('Minimum Price', validators=[InputRequired(), NumberRange(min=DEFAULT_MIN_PRICE,
                                                                                        message='Must be greater than 0')], default=DEFAULT_MIN_PRICE)
    max_price = DecimalField('Maximum Price', default=DEFAULT_MAX_PRICE)
    submit = SubmitField('Search!')

def get_deals(title: str = '', lower_price: float = DEFAULT_MIN_PRICE, upper_price: float = DEFAULT_MAX_PRICE, page_number: int = 0) -> dict:
    global BASE_URL

    url = BASE_URL + 'deals?storeID=1&lowerPrice={0}&upperPrice={1}&title={2}&pageSize=15&pageNumber={3}'
    response = requests.get(url.format(lower_price, upper_price, title, page_number)).json()
    return response


def get_game(gameid: int) -> dict:
    global BASE_URL

    url = BASE_URL + 'games?id={}'
    response = requests.get(url.format(gameid)).json()
    return response


def get_urls(games: list[dict]) -> dict:
    '''
    Takes a list of game dictionaries and returns a dictionary
    that correlates a games cheapshark ID with the games steam thumbnail url.

    steamshark_id -> steam_url

    Gets the thumbnail that is displayed on the steam main page.
    The default thumbnails that cheapshark provides are in a very small resolution.
    '''
    steam_url = 'https://cdn.akamai.steamstatic.com/steam/apps/{0}/header.jpg'
    game_urls = {}

    if 'error' in games:
        raise Exception('Rate limit reached.')

    for game in games:
        game_urls[game['gameID']] = steam_url.format(game['steamAppID'])

    return game_urls


@app.route('/', methods=["GET", "POST"])
def index():
    form = Menus()
    
    try:
        if request.method == 'POST':
            game_name = form.name.data
            min_price = form.min_price.data
            max_price = form.max_price.data

            games = get_deals(lower_price=min_price, upper_price=max_price, title=game_name)
            thumb_urls = get_urls(games=games)

            return render_template('index.html', form=form, games=games, thumb_urls=thumb_urls)

        games = get_deals()
        thumb_urls = get_urls(games=games)
        return render_template('index.html', form=form, games=games, thumb_urls=thumb_urls)
    except Exception as e:
        return render_template('index.html', form=form, games=[], thumb_urls={})


@app.route('/game', methods=["POST"])
def game():
    gameid = request.form['submit_button']
    game = get_game(gameid=gameid)
    return render_template('game.html', game=game)


if __name__ == '__main__':
    app.run(debug=True, port=8080)