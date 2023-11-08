import os
import requests, json
from flask import Flask, render_template

#https://apidocs.cheapshark.com/#intro

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    #app.run(debug=True, port=8080)
    
    upper_price = 15
    response = requests.get(f"https://www.cheapshark.com/api/1.0/deals?storeID=1&upperPrice={upper_price}&pageNumber=0").json()
    with open("response.json", 'w') as outfile:
        json.dump(response, outfile, indent=4)