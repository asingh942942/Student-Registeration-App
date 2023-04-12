from flask import Flask, redirect, url_for, request, render_template, json, abort, session, flash
import hashlib
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, login_user, logout_user, login_required, LoginManager, UserMixin

app = Flask(__name__)

# set optional bootswatch theme
app.config['FLASK_ADMIN_SWATCH'] = 'lumen'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///registeration.sqlite"
app.secret_key = 's123834'

db = SQLAlchemy(app)

class_student = db.Table('class_student', db.Column('class_id', db.Integer, db.ForeignKey("classes.id")), db.Column('student_id', db.Integer, db.ForeignKey("student.id")), db.Column('grade_id', db.Integer, db.ForeignKey("grades.id"))) 

class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String, unique=False, nullable=False)
  username = db.Column(db.String, unique=True, nullable=False)
  password = db.Column(db.String, unique=True, nullable=False)
  role = db.Column(db.String, unique=False, nullable=False)
  students = db.relationship('Student', backref=db.backref('user', uselist=False))

  def check_password(self, password):
    return self.password == password

class Classes(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  instructor = db.Column(db.String, unique=False, nullable=False)
  class_name = db.Column(db.String, unique=True, nullable=False)
  class_times = db.Column(db.String, unique=False, nullable=False)
  cur_students = db.Column(db.Integer, unique=False)
  cap = db.Column(db.Integer, unique=False, nullable=False)
  students = db.relationship('Student', secondary='class_student', backref='class')

class Student(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String, unique=False, nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
  courses = db.relationship('Classes', secondary='class_student', backref='student')

class Grades(db.Model):
  grade = db.Column(db.Integer, unique=False, nullable=True)
  student_id = db.Column(db.Integer, db.ForeignKey('student.id'), primary_key=True)
  class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
  grades_student = db.relationship('Student', backref='student')
  grades_classes = db.relationship('Classes', backref='class')

class PkView(ModelView):
  column_display_pk = True

admin = Admin(app, name='Admin', template_mode='bootstrap3')
admin.add_view(PkView(User, db.session))
admin.add_view(PkView(Classes, db.session))
admin.add_view(PkView(Student, db.session))
admin.add_view(PkView(Grades, db.session))

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.before_request
def check_for_admin():
  if request.path.startswith('/admin/') and not current_user.role == "admin":
    return abort(403)

@app.before_first_request
def initialize():
  db.create_all()

@login_manager.user_loader
def load_user(user_id):
  return User.query.get(user_id)

@app.route('/index', methods=["GET", "POST"])
@app.route('/')
@login_required
def index():
  if(current_user.role == "student"):
    if request.method == "POST":
      buttonid = request.get_json().get("dataset")
      course = Classes.query.filter_by(id=buttonid).first()
      current_student = Student.query.filter_by(user_id=current_user.id).first()
      if request.get_json().get("action") == "add":
        if (current_student.courses.count(course) > 0) or (course.cur_students == course.cap):
          return abort(403)
        course.cur_students += 1
        current_student.courses.append(course)
      elif request.get_json().get("action") == "remove":
        if current_student.courses.count(course) <= 0:
          return abort(403)
        course.cur_students -= 1
        current_student.courses.remove(course)
    db.session.commit()
    return render_template("student.html", student=current_user.name, classes=Classes.query.all(), added_classes=Student.query.filter_by(user_id=current_user.id).first().courses)
  elif(current_user.role == "teacher"):
    if request.method == "POST":
      buttonid = request.get_json().get("dataset")
      course = Classes.query.filter_by(id=buttonid).first()
      return json.dumps(f"/students/{course.id}")
    return render_template("teacher.html", teacher=current_user.name, added_classes=Classes.query.filter_by(instructor=current_user.name).all())
  elif(current_user.role == "admin"):
    return redirect("/admin")
@app.route('/login')
def login_page():
  return render_template('login.html')

@app.route('/students/<id>', methods=['GET', 'POST'])
def students(id):
  if request.method == "POST":
    student = Student.query.filter_by(name=request.form.get("student-name")).first()
    get_grade = request.form.get("student-grade")
    # if student already exists, update their grade
    if Grades.query.filter_by(student_id=student.id).first():
      Grades.query.filter_by(student_id=student.id).first().grade = get_grade
      db.session.commit()
      return render_template("enrolled_students.html", enrolled_students = Classes.query.filter_by(id=id).first().students, grades = Grades.query.filter_by(class_id=id).all())
    
    # adds student, class, and corresponding grade if it does not exist
    add_grade = Grades(grade=get_grade, student_id=student.id, class_id=id)
    db.session.add(add_grade)
    db.session.commit()
  return render_template("enrolled_students.html", enrolled_students = Classes.query.filter_by(id=id).first().students, grades = Grades.query.filter_by(class_id=id).all())

@app.route('/login', methods=['POST'])
def login():
  person_username = request.form.get("username")
  person_password = request.form.get("password")
  user = User.query.filter_by(username=person_username).first()
  if user is None or not user.check_password(person_password):
    return redirect("/login")
  if user.is_authenticated:
    login_user(user)
    return redirect("/index")

@app.route("/signup")
def signup_page():
  return render_template("signup.html")

@app.route("/signup", methods=['POST'])
def signup():
  person_name = request.form.get("name")
  person_username = request.form.get("username")
  #person_password = hashlib.md5(request.get_json().get("password").encode())
  person_password = request.form.get("password")
  person_role = request.form.get("role")
  user = User(name=person_name, username=person_username, password=person_password, role=person_role)
  db.session.add(user)
  if user.role == "student":
    student = User.query.filter_by(name=user.name).first()
    add_student = Student(name=student.name, user_id=student.id)
    db.session.add(add_student)
  db.session.commit()
  db.create_all()
  return redirect("/login")

@app.route("/logout")
@login_required
def logout():
  session.clear()
  logout_user()
  return redirect("/login")

@app.route('/database', methods=['GET'])
def database():
  return render_template("database.html", users = Student.query.all())

if __name__ == "__main__":
  app.run(debug=True)