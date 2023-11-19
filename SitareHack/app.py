# importing necessary modules
from flask import Flask, render_template, request, session, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
# from flask_mail import Mail
from werkzeug.utils import secure_filename
import json
import os
from datetime import datetime
import math
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd



directory = "C:\\Users\\Shravan Bishnoi\\OneDrive\\Desktop\\SitareHack\\static\\" # set this acc to your dir
local_server = True
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.config['UPLOAD_FOLDER'] = f'{directory}data'
app.config['UPLOAD_SCANNEDCOPY_FOLDER'] = f'{directory}scannedcopy'
app.secret_key = 'super-secret-key'
login_manager = LoginManager()
ALLOWED_EXTENSIONS = {'xlsx', 'pdf', 'docx'}
login_manager.login_view = "login"
login_manager.init_app(app)
db = SQLAlchemy(app)


### Database Tables ###
class studentdata(db.Model, UserMixin):
    __tablename__ = 'student_data'
    s_id = db.Column(db.Integer, primary_key=True)
    s_name = db.Column(db.String(255), nullable = False)
    roll_no = db.Column(db.Integer, nullable = False,  unique=True)
    email = db.Column(db.Text(1000), nullable = False,  unique=True)
    password = db.Column(db.Text(100), nullable = False)
    semester = db.Column(db.Text(100), nullable=False)
    img = db.Column(db.String(1000), default="profile.jpeg")

    def get_id(self):
        """Returns user Id"""
        return str(self.s_id)
    
    def get_name(self):
        """Returns user Id"""
        return str(self.s_name)
    
class profdata(db.Model, UserMixin):
    __tablename__ = 'professor_data'
    p_id = db.Column(db.Integer, primary_key=True)
    p_name = db.Column(db.String(255), nullable = False)
    email = db.Column(db.Text(1000), nullable = False,  unique=True)
    password = db.Column(db.Text(100), nullable = False)
    img = db.Column(db.String(1000), default="profile.jpeg")

    def get_id(self):
        """Returns user Id"""
        return str(self.p_id)
    
    def get_name(self):
        """Returns user Id"""
        return str(self.p_name)
    
class pcourse(db.Model, UserMixin):
    __tablename__ = 'pcourse'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    p_id = db.Column(db.Integer, db.ForeignKey('professor_data.p_id'))
    semester = db.Column(db.Text(1000), nullable = False)
    course = db.Column(db.Text(1000), nullable = False)

    def get_id(self):
        """Returns user Id"""
        return str(self.p_id)
    
    def get_name(self):
        """Returns user Id"""
        return str(self.course)

class UploadedFile(db.Model):
    __tablename__ = 'uploaded_files'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    semester = db.Column(db.Text(1000), nullable = False)
    course = db.Column(db.Text(1000), nullable = False)
    filename = db.Column(db.String(100), nullable=False)

class SemesterCourse(db.Model):
    __tablename__ = 'semestercourse'
    id = db.Column(db.Integer, primary_key=True)
    semester = db.Column(db.Text(50))
    course_name = db.Column(db.String(100))

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    professor_id = db.Column(db.Integer, db.ForeignKey('professor_data.p_id'), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Scannedcopy(db.Model):
    __tablename__ = 'scanned_copy'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable = False)
    semester = db.Column(db.Text(100), nullable = False)
    course = db.Column(db.Text(1000), nullable = False)
    filename = db.Column(db.String(1000), nullable=False)

with app.app_context():
    db.create_all()

### First click ###
@app.route("/")
def home():
    return render_template("login.html")


### For Login ###
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["emailid"]
        password = request.form['password']
        user = studentdata.query.filter_by(email = email, password=password).first()
        if user:
            login_user(user)
            flash("Logged in successfully", 'success')
            return redirect(url_for('student_dashboard', name=user.s_name, rollno=user.roll_no, semester=user.semester))
        else:
            user = profdata.query.filter_by(email = email, password=password).first()
            if user:
                login_user(user)
                flash("Logged in successfully", 'success')
                return redirect(url_for('professor_dashboard', name=user.p_name, pid=user.p_id))
            else:
                flash("Email/Password is incorrect", 'error')
                return redirect(url_for('login'))
    return render_template("login.html")


### ROUTE FOR REGISTER ###
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        s_name = request.form['name']
        email = request.form['emailid']
        password = request.form['password']
        confirm_pass = request.form['confirm_password']
        if 'agree' in request.form:
            if password != confirm_pass:
                flash('Passwords do not match!', 'error')
                return redirect(url_for('admin'))
            # Check if the username is already taken
            existing_user = profdata.query.filter_by(email = email).first()
            if existing_user:
                flash('Username already exists.', 'error')
                return redirect(url_for('admin'))
            # Create a new user
            new_user = profdata(p_name=s_name, email = email, password=password)
            db.session.add(new_user) # new user added
            db.session.commit()      # commit changes
            flash('Registration successful!', 'success')
            return redirect(url_for('professor_dashboard', name=new_user.p_name, pid=new_user.p_id))
        else:
            sem = request.form['semester']
            roll_no = request.form['rollno']
            if password != confirm_pass:
                flash('Passwords do not match!', 'error')
                return redirect(url_for('admin'))
        
            # Check if the username is already taken
            existing_user = studentdata.query.filter_by(roll_no=roll_no).first()
            if existing_user:
                flash('Username already exists.', 'error')
                return redirect(url_for('admin'))
            # Create a new user
            new_user = studentdata(s_name=s_name, roll_no=roll_no, email = email, password=password, semester=sem)
            db.session.add(new_user) # new user added
            db.session.commit()      # commit changes
            flash('Registration successful!', 'success')
            return redirect(url_for('student_dashboard', name=new_user.s_name, rollno=new_user.roll_no, semester=new_user.semester))
    return render_template('admin.html')

### Professor Dashboard page ###
@app.route("/prof_dashboard/<string:name>/<int:pid>")
def professor_dashboard(name, pid):
    course = pcourse.query.filter_by(p_id=pid).all()
    prof_obj = profdata.query.filter_by(p_id=pid).first()
    cdetail = {}
    sems = []
    for i in course:
        if i.semester not in cdetail:
            cdetail[i.semester] = [i.course]
        else:
            cdetail[i.semester].append(i.course)
        if i.semester not in sems:
            sems.append(i.semester)
    student_lst = {}
    files = {}
    for i in sems:
        student_lst[i] = studentdata.query.filter_by(semester=i).all()
        files_temp = {}
        for j in cdetail[i]:
            files_temp[j] = UploadedFile.query.filter_by(semester=i, course=j).all()
        files[i] = files_temp
    return render_template('prof_dashboard.html', name=name, course=cdetail, student_lst=student_lst, files=files, img=prof_obj.img)


### Helper for calculating marks for a student ###
def _calculateMarks(name, rollno, semester, courses):
    """Returns a dict with keys as test name and values as marks"""
    tests = ['ia1', 'ia2', 'ia3', 'final']
    tests_cap = ['IA-1', 'IA-2', 'IA-3', 'Final']
    marks_dict1 = {}
    for i in range(len(courses)):
        marks_dict = {}
        for j in range(len(tests)):
            file_path = app.config['UPLOAD_FOLDER']
            file_name = f'{file_path}\\sem{semester}_{tests[j]}_{courses[i]}.xlsx'
            if os.path.exists(file_name):
                df = pd.read_excel(file_name)
                df.columns = ['rollno', 'name', 'email', 'marks', 'feedback']
                marksdf = df[df['rollno']==rollno]
                if not marksdf.empty:
                    marks = float(marksdf['marks'].values[0])
                    feedback = marksdf['feedback'].values[0]
                else:
                    marks = ('NA','-')
                    feedback = ''
                marks_dict[tests_cap[j]] = (marks,feedback)
            else:
                marks_dict[tests_cap[j]] = ('NA','-')
        marks_dict1[courses[i]] = marks_dict
    overall_report = {}
    for course, data in marks_dict1.items():
        for test, mark in data.items():
            if type(mark[0])==int or type(mark[0])==float:
                if test not in overall_report:
                    overall_report[test] = mark[0]
                else:
                    overall_report[test] = mark[0]
    for test, mark in overall_report.items():
        if test!='Final':
            overall_report[test] = (mark/(25*len(marks_dict1)))*(100)
        else:
            overall_report[test] = (mark/(50*len(marks_dict1)))*(100)
    return (marks_dict1, overall_report)


### Student Dashboard page ###
@app.route("/student_dashboard/<string:name>/<int:rollno>/<int:semester>")
def student_dashboard(name, rollno, semester):
    courses = SemesterCourse.query.filter_by(semester=semester).all()
    student_obj = studentdata.query.filter_by(roll_no=rollno).first()
    courselst = []
    for i in courses:
        courselst.append(i.course_name)
    marks_dict = _calculateMarks(name, rollno, semester, courselst)
    ann = Announcement.query.filter_by(semester=semester).order_by(Announcement.timestamp.desc()).all()
    announcements = {}
    count = 0
    for announcement in ann:
        pobj = profdata.query.filter_by(p_id=announcement.professor_id).first()
        announcements[count] = (pobj.p_name, announcement.timestamp.strftime('%Y-%m-%d'), announcement.message)
        count += 1
    return render_template('student_dashboard.html', name=name, rollno=rollno, email=student_obj.email, semester=semester, courses=courselst, img=student_obj.img, marks=marks_dict, announcements=announcements)


@app.route('/coursedetail', methods=['GET', 'POST'])
def coursedetail():
    if request.method == 'POST':
        id = request.form['id']
        p_id = request.form['pid']
        sem = request.form['semester']
        course = request.form['course']
        new_detail = pcourse(id=id, p_id = p_id, semester = sem, course=course)
        db.session.add(new_detail) # new user added
        db.session.commit()      # commit changes
        flash('Details saved successfully!', 'success')
        return render_template('coursedetail.html')
    return render_template('coursedetail.html')


### PROF UPLOADER FUNCTION ###
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.referrer)
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.referrer)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        _, file_extension = os.path.splitext(filename)
        filename = 'sem'+request.form['semester']+'_'+request.form['test']+'_'+request.form['course']+file_extension
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            semester_file = UploadedFile.query.filter_by(filename=filename).first()
            if semester_file:
                db.session.delete(semester_file)
                db.session.commit()
        file.save(file_path)
        new_file = UploadedFile(semester=request.form['semester'], course=request.form['course'], filename=filename)
        db.session.add(new_file)
        db.session.commit()
        flash('File uploaded successfully', 'success')
        return redirect(request.referrer)
    flash("Invalid file format. Allowed extensions: .xlsx, .xls, .pdf, .docx", 'error')
    return redirect(request.referrer)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


### DOWNLOAD FUNCTION ###
@app.route('/download_pdf/<path:filename>', methods=['GET'])
def download_pdf(filename):
    try:
        directory = app.config['UPLOAD_FOLDER']
        return send_from_directory(directory, filename, as_attachment=True)
    except:
        flash("Outline not available", 'error')
    return redirect(request.referrer)


### PROFESSOR ANNOUCEMENT FUNCTION ###
@app.route('/professor/announcement', methods=['GET', 'POST'])
def professor_announcement():
    if request.method == 'POST':
        semester = request.form.get('semester')
        message = request.form.get('message')
        professor_id = current_user.p_id
        new_announcement = Announcement(professor_id=professor_id, semester=semester, message=message)
        db.session.add(new_announcement)
        db.session.commit()
        flash("Annoucement successfully sent!", 'success')
        return redirect(url_for('professor_dashboard', name=current_user.p_name , pid= professor_id))
    return render_template('prof_dashboard.html')


### UPLOAD SCANNED ANSWERSHEETS ###
@app.route('/upload_scannedcopy', methods=['POST'])
def upload_scannedcopy():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.referrer)
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.referrer)
    if file and allowed_file(file.filename):
        name = request.form['name']
        sem = request.form['semester']
        course = request.form['course']
        test = request.form['test']
        filename = secure_filename(file.filename)
        _, file_extension = os.path.splitext(filename)
        filename = f"{name}_{course}_{test}_sem{sem}{file_extension}"
        file_path = os.path.join(app.config['UPLOAD_SCANNEDCOPY_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            semester_file = Scannedcopy.query.filter_by(filename=filename).first()
            if semester_file:
                db.session.delete(semester_file)
                db.session.commit()
        file.save(file_path)
        new_file = Scannedcopy(name=name, semester=sem, course=course, filename=filename)
        db.session.add(new_file)
        db.session.commit()
        flash('File uploaded successfully', 'success')
        return redirect(request.referrer)
    flash("Invalid file format. Allowed extensions: .pdf", 'error')
    return redirect(request.referrer)


login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return profdata.query.get(int(user_id))

### LOGOUT FUNCTION ###
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.run(debug=True)
