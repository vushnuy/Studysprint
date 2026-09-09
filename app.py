
import os, random
from flask import Flask, request, jsonify, render_template, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///studysprint.db").replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    chapter = db.Column(db.String(150), nullable=False)
    language = db.Column(db.String(10), nullable=False, default="en")
    question = db.Column(db.Text, nullable=False)
    a = db.Column(db.Text, nullable=False)
    b = db.Column(db.Text, nullable=False)
    c = db.Column(db.Text, nullable=False)
    d = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Integer, nullable=False)
    explanation = db.Column(db.Text, nullable=False)

class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student = db.Column(db.String(120))
    class_name = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    chapter = db.Column(db.String(150), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

def seed():
    if Question.query.count():
        return
    seed_data = [
        ("10","Science","Electricity","en","What is the SI unit of electric current?","Volt","Ampere","Ohm","Watt",1,"Electric current is measured in ampere (A)."),
        ("10","Science","Electricity","en","If V = 12 V and R = 4 Ω, the current is:","2 A","3 A","4 A","48 A",1,"By Ohm's law, I = V/R = 3 A."),
        ("10","Science","Life Processes","en","Which organelle is called the powerhouse of the cell?","Nucleus","Mitochondria","Ribosome","Vacuole",1,"Mitochondria release usable energy through cellular respiration."),
        ("10","Maths","Quadratic Equations","en","The discriminant of ax²+bx+c=0 is:","b²+4ac","b²−4ac","4ac−b²","a²−4bc",1,"The discriminant is D = b² − 4ac."),
        ("10","Maths","Quadratic Equations","en","If the discriminant is zero, the roots are:","Real and equal","Real and unequal","Not real","Always negative",0,"D = 0 gives two real and equal roots."),
        ("10","Science","Light","en","The SI unit of power of a lens is:","Metre","Dioptre","Watt","Pascal",1,"Lens power is measured in dioptres (D)."),
        ("10","SST","Nationalism in India","en","The Non-Cooperation Movement was launched under the leadership of:","Mahatma Gandhi","Subhas Chandra Bose","Bhagat Singh","Jawaharlal Nehru",0,"Mahatma Gandhi launched the movement in 1920."),
        ("10","English","Grammar","en","Choose the correct form: She ___ to school every day.","go","goes","going","gone",1,"With singular subject 'she', the simple present form is 'goes'."),
        ("9","Maths","Polynomials","en","The degree of 7x³−2x+1 is:","1","2","3","7",2,"The highest exponent is 3."),
        ("8","Maths","Linear Equations","en","Solve: x + 7 = 12.","3","5","7","19",1,"Subtract 7 from both sides: x = 5.")
    ]
    for row in seed_data:
        db.session.add(Question(class_name=row[0],subject=row[1],chapter=row[2],language=row[3],
            question=row[4],a=row[5],b=row[6],c=row[7],d=row[8],answer=row[9],explanation=row[10]))
    db.session.commit()

with app.app_context():
    db.create_all()
    seed()

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/meta")
def meta():
    classes = [x[0] for x in db.session.query(Question.class_name).distinct().order_by(Question.class_name)]
    subjects = [{"class_name":x[0],"subject":x[1]} for x in db.session.query(Question.class_name,Question.subject).distinct().order_by(Question.class_name,Question.subject)]
    chapters = [{"class_name":x[0],"subject":x[1],"chapter":x[2]} for x in db.session.query(Question.class_name,Question.subject,Question.chapter).distinct().order_by(Question.class_name,Question.subject,Question.chapter)]
    return jsonify(classes=classes,subjects=subjects,chapters=chapters)

@app.post("/api/quiz")
def quiz():
    x=request.json or {}
    required=["class_name","subject","chapter","language","count"]
    if any(not str(x.get(k,"")).strip() for k in required):
        return jsonify(error="Please select all fields."),400
    q=Question.query.filter_by(class_name=x["class_name"],subject=x["subject"],chapter=x["chapter"]).filter(
        (Question.language==x["language"]) | (Question.language=="bi")
    ).all()
    if not q:
        return jsonify(error="No questions found for this exact Class + Subject + Chapter."),404
    n=int(x["count"])
    random.shuffle(q)
    q=(q*((n+len(q)-1)//len(q)))[:n]
    return jsonify(questions=[{"id":r.id,"question":r.question,"options":[r.a,r.b,r.c,r.d],
                              "answer":r.answer,"explanation":r.explanation} for r in q],
                   config={k:x[k] for k in ["class_name","subject","chapter"]})

@app.post("/api/attempt")
def attempt():
    x=request.json or {}
    db.session.add(Attempt(student=x.get("student",""),class_name=x["class_name"],subject=x["subject"],
                           chapter=x["chapter"],score=x["score"],total=x["total"],accuracy=x["accuracy"]))
    db.session.commit()
    return jsonify(ok=True)

def admin_required():
    return not session.get("admin")

@app.post("/api/admin/login")
def admin_login():
    if (request.json or {}).get("password") != ADMIN_PASSWORD:
        return jsonify(error="Wrong password."),401
    session["admin"]=True
    return jsonify(ok=True)

@app.post("/api/admin/logout")
def admin_logout():
    session.clear()
    return jsonify(ok=True)

@app.get("/api/admin/status")
def admin_status():
    return jsonify(logged=bool(session.get("admin")))

@app.get("/api/admin/questions")
def admin_questions():
    if admin_required(): return jsonify(error="Login required."),401
    rows=Question.query.order_by(Question.id.desc()).all()
    return jsonify(questions=[{"id":r.id,"class_name":r.class_name,"subject":r.subject,"chapter":r.chapter,"language":r.language,"question":r.question} for r in rows])

@app.post("/api/admin/questions")
def add_question():
    if admin_required(): return jsonify(error="Login required."),401
    x=request.json or {}
    fields=["class_name","subject","chapter","language","question","a","b","c","d","answer","explanation"]
    if any(not str(x.get(k,"")).strip() for k in fields):
        return jsonify(error="All fields are required."),400
    db.session.add(Question(**{k:x[k] for k in fields}))
    db.session.commit()
    return jsonify(ok=True)

@app.delete("/api/admin/questions/<int:qid>")
def delete_question(qid):
    if admin_required(): return jsonify(error="Login required."),401
    r=db.session.get(Question,qid)
    if not r: return jsonify(error="Question not found."),404
    db.session.delete(r);db.session.commit()
    return jsonify(ok=True)

@app.get("/api/admin/progress")
def progress():
    if admin_required(): return jsonify(error="Login required."),401
    rows=Attempt.query.order_by(Attempt.id.desc()).all()
    return jsonify(attempts=[{"student":r.student,"class_name":r.class_name,"subject":r.subject,"chapter":r.chapter,
                              "score":r.score,"total":r.total,"accuracy":r.accuracy,
                              "created_at":r.created_at.isoformat() if r.created_at else ""} for r in rows])

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
