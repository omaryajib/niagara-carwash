from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Length

class WashRecordForm(FlaskForm):
    filiale = SelectField('Filiale', choices=[('Aachen', 'Aachen'), ('Dinslaken', 'Dinslaken'), ('Neuss', 'Neuss')], validators=[DataRequired()])
    submit = SubmitField('Add Wash')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20, message="اسم المستخدم خاص يكون بين 4 و 20 حرف.")])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message="كلمة المرور خاص تكون على الأقل 6 حروف.")])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="كلمة المرور وتأكيد كلمة المرور غير متطابقين.")])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')