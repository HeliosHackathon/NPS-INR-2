from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
import time
import toml
# import secrets # Not used directly, secret_key is from toml

app = Flask(__name__)
app.secret_key = toml.load('secrets.toml')['SECRET']
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app) # Initialize db with app

class Farmer(db.Model):
    name: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String)
    passwordHash: Mapped[str] = mapped_column(String, nullable=False)
    phoneNo: Mapped[int] = mapped_column(Integer, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)

class GiveAway(db.Model):
    id: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)
    farmer: Mapped[str] = mapped_column(String, nullable=False) # Foreign key to Farmer.email
    produceType: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class Recipient(db.Model):
    name: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String)
    passwordHash: Mapped[str] = mapped_column(String, nullable=False)
    phoneNo: Mapped[int] = mapped_column(Integer, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/farmer-sign-up", methods=['GET', 'POST'])
def farmer_sign_up_page():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        password = form_data.pop('password')
        password_hash = generate_password_hash(password)
        form_data['phoneNo'] = int(form_data['phoneNo'])
        
        existing_farmer = db.session.get(Farmer, form_data['email'])
        if existing_farmer:
            flash('Email already registered. Please login or use a different email.', 'danger')
            return render_template('farmersignup.html')

        new_farmer = Farmer(passwordHash=password_hash, **form_data)
        db.session.add(new_farmer)
        db.session.commit()
        session['email'] = new_farmer.email
        session['type'] = 'FARMER'
        flash('Farmer account created successfully!', 'success')
        return redirect(url_for("my_giveaway_list"))
    return render_template('farmersignup.html')

@app.route("/recipient-sign-up", methods=['GET', 'POST'])
def recipient_sign_up_page():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        password = form_data.pop('password')
        password_hash = generate_password_hash(password)
        form_data['phoneNo'] = int(form_data['phoneNo'])

        existing_recipient = db.session.get(Recipient, form_data['email'])
        if existing_recipient:
            flash('Email already registered. Please login or use a different email.', 'danger')
            return render_template('recipientsignup.html')

        new_recipient = Recipient(passwordHash=password_hash, **form_data)
        db.session.add(new_recipient)
        db.session.commit()
        session['email'] = new_recipient.email
        session['type'] = 'RECP'
        flash('Recipient account created successfully!', 'success')
        return redirect(url_for("giveaway_list"))
    return render_template('recipientsignup.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'email' in session: # Already logged in
        if session.get('type') == 'FARMER':
            return redirect(url_for('my_giveaway_list'))
        elif session.get('type') == 'RECP':
            return redirect(url_for('giveaway_list'))
        else:
            return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type') # 'farmer' or 'recipient'

        user = None
        if user_type == 'farmer':
            user = db.session.get(Farmer, email)
        elif user_type == 'recipient':
            user = db.session.get(Recipient, email)
        else:
            flash('Invalid user type selected.', 'danger')
            return render_template('login.html')

        if user and check_password_hash(user.passwordHash, password):
            session['email'] = user.email
            session['type'] = 'FARMER' if user_type == 'farmer' else 'RECP'
            flash('Logged in successfully!', 'success')
            if session['type'] == 'FARMER':
                return redirect(url_for('my_giveaway_list'))
            else:
                return redirect(url_for('giveaway_list'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('login.html')
    return render_template('login.html')

@app.route("/logout")
def logout():
    session.pop('email', None)
    session.pop('type', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route("/want-to-give-away", methods=['GET', 'POST'])
def give_away_form():
    if 'email' not in session or session.get('type') != 'FARMER':
        flash('You must be logged in as a farmer to create a giveaway.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        form_data = request.form.to_dict()
        form_data['farmer'] = session['email']
        # Consider removing 'submit' if it's part of form_data and not a DB column
        # form_data.pop('submit', None) # Safely remove if present
        
        new_giveaway = GiveAway(id=str(time.time()), **form_data)
        db.session.add(new_giveaway)
        db.session.commit()
        flash('Giveaway created successfully!', 'success')
        return redirect(url_for("my_giveaway_list"))
    return render_template('farmerform.html')

@app.route("/giveaways")
def giveaway_list():
    giveaways_data = db.session.execute(
        db.select(GiveAway, Farmer.name, Farmer.location, Farmer.phoneNo).\
        where(GiveAway.farmer == Farmer.email).where(GiveAway.status)
    ).fetchall()
    
    # The template expects glist=(giveaway_obj, farmer_name, farmer_loc, farmer_phno)
    return render_template("giveaways.html", glist=giveaways_data, \
                           ctimes=lambda x: time.ctime(float(x)))


@app.route("/my-giveaways", methods=['GET', 'POST'])
def my_giveaway_list():
    if 'email' not in session or session.get('type') != 'FARMER':
        flash('Please login as a farmer to view your giveaways.', 'warning')
        return redirect(url_for('login'))

    email = session['email']
    
    farmer_details_obj = db.session.get(Farmer, email)
    if not farmer_details_obj:
        flash('Farmer details not found.', 'danger')
        session.pop('email', None) # Log out user if farmer record is missing
        session.pop('type', None)
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'id' in request.form:
            x = db.session.execute(db.select(GiveAway)\
                               .where(GiveAway.farmer == email).where(GiveAway.id == request.form['id']))\
                                .one()[0]
            x.status = not x.status
            db.session.commit()
            flash(f"Giveaway is now {'reposted' if x.status else 'withdrawn'}.", 'category')

    giveaways_list = db.session.execute(
        db.select(GiveAway).where(GiveAway.farmer == email)
    ).scalars().all() # .scalars().all() gives a list of GiveAway objects

    return render_template("mygiveaways.html", giveaways=giveaways_list, farmer_details=farmer_details_obj, \
                           ctimes=lambda x: time.ctime(float(x)))
    
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)