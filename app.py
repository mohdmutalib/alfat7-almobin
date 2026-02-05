from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# إنشاء تطبيق Flask
app = Flask(__name__)

# تكوينات التطبيق
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///members.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# إنشاء كائن قاعدة البيانات
db = SQLAlchemy(app)

# قائمة الرتب العسكرية بالترتيب من الأعلى إلى الأدنى
MILITARY_RANKS = [
    ('', 'اختر الرتبة العسكرية'),
    ('مشير', 'مشير'),
    ('فريق أول', 'فريق أول'),
    ('فريق', 'فريق'),
    ('لواء', 'لواء'),
    ('عميد', 'عميد'),
    ('عقيد', 'عقيد'),
    ('رائد', 'رائد'),
    ('نقيب', 'نقيب'),
    ('ملازم أول', 'ملازم أول'),
    ('ملازم', 'ملازم'),
    ('مساعد أول', 'مساعد أول'),
    ('مساعد', 'مساعد'),
    ('رقيب أول', 'رقيب أول'),
    ('رقيب', 'رقيب'),
    ('عريف', 'عريف'),
    ('جندي أول', 'جندي أول'),
    ('جندي', 'جندي')
]

# نموذج قاعدة البيانات للعضو
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    military_rank = db.Column(db.String(50))  # حقل الرتبة العسكرية
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Member {self.name}>'

# نموذج تسجيل العضو
class RegistrationForm(FlaskForm):
    name = StringField('الاسم الكامل', validators=[DataRequired(), Length(min=3, max=100)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[
        DataRequired(),
        Length(min=6, message='كلمة المرور يجب أن تكون 6 أحرف على الأقل')
    ])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[
        DataRequired(),
        EqualTo('password', message='كلمات المرور غير متطابقة')
    ])
    phone = StringField('رقم الهاتف')
    address = StringField('العنوان')
    military_rank = SelectField('الرتبة العسكرية', choices=MILITARY_RANKS, validators=[DataRequired()])
    submit = SubmitField('تسجيل عضو جديد')

# نموذج البحث
class SearchForm(FlaskForm):
    search_term = StringField('بحث', validators=[DataRequired()])
    submit = SubmitField('بحث')

# إنشاء قاعدة البيانات
with app.app_context():
    db.create_all()

# الصفحة الرئيسية
@app.route('/')
def index():
    try:
        members_count = Member.query.count()
    except:
        members_count = 0
    return render_template('index.html', members_count=members_count)

# صفحة تسجيل عضو جديد
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # التحقق من عدم وجود البريد الإلكتروني مسبقاً
        existing_member = Member.query.filter_by(email=form.email.data).first()
        
        if existing_member:
            flash('هذا البريد الإلكتروني مسجل مسبقاً!', 'error')
            return redirect(url_for('register'))
        
        # إنشاء عضو جديد
        new_member = Member(
            name=form.name.data,
            email=form.email.data,                                                          ## to make it work online following the below ##
            password=generate_password_hash(form.password.data),    #remove the whole last argument (method='pbkdf2:sha256')
            phone=form.phone.data or None,                                                          #add "or None" after "data" => (phone.data or None)
            address=form.address.data or None,                                                      #add "or None" after "data" => (address.data or None)
            military_rank=form.military_rank.data
        )
        
        # حفظ في قاعدة البيانات
        db.session.add(new_member)
        db.session.commit()
        
        flash('تم تسجيل العضو بنجاح!', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html', form=form)

# صفحة البحث عن عضو
@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    results = []
    
    if form.validate_on_submit():
        search_term = form.search_term.data
        
        # البحث في قاعدة البيانات
        results = Member.query.filter(
            Member.name.contains(search_term)
        ).all()
        
        if not results:
            flash('لم يتم العثور على أعضاء بهذا الاسم', 'info')
    
    return render_template('search.html', form=form, results=results)

# صفحة نتائج البحث
@app.route('/results')
def results():
    search_term = request.args.get('search', '')
    
    if search_term:
        results = Member.query.filter(
            Member.name.contains(search_term)
        ).all()
    else:
        results = []
    
    return render_template('results.html', results=results, search_term=search_term)

# صفحة عرض جميع الأعضاء
@app.route('/all-members')
def all_members():
    members = Member.query.order_by(Member.registration_date.desc()).all()
    return render_template('results.html', results=members, search_term='')

# صفحة إحصاءات الرتب
@app.route('/ranks-stats')
def ranks_stats():
    # إحصائيات حسب الرتبة
    ranks_stats = {}
    all_members = Member.query.all()
    
    for member in all_members:
        rank = member.military_rank if member.military_rank else 'غير محدد'
        if rank in ranks_stats:
            ranks_stats[rank] += 1
        else:
            ranks_stats[rank] = 1
    
    # تحويل إلى قائمة للعرض
    stats_list = [{'rank': rank, 'count': count} for rank, count in ranks_stats.items()]
    stats_list.sort(key=lambda x: x['count'], reverse=True)
    
    return render_template('ranks_stats.html', ranks_stats=stats_list)

# تشغيل التطبيق
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)