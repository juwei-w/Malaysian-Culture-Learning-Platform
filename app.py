from enum import unique
from livereload import Server
from email.policy import default
from multiprocessing.sharedctypes import Value
from wsgiref import validate
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Email, Length, NumberRange, DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import time


app = Flask(__name__)
app.config['SECRET_KEY'] = 'Secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# ---------- User ---------- #
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), default='User')
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    
    def __repr__(self):
        return f'{self.username}'


# ---------- Course ---------- #
class Course(db.Model):
    course_id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(50), nullable=False, unique=True)
    course_duration = db.Column(db.Integer, nullable=False)
    course_price = db.Column(db.Integer, nullable=False)
    course_slot = db.Column(db.Integer, nullable=False)
    course_trainer = db.Column(db.String(50), nullable=False)
    course_order = db.Column(db.Integer, default=0)
    course_date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    course_info = db.Column(db.String(200), nullable=False)
    course_slot_1_day = db.Column(db.String, nullable=False)
    course_slot_1_time = db.Column(db.String, nullable=False)
    course_slot_2_day = db.Column(db.String, nullable=False)
    course_slot_2_time = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f'{ self.course_name }'


# ---------- Order ---------- #
class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    course_name = db.Column(db.String(50), nullable=False)
    slot_day = db.Column(db.String, nullable=False)
    slot_time = db.Column(db.String, nullable=False)


# ---------- Cart ---------- #
class Cart(db.Model):
    cart_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    course_name = db.Column(db.String(50), nullable=False)
    course_price = db.Column(db.Integer, nullable=False)
    slot_day = db.Column(db.String, nullable=False)
    slot_time = db.Column(db.String, nullable=False)


# ---------- Feedback ---------- #
class Feedback(db.Model):
    feedback_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), nullable=False)
    feedback = db.Column(db.String(3000), nullable=False)


# ---------- Login ---------- #
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid Email'), Length(max= 50)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('Remember me')


# ---------- Register ---------- #
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid Email'), Length(max= 50)])
    

# ---------- Create Course ---------- #
class CourseForm(FlaskForm):
    course_name = StringField('Course Name', validators=[InputRequired(), Length(min=2, max=30)])
    course_duration = IntegerField('Course Duration (month)', validators=[InputRequired(), NumberRange(min=1, max=24, message='Invalid number')])
    course_price = IntegerField('Price', validators=[InputRequired(), NumberRange(min=1, max=100000, message='Invalid number')])
    course_slot = IntegerField('Slots', validators=[InputRequired(), NumberRange(min=1, max=1000, message='Invalid number')])
    course_trainer = StringField('Trainer Name', validators=[InputRequired(), Length(min=2, max=50)])
    course_info = StringField('Course Description', validators=[InputRequired(), Length(max=700)])
    course_slot_1_day = StringField('Slot 1 Day', validators=[InputRequired(), Length(min=2, max=20)])
    course_slot_1_time = StringField('Slot 1 Time', validators=[InputRequired(), Length(min=2, max=20)])
    course_slot_2_day = StringField('Slot 2 Day', validators=[InputRequired(), Length(min=2, max=20)])
    course_slot_2_time = StringField('Slot 2 Time', validators=[InputRequired(), Length(min=2, max=20)])


# ---------- Search Bar ---------- #
class SearchForm(FlaskForm):
    search = StringField("Search")
    submit = SubmitField("Submit")


# ---------- Purchase Course ---------- #
class PurchaseCourseForm(FlaskForm):
    submit = SubmitField('Register')


# ---------- Feedback Form ---------- #
class FeedbackForm(FlaskForm):
    feedback = StringField("Kindly leave your feedbacks here <3")
    submit = SubmitField("Submit")

# ---------- Load user ---------- #
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------- Pass stuff to navbar ---------- #
@app.context_processor
def base():
    form=SearchForm()
    return dict(form=form)


# ======================================= #
# INDEX, LOG IN, SIGN UP (AUTHENTICATION) #
# ======================================= #


# ---------- Redirect index ---------- #
@app.route('/')
def index():
    return render_template('index.html')


# ---------- Redirect login ---------- #
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    # if form is submitted
    if form.validate_on_submit():
        # finds the first email that matches the input in login form
        user = User.query.filter_by(email=form.email.data).first()
        if user == None:
            flash('This user does not exist')
            return redirect(url_for('login'))

        elif user.type == 'Admin':
            if user.password == form.password.data:
                login_user(user, remember=form.remember.data)
                flash(f'Logged in successfully')
                return redirect(url_for('editcourse'))
            flash('Invalid username or password')

        elif user:
            if user.password == form.password.data:
                login_user(user, remember=form.remember.data)
                flash(f'Logged in successfully')
                return redirect(url_for('dashboard'))
            flash('Invalid username or password')

    return render_template('login.html', form=form)


# ---------- Redirect signup ---------- #
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    
    # if form is submitted
    if form.validate_on_submit():
        new_user = User(username=form.username.data, email=form.email.data, password=form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('New user has been created')

    return render_template('signup.html', form=form)


# =========================================== #
# ADMIN DASHBOARD, EDIT COURSE, DELETE COURSE #
# =========================================== #


# # ---------- Redirect admindashboard ---------- #
# @app.route('/admin/admindashboard')
# @login_required
# def admindashboard():
    return render_template('/admin/admindashboard.html')


# ---------- Redirect editcourse ---------- #
@app.route('/admin/editcourse', methods=['GET', 'POST'])
@login_required
def editcourse():
    form = CourseForm()
    courses = Course.query.all()
    search_form = SearchForm()


    #---------- Search Bar ----------#
    if request.method == 'POST' and 'search' in request.form:
        searched = search_form.search.data
        if search_form.search.data == '':
            flash('Enter something to search')
            return redirect(url_for('editcourse'))

        else:
            courses = Course.query.filter(Course.course_name.like('%' + searched + '%'))
            
            flash(f'You searched {searched}')
            return render_template('/admin/editcourse.html', form=form, courses=courses)


    # Create course form
    if form.validate_on_submit():
        course_name = Course.query.filter_by(course_name=form.course_name.data).first()

        if course_name == None:
            new_course = Course(
                course_name=form.course_name.data,
                course_duration=form.course_duration.data,
                course_price=form.course_price.data,
                course_slot=form.course_slot.data,
                course_trainer=form.course_trainer.data,
                course_info=form.course_info.data,
                course_slot_1_day=form.course_slot_1_day.data,
                course_slot_1_time=form.course_slot_1_time.data,
                course_slot_2_day=form.course_slot_2_day.data,
                course_slot_2_time=form.course_slot_2_time.data
                )
            db.session.add(new_course)
            db.session.commit()
            flash('New course has been created!')

            courses = Course.query.all()
            return render_template('/admin/editcourse.html', form=form, courses=courses)
        else:
            flash('This course already exist')
            return render_template('/admin/editcourse.html', form=form, courses=courses)

    else:
        return render_template('/admin/editcourse.html', form=form, courses=courses)


# ---------- Delete Course ---------- #
@app.route('/delete/<int:course_id>', methods=['GET', 'POST'])
@login_required
def delete(course_id):
    entry = Course.query.get(course_id)
    if entry != None:
        db.session.delete(entry)
        db.session.commit()
        flash(f'{entry.course_name} has been deleted')

    return redirect(url_for('editcourse'))


# ========================================================= #
# USER DASHBOARD, MYPLAN, COURSE, MYCART, ABOUT, SEARCH BAR #
# ========================================================= #


# ---------- Redirect dashboard ---------- #
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    # Cart & Checkout
    user_id = int(current_user.id)                              # (Get current user id)
    user_cart = Cart.query.filter_by(user_id=user_id).all()     # (Get course from user's cart)
    # Feedbacks
    form = FeedbackForm()
    user = User.query.filter_by(id=user_id).first()
    feedbacks = Feedback.query.all()


    #---------- Remove From Cart ----------#
    if request.method == 'POST' and 'remove' in request.form:
        course_name = request.form.get('remove')
        for course in user_cart:
            if course.course_name == course_name:
                db.session.delete(course)
                db.session.commit()
                flash(f'{course_name} has been removed from cart')
                return redirect(url_for('dashboard'))


    #---------- Checkout ----------#
    if request.method == 'POST' and 'checkout' in request.form:

        for register_course in user_cart:
            # Total order increment
            course = Course.query.filter_by(course_name=register_course.course_name).first() # (Getting course object)
            course.course_order += 1

            # Adding into Order database
            order = Order(user_id=user_id, course_name=register_course.course_name, slot_day=register_course.slot_day, slot_time=register_course.slot_time)
            db.session.add(order)

            # Delete course from cart
            db.session.delete(register_course)
            db.session.commit()

        flash('Courses successfully registered')
        return redirect(url_for('dashboard'))

    
    #---------- Feedback ----------#
    if form.validate_on_submit():
        feedback = form.feedback.data
        flash(feedback)

        new_feedback = Feedback(
            user_name = user.username,
            feedback = feedback
        )

        db.session.add(new_feedback)
        db.session.commit()
        flash('Thank you for your kind feedback!')
        return redirect(url_for('dashboard'))

    return render_template('dashboard.html', name=current_user.username, user_cart=user_cart, form=form, feedbacks=feedbacks)


# ---------- Myplan event(calendar) ---------- #
events = [
    {
        'todo' : 'Batik Tutorial',
        'date' : '2022-08-30',
    },
    {
        'todo' : 'Kuih Tutorial',
        'date' : '2022-08-31',
    },
    {
        'todo' : 'Kuih Tutorial',
        'date' : '2022-08-31',
    }
]

# ---------- Redirect myplan ---------- #
@app.route('/myplan', methods=['GET', "POST"])
# @login_required
def myplan():
    # Cart & Checkout
    user_id = int(current_user.id)                              # (Get current user id)
    user_cart = Cart.query.filter_by(user_id=user_id).all()     # (Get course from user's cart)
    user_ordered = Order.query.filter_by(user_id=user_id).all() # (Get registered course from database)


    #---------- Remove From Cart ----------#
    if request.method == 'POST' and 'remove' in request.form:
        course_name = request.form.get('remove')
        for course in user_cart:
            if course.course_name == course_name:
                db.session.delete(course)
                db.session.commit()
                flash(f'{course_name} has been removed from cart')
                return redirect(url_for('myplan'))


    #---------- Checkout ----------#
    if request.method == 'POST' and 'checkout' in request.form:

        for register_course in user_cart:
            # Total order increment
            course = Course.query.filter_by(course_name=register_course.course_name).first() # (Getting course object)
            course.course_order += 1

            # Adding into Order database
            order = Order(user_id=user_id, course_name=register_course.course_name, slot_day=register_course.slot_day, slot_time=register_course.slot_time)
            db.session.add(order)

            # Delete course from cart
            db.session.delete(register_course)
            db.session.commit()

        flash('Courses successfully registered')
        return redirect(url_for('myplan'))


    if request.method == "POST":
        title = request.form['title']
        start = request.form['start']
        end = request.form['end']
        url = request.form['url']
        if end == '':
            end=start
        events.append({
            'title' : title,
            'start' : start,
            'end' : end,
            'url' : url
        },
        )
    return render_template("myplan.html", events=events, user_cart=user_cart, user_ordered=user_ordered)


# ---------- Redirect course ---------- #
@app.route('/course', methods=['GET', 'POST'])
@login_required
def course():
    # Top Nav (register submit button)
    purchase_form = PurchaseCourseForm() # Currently not used in code
    # Course
    courses = Course.query.all()
    # Filter By
    select = request.form.get('list')
    # Search Bar
    form = SearchForm()
    # Cart & Checkout
    user_id = int(current_user.id)                              # (Get current user id)
    user_cart = Cart.query.filter_by(user_id=user_id).all()     # (Get course from user's cart)
    user_ordered = Order.query.filter_by(user_id=user_id).all() # (Get registered course from database)
    # Display all student
    user_list = []

    # Total $ in cart
    cart_total = 0
    for course in user_cart:
        cart_total = cart_total + course.course_price


    # #---------- Display all student ----------#
    # if request.method == 'POST' and 'course_name' in request.form:
    #     course_name = request.form.get('course_name')

    #     display_courses = Order.query.filter_by(course_name=course_name).all()
    #     for course in display_courses:
    #         # users = User.query.filter_by(id=course.user_id).all()
    #         # for user in users:
    #         user = course.user_id
    #         user_list.append(user)

    #     return redirect(url_for('course'))
    #     return render_template('course.html', courses=courses, user_list=user_list, select=select, purchase_form=purchase_form, user_cart=user_cart, cart_total=cart_total)

    #---------- Search Bar ----------#
    if form.validate_on_submit():
        searched = form.search.data
        if form.search.data == '':
            flash('Enter something to search')
            return redirect(url_for('course'))

        else:
            courses = Course.query.filter(Course.course_name.like('%' + searched + '%'))
            
            flash(f'You searched {searched}')
            return render_template('course.html', courses=courses, user_list=user_list, select=select, purchase_form=purchase_form, user_cart=user_cart, cart_total=cart_total)


    #---------- Filter By ----------#
    if select == 'id':
        flash('Filtered by course id')
        courses = Course.query.order_by(Course.course_id)
    elif select == 'price':
        flash('Filtered by course price')
        courses = Course.query.order_by(Course.course_price)
    elif select == 'slot':
        flash('Filtered by course slot')
        courses = Course.query.order_by(Course.course_slot)


    #---------- Add To Cart ----------#
    if request.method == 'POST' and 'add_cart' in request.form:
        course_name = request.form.get('add_cart')
        slot_day = request.form.get('day')
        slot_time = request.form.get('time')

        course = Course.query.filter_by(course_name=course_name).first() # (Getting course object)

        # Avoid registering same course
        for order in user_ordered:
            if order.course_name == course_name:
                flash('This course is already registered')
                return redirect(url_for('course'))

        # Course capacity checking
        if course.course_slot == course.course_order:
            flash('This course is already full, register other course instead')
            return redirect(url_for('course'))
        
        # Avoid adding same course into cart
        for course_in_cart in user_cart:
            if course_in_cart.course_name == course_name:
                flash('This course is already in cart')
                return redirect(url_for('course'))

        if slot_day and slot_time != None:

            # Add to cart
            cart = Cart(user_id=user_id, 
                        course_name=course_name, 
                        course_price=course.course_price, 
                        slot_day=slot_day, 
                        slot_time=slot_time)
            db.session.add(cart)
            db.session.commit()
            flash(f'{course_name} added to cart')
            return redirect(url_for('course'))
            
        else:
            flash('Please select day and time before adding to cart')


    #---------- Remove From Cart ----------#
    if request.method == 'POST' and 'remove' in request.form:
        course_name = request.form.get('remove')
        for course in user_cart:
            if course.course_name == course_name:
                db.session.delete(course)
                db.session.commit()
                flash(f'{course_name} has been removed from cart')
                return redirect(url_for('course'))


    #---------- Checkout ----------#
    if request.method == 'POST' and 'checkout' in request.form:

        for register_course in user_cart:
            # Total order increment
            course = Course.query.filter_by(course_name=register_course.course_name).first() # (Getting course object)
            course.course_order += 1

            # Adding into Order database
            order = Order(user_id=user_id, course_name=register_course.course_name, slot_day=register_course.slot_day, slot_time=register_course.slot_time)
            db.session.add(order)

            # Delete course from cart
            db.session.delete(register_course)
            db.session.commit()

        flash('Courses successfully registered')
        return redirect(url_for('course'))


    #---------- Unregister ----------#
    if request.method == 'POST' and 'unregister' in request.form:
        course_name = request.form.get('unregister')
        for ordered in user_ordered:
            if ordered.course_name == course_name:

                # Total order decrement
                course = Course.query.filter_by(course_name=ordered.course_name).first() # (Getting course object)
                course.course_order -= 1

                # Remove from order (unregister)
                db.session.delete(ordered)
                db.session.commit()
        flash(f'You have successfully unregistered {course_name} class')
        return redirect(url_for('course'))

    return render_template('course.html', courses=courses, user_list=user_list, select=select, purchase_form=purchase_form, user_cart=user_cart, cart_total=cart_total, user_ordered=user_ordered)


# ---------- Redirect about ---------- #
@app.route('/about', methods=['GET', 'POST'])
@login_required
def about():
    # Cart & Checkout
    user_id = int(current_user.id)                              # (Get current user id)
    user_cart = Cart.query.filter_by(user_id=user_id).all()     # (Get course from user's cart)


    #---------- Remove From Cart ----------#
    if request.method == 'POST' and 'remove' in request.form:
        course_name = request.form.get('remove')
        for course in user_cart:
            if course.course_name == course_name:
                db.session.delete(course)
                db.session.commit()
                flash(f'{course_name} has been removed from cart')
                return redirect(url_for('about'))


    #---------- Checkout ----------#
    if request.method == 'POST' and 'checkout' in request.form:

        for register_course in user_cart:
            # Total order increment
            course = Course.query.filter_by(course_name=register_course.course_name).first() # (Getting course object)
            course.course_order += 1

            # Adding into Order database
            order = Order(user_id=user_id, course_name=register_course.course_name, slot_day=register_course.slot_day, slot_time=register_course.slot_time)
            db.session.add(order)

            # Delete course from cart
            db.session.delete(register_course)
            db.session.commit()

        flash('Courses successfully registered')
        return redirect(url_for('about'))

    return render_template('about.html', user_cart=user_cart)


# =============== #
# LOGOUT FUNCTION #
# =============== #

# ---------- Redirect index (logout) ---------- #
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(f"Logged out successfully")
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Create all database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)
    server = Server(app.wsgi_app)
    server.serve()