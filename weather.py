from flask import Flask,request,render_template,abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import os
import json
import urllib.request
from ddtrace import tracer

tracer.set_tags({"track_error":True})

app = Flask(__name__)

#setting path for database file 
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'weather.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Weather(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country_code = db.Column(db.String(5), nullable=False)
    coordinate = db.Column(db.String(20), nullable=False)
    temp = db.Column(db.String(5))
    pressure = db.Column(db.Integer)
    humidity = db.Column(db.Integer)
    cityname = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())

with app.app_context():
    db.create_all()

def tocelcius(temp):
    return str(round(float(temp) - 273.16,2))

def get_default_city():
    return 'Delhi'
    
def save_to_database(weather_details):
    weather = Weather(country_code=weather_details["country_code"],
                    coordinate=weather_details["coordinate"],
                    temp=weather_details["temp"],
                    pressure=int(weather_details["pressure"]),
                    humidity=int(weather_details["humidity"]),
                    cityname=weather_details["cityname"])
    db.session.add(weather)
    db.session.commit()
    
def get_weather_details(city):
    api_key = '48a90ac42c53'
    # source contain json data from api
    try:
        source = urllib.request.urlopen('http://api.openweathermap.org/data/2.5/weather?q=' + city + '&appid='+api_key).read()
    except Exception as e:
        print("Oops!", e.__class__, "occurred.")
        return abort(400)
        
    # converting json data to dictionary
    list_of_data = json.loads(source)

    # data for variable list_of_data
    data = {
        "country_code": str(list_of_data['sys']['country']),
        "coordinate": str(list_of_data['coord']['lon']) + ' ' + str(list_of_data['coord']['lat']),
        "temp": str(list_of_data['main']['temp']) + 'k',
        "temp_cel": tocelcius(list_of_data['main']['temp']) + 'C',
        "pressure": str(list_of_data['main']['pressure']),
        "humidity": str(list_of_data['main']['humidity']),
        "cityname":str(city),
    }

    save_to_database(data)
    return data

@app.route('/',methods=['POST','GET'])
def weather():
    if request.method == 'POST':
        city = request.form['city']
    else:
        #for default name
        city = get_default_city()
    data = get_weather_details(city)
    return render_template('index.html',data=data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)