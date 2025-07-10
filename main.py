from flask import *
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, ForeignKey, PickleType, Double
from sqlalchemy.ext.mutable import MutableList, MutableSet
import time
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy()
db.init_app(app)

class Farmer(db.Model):
    name: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String)
    passwordHash: Mapped[str] = mapped_column(String, nullable=False)
    phoneNo: Mapped[int] = mapped_column(Integer, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)

class GiveAway(db.Model):
    id: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)
    farmer: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)
    produceType: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[str] = mapped_column(String, nullable=False)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/farmer", methods=['GET', 'POST'])
def farmer_sign_up_page():
    if request.method == 'GET':
        return render_template('farmersignup.html')  # TODO
    x = request.form.to_dict()
    # x.pop("submit")
    password_hash = generate_password_hash(x.pop('password'))
    x['phoneNo'] = int(x['phoneNo'])
    db.session.add(Farmer(passwordHash=password_hash, **x))
    db.session.commit()
    session['email'] = request.form['email']
    session['type'] = 'FARMER'
    return redirect("/want-to-give-away")

@app.route("/want-to-give-away", methods=['GET', 'POST'])
def give_away_form():
    if request.method == 'GET':
        return render_template('farmerform.html')  # TODO
    # farmer = db.session.get(Farmer, session.get('email'))
    x = request.form.to_dict()
    x.pop('submit')
    x['farmer'] = session.get('email')
    print(x)
    db.session.add(GiveAway(id=str(time.time()), **x))
    db.session.commit()
    return redirect("/my-giveaways")

@app.route("/login-farmer", methods=['GET', 'POST'])
def login_farmer():
    if request.method == 'GET':
        return render_template('')  # TODO
    farmer = db.session.get(Farmer, request.form['email'])
    if check_password_hash(farmer.passwordHash, request.form['password']):
        session['email'] = request.form['email']
        session['type'] = 'FARMER'
        return redirect("/")
    else:
        return jsonify(error="Wrong"), 400
    
@app.route("/login-recipient", methods=['GET', 'POST'])
def login_recipient():
    if request.method == 'GET':
        return render_template('')  # TODO
    farmer = db.session.get(Farmer, request.form['email'])
    if check_password_hash(farmer.passwordHash, request.form['password']):
        session['email'] = request.form['email']
        session['type'] = 'FARMER'
        return redirect("/")
    else:
        return jsonify(error="Wrong"), 400
    
@app.route("/giveaways")
def giveaway_list():
    glist = db.session.execute(db.select(GiveAway, Farmer.name, Farmer.location).where(GiveAway.farmer == Farmer.email)).all()

    return render_template("giveaways.html", glist=glist)

@app.route("/my-giveaways")
def my_giveaway_list():
    email = session.get('email')
    glist = db.session.execute(db.select(GiveAway, Farmer.name, Farmer.location).where(GiveAway.farmer == Farmer.email)).all()
    return render_template("giveaways.html", glist=glist)
    
with app.app_context():
    db.create_all()