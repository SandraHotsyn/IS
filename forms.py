from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, NumberRange
from flask_wtf.file import FileField, FileAllowed

class ProductForm(FlaskForm):
    name = StringField("Назва", validators=[DataRequired()])
    price = FloatField("Ціна", validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField("Кількість", validators=[DataRequired(), NumberRange(min=0)])
    image_url = StringField("Зображення")
    image = FileField("Зображення", validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], "❌ Лише зображення!")])
    description = TextAreaField("Опис", validators=[DataRequired()])
    subcategory_id = SelectField("Підкатегорія", coerce=int)
