from flask import Flask, render_template, url_for, request, redirect, session, flash
from functools import wraps
from flask_mysqldb import MySQL 
from wtforms import Form, BooleanField, StringField, validators, PasswordField, SubmitField, FileField, SelectField, IntegerField, DecimalField, TextAreaField
import email_validator
from flask_wtf.file import FileField, FileAllowed, FileRequired
from passlib.hash import sha256_crypt
from wtforms.validators import NumberRange

class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=2, max=25, message="Username-i düzgün daxil edin."), validators.required("Username daxil edin.")])
    email = StringField('Email', [validators.Email(message="Email düzgün deyil."), validators.required("Email daxil edin.")])
    password = PasswordField('Password', [validators.required("Şifrə yaradın."), validators.EqualTo('confirm', message="Şifrələr uyuşmur.")])
    confirm = PasswordField('Repeat Password', [validators.required(message="Şifrəni təkrarlayın.")])

class LoginForm(Form):
    username = StringField('Username', [validators.Length(min=2, max=25, message="Username-i düzgün daxil edin."), validators.required("Username daxil edin.")])
    password = PasswordField('Password', [validators.required("Şifrənizi daxil edin.")])

class AnnouncementForm(Form):
    brand = SelectField('Brand', choices=[('Mercedes')])
    model = SelectField('Model', choices=[('E220')])
    currency = SelectField('Currency', choices=[('₼'),('€'),('$')])
    price = IntegerField('Price', validators=[validators.Required(message='Qiymət müəyyən edin.')])
    year = IntegerField('Year', validators=[validators.Required(message='Buraxılış ilini qeyd edin.')])
    engine = SelectField('Engine', choices=[('3.1')])
    engine_power = IntegerField('Engine power', validators=[validators.Required(message='Qiymət müəyyən edin.')])
    kilometer = IntegerField('Kilometer')
    city = StringField('City', validators=[validators.Length(min=2, max=30, message="Şəhərinizi düzgün daxil edin."), validators.required(message="Şəhər daxil edin.")])
    car_type = SelectField('Car type', choices=[('Sedan')])
    color = SelectField('Color', choices=[('Qara')])
    fuel_type = SelectField('Fuel type', choices=[('Dizel')])
    gearbox = SelectField('Gearbox', choices=[('Manual')])
    new = BooleanField('New')
    transmitter = SelectField('Fuel type', choices=[('Ön')])
    details = TextAreaField('Details', validators=[validators.Required("Bu yerin boş qalması məqsədəuyğun deyil.")])

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash('Bu səhifəyə baxmaq üçün daxil olun.','danger')
            return redirect(url_for("login"))
    return decorated_function

app = Flask(__name__)
mysql = MySQL(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'emta'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = '13572468'

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/register", methods = ["POST", "GET"])
def register():
    form = RegistrationForm(request.form)
    if request.method == "POST" and form.validate():
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        sorgu2 = "SELECT * FROM users WHERE username = %s OR email = %s"
        result = cursor.execute(sorgu2,(username, email))
        if result == 0:
            cursor = mysql.connection.cursor()
            sorgu = "INSERT INTO users(username, email, password) VALUES(%s,%s,%s)"
            cursor.execute(sorgu,(username, email, password))
            mysql.connection.commit()
            cursor.close()
            flash('Qeydiyyatdan uğurla keçdiniz.', 'success')
            return redirect("/login")
        else:
            flash('Belə bir istifadəçi var.', 'danger')
            return render_template("register.html", form=form)
    else:
        return render_template("register.html", form=form)

@app.route("/login", methods = ["POST", "GET"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM users WHERE username = %s"
        result = cursor.execute(sorgu,(username,))
        if result > 0:
            data = cursor.fetchone()
            real_password = data['password']
            if sha256_crypt.verify(password_entered,real_password):
                flash('Uğurla daxil oldunuz.', 'success')
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for('index'))
            else:
                flash('Şifrənizi düzgün daxil edin.','danger')
                return redirect(url_for('login'))
        else:
            flash('Belə bir istifadəçi tapılmadı.','danger')
            return redirect(url_for('login'))
    else:
        return render_template("login.html", form=form)

    return render_template("login.html", form=form)

@app.route("/announcements")
def announcements():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM cars ORDER BY announcement_date DESC"
    result = cursor.execute(sorgu)
    cars = cursor.fetchall()
    return render_template("announcements.html", result=result, cars=cars)

@app.route("/announcement/<string:car_id>")
def announcement(car_id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM cars WHERE id=%s"
    result = cursor.execute(sorgu,(car_id,))
    if result > 0:
        car = cursor.fetchone()
        return render_template("announcement.html", car=car)
    else:
        flash("Belə bir elan tapılmadı.","danger")
        return render_template("announcement.html")

@app.route("/remove/<string:car_id>")
@login_required
def remove(car_id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM cars WHERE id=%s AND profile=%s"
    result = cursor.execute(sorgu,(car_id,session["username"]))
    if result > 0:
        sorgu2 = "DELETE FROM cars WHERE id=%s"
        cursor.execute(sorgu2,(car_id,))
        mysql.connection.commit()
        flash("Elanınız silindi.", "success")
        return redirect(url_for("myprofile"))
    else:
        flash("Belə bir elan yoxdur və ya bu elanı silməyə icazəniz yoxdur.", "danger")
        return redirect(url_for("index"))
        

@app.route("/edit/<string:car_id>", methods=["POST", "GET"])
@login_required
def edit(car_id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM cars WHERE id=%s AND profile=%s"
    result = cursor.execute(sorgu,(car_id, session["username"]))
    if result > 0:
        form = AnnouncementForm(request.form)
        if request.method == "POST" and form.validate():
            new_brand = form.brand.data
            new_model = form.model.data
            new_currency = form.currency.data
            new_price = form.price.data
            new_year = form.year.data
            new_engine = form.engine.data
            new_engine_power = form.engine_power.data
            new_kilometer = form.kilometer.data
            new_city = form.city.data
            new_car_type = form.car_type.data
            new_color = form.color.data
            new_fuel_type = form.fuel_type.data
            new_gearbox = form.gearbox.data
            new_transmitter = form.transmitter.data
            new_details = form.details.data
            if new_kilometer > 0:
                new_new = "Xeyr"
            else:
                new_new = "Bəli"
            cursor = mysql.connection.cursor()
            sorgu2 = "UPDATE cars SET new = %s, announcement_date=current_timestamp, brand = %s, model=%s, currency=%s, price=%s, year=%s, engine=%s, engine_power=%s, kilometer=%s, city=%s, car_type=%s, color=%s, fuel_type=%s, gearbox=%s, transmitter=%s, details=%s WHERE id=%s AND profile=%s"
            cursor.execute(sorgu2,(new_new, new_brand, new_model, new_currency, new_price, new_year, new_engine, new_engine_power, new_kilometer, new_city, new_car_type, new_color, new_fuel_type, new_gearbox, new_transmitter, new_details, car_id, session["username"]))
            mysql.connection.commit()
            cursor.close()
            flash("Elanınız yeniləndi", "success")
            return redirect(url_for("myprofile"))
        else:
            car = cursor.fetchone()
            form.brand.data = car["brand"]
            form.model.data = car["model"]
            form.currency.data = car["currency"]
            form.price.data = car["price"] 
            form.year.data = car["year"]
            form.engine.data = car["engine"] 
            form.engine_power.data = car["engine_power"]
            form.kilometer.data = car["kilometer"] 
            form.city.data = car["city"]
            form.car_type.data = car["car_type"] 
            form.color.data = car["color"]
            form.fuel_type.data = car["fuel_type"] 
            form.gearbox.data = car["gearbox"]
            form.new.data = car["new"]
            form.transmitter.data = car["transmitter"] 
            form.details.data = car["details"]
            return render_template("edit.html", form=form)
    else:
        flash("Belə bir elan yoxdur və ya bu elanı yeniləməyə icazəniz yoxdur.","danger")
        return redirect(url_for("index"))


@app.route("/myprofile")
@login_required
def myprofile():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM cars WHERE profile=%s ORDER BY announcement_date DESC"
    result = cursor.execute(sorgu,(session["username"],))
    cars = cursor.fetchall()
    return render_template("myprofile.html", cars=cars, result=result)

@app.route("/profile/<string:username>")
def profile(username):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM users WHERE username = %s"
    result = cursor.execute(sorgu,(username,))
    if result > 0:
        cursor = mysql.connection.cursor()
        sorgu2 = "SELECT * FROM cars WHERE profile=%s  ORDER BY announcement_date DESC"
        result2 = cursor.execute(sorgu2,(username,))
        cars = cursor.fetchall()
        return render_template("profile.html", result=result, result2=result2, cars=cars, username=username)
    else:
        return render_template("profile.html", result=result)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/addannouncement", methods=["GET", "POST"])
@login_required
def addannouncement():
    form = AnnouncementForm(request.form)
    if request.method == "POST" and form.validate():
        profile = session["username"]
        brand = form.brand.data 
        model = form.model.data
        price = form.price.data
        currency = form.currency.data 
        year = form.year.data
        engine = form.engine.data
        kilometer = form.kilometer.data
        engine_power = form.engine_power.data
        city = form.city.data
        car_type = form.car_type.data
        color = form.color.data
        fuel_type = form.fuel_type.data
        gearbox = form.gearbox.data
        transmitter = form.transmitter.data
        details = form.details.data
        if kilometer > 0:
            new = "Xeyr"
        else:
            new = "Bəli"
        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO cars(profile, brand, model, price, currency, year, engine, kilometer, engine_power, city, car_type, color, fuel_type, gearbox, transmitter, new, details) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sorgu,(profile, brand, model, price, currency, year, engine, kilometer, engine_power, city, car_type, color, fuel_type, gearbox, transmitter, new, details))
        mysql.connection.commit()
        cursor.close()
        flash('Elanınız yaradıldı.','success')
        return redirect(url_for('myprofile'))
    else:
        return render_template("addannouncement.html", form=form)


if __name__ == "__main__":
    app.run(debug=True)