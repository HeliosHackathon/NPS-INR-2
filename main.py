from flask import *
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, ForeignKey, PickleType
from sqlalchemy.ext.mutable import MutableList, MutableSet
import time

app = Flask(__name__)
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
    id: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    farmer: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)
    produceType: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[str] = mapped_column(String, nullable=False)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/farmer", methods=['GET', 'POST'])
def farmer_sign_up_page():
    if request.method == 'GET':
        return render_template('')  # TODO
    password_hash = generate_password_hash(request.form.pop('password'))
    db.session.add(Farmer(passwordHash=password_hash, **request.form))
    db.session.commit()
    return redirect("/want-to-give-away")

@app.route("/want-to-give-away", methods=['GET', 'POST'])
def give_away_form():
    if request.method == 'GET':
        return render_template('')  # TODO
    # farmer = db.session.get(Farmer, session.get('email'))
    db.session.add(GiveAway(farmer=session.get('email'), id=time.time(), **request.form))
    db.session.commit()
    return redirect("/give-aways")

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