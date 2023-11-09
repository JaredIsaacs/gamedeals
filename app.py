import os
import requests, json
from flask import Flask, request, render_template
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import validators

#https://apidocs.cheapshark.com/#intro

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

class Menus(FlaskForm):
    name = StringField("Name")

def get_games(title: str = '', upper_price: int = 15) -> dict:
    base_url = 'https://www.cheapshark.com/api/1.0/deals?storeID=1&upperPrice={0}&title={1}'
    print("Base URL:", base_url.format(upper_price, title))
    response = requests.get(base_url.format(upper_price, title)).json()
    return response

@app.route('/', methods=["GET", "POST"])
def index():
    form = Menus()
    
    if request.method == 'POST':
        game_name = form.name.data.strip()
        print('game_name: ', game_name)
        games = get_games(title=game_name)
        return render_template('index.html', form=form, games=games)

    games = get_games()
    return render_template('index.html', form=form, games=games)

if __name__ == '__main__':
    upper_price = 15
    response = requests.get(f"https://www.cheapshark.com/api/1.0/deals?storeID=1&upperPrice={upper_price}&pageNumber=0").json()
    with open("response.json", 'w') as outfile:
        json.dump(response, outfile, indent=4)

    app.run(debug=True, port=8080)