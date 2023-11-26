import os
import requests, json
from dotenv import load_dotenv
from flask import Flask, request, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField
from wtforms.validators import NumberRange, InputRequired

#https://apidocs.cheapshark.com/#intro

DEFAULT_MIN_PRICE = 0
DEFAULT_MAX_PRICE = 60
BASE_URL = 'https://www.cheapshark.com/api/1.0/'

load_dotenv()
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


def get_deal(deal_id: int) -> dict:
    global BASE_URL

    url = BASE_URL + 'deals?id={}'
    response = requests.get(url.format(deal_id)).json()
    return response


def get_img_urls(games: list[dict]) -> dict:
    '''
    Takes a list of game dictionaries and returns a dictionary
    that correlates a games cheapshark ID with the games steam thumbnail url.

    steamshark_id -> steam_img_url

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


def generate_access_token() -> str:
    url = 'https://id.twitch.tv/oauth2/token?client_id={0}&client_secret={1}&grant_type=client_credentials'
    client_id = os.getenv('CLIENT_ID')
    client_token = os.getenv('CLIENT_TOKEN')

    response = requests.post(url.format(client_id, client_token)).json()
    return response['access_token']


def get_game(game_name: str) -> dict:
    url = 'https://api.igdb.com/v4/games'
    client_id = os.getenv('CLIENT_ID')
    access_token = 'Bearer ' + generate_access_token()
    game_request = {
                        'headers': {'Client-ID': client_id, 'Authorization': access_token},
                        'data': 'where name = "{0}"; fields name, videos, summary;'.format(game_name)
                    }

    response = requests.post(url, **game_request).json()
    
    #If the game is not returned, search for it in a different, less precise way.
    if response == []:
        game_request['data'] = 'search "{0}"; fields name, videos, summary;'.format(game_name)
        response = requests.post(url, **game_request).json()

    #Get the oldest version of the game on steam if there a duplicates
    if len(response) > 1:
        game = [{'id': '999999999'}]
        for g in response:
            if int(g['id']) < int(game[0]['id']):
                game[0] = g
        return game
    

    return response


def get_video(game: dict) -> str:
    client_id = os.getenv('CLIENT_ID')
    access_token = 'Bearer ' + generate_access_token()

    response = requests.post('https://api.igdb.com/v4/game_videos', **{
                                                                        'headers': {'Client-ID': client_id, 'Authorization': access_token},
                                                                        'data': 'where game={}; fields checksum,game,name,video_id;'.format(game[0]['id'])
                                                                        }).json()
    
    #Get odlest video, aka the release trailer.
    if len(response) > 1:
        video = [{'id': '0'}]
        for v in response:
            if int(v['id']) > int(video[0]['id']):
                video[0] = v
        return video

    return response


@app.route('/', methods=["GET", "POST"])
def index():
    form = Menus()
    
    try:
        if request.method == 'POST':
            game_name = form.name.data
            min_price = form.min_price.data
            max_price = form.max_price.data

            games = get_deals(lower_price=min_price, upper_price=max_price, title=game_name)
            thumb_urls = get_img_urls(games=games)

            return render_template('index.html', form=form, games=games, thumb_urls=thumb_urls)

        games = get_deals()
        thumb_urls = get_img_urls(games=games)
        return render_template('index.html', form=form, games=games, thumb_urls=thumb_urls)
    except Exception as e:
        return render_template('index.html', form=form, games=[], thumb_urls={})


@app.route('/game', methods=["POST"])
def game():
    deal_id = request.form['submit_button']

    deal = get_deal(deal_id)
    game_name = deal['gameInfo']['name']
    game = get_game(game_name)
    video = get_video(game)

    return render_template('game.html', deal=deal, game=game, video=video)


if __name__ == '__main__':
    app.run(debug=True, port=8080)