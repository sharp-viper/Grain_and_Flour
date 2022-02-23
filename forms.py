from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DateField, FloatField, SelectField, HiddenField
from wtforms.validators import DataRequired


class AddRealisation(FlaskForm):
    agent = StringField("Контрагент", validators=[DataRequired()])
    date = DateField("Дата", validators=[DataRequired()])
    production = SelectField("Продукция", validators=[DataRequired()], choices=['Первый сорт', 'Высший сорт', 'Отруби', 'Зерноотходы', 'Второй сорт'])
    value = FloatField("Количество (кг)", validators=[DataRequired()])
    price = FloatField("Цена (руб/кг)", validators=[DataRequired()])
    submit = SubmitField("Добавить")


class AddGrain(FlaskForm):
    agent = StringField("Контрагент", validators=[DataRequired()])
    date = DateField("Дата", validators=[DataRequired()])
    value = FloatField("Количество (кг)", validators=[DataRequired()])
    discount = StringField("Скидка", validators=[DataRequired()])
    price = StringField("Цена (руб/кг)", validators=[DataRequired()])
    submit = SubmitField("Добавить")


class AddProduction(FlaskForm):
    date = DateField("Дата")
    highest = FloatField("Высший сорт (кг)")
    first = FloatField("Первый сорт (кг)")
    bran = FloatField("Отруби (кг)", validators=[DataRequired()])
    waste = FloatField("Зерноотходы")
    second = FloatField("Второй сорт (кг)")
    submit = SubmitField("Добавить")