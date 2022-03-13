from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from forms import AddRealisation, AddGrain, AddProduction, Logmein
from flask_sqlalchemy import SQLAlchemy
import datetime as dt
import jinja2
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from functools import wraps


application = Flask(__name__)
application.config['SECRET_KEY'] = '123'
Bootstrap(application)
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintable.db'
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(application)

login_manager = LoginManager()
login_manager.init_app(application)



loader = jinja2.FileSystemLoader('temp')
# инициализация среды окружения, это нужно нам для того чтобы создать в этой среде функции (см. ниже)
env = jinja2.Environment(loader=loader, trim_blocks=True)


@application.template_filter('jround')
def jround(x):
    y = round(x, 2)
    return y


@application.template_filter('plus1')
def plus1(x):
    y = x + 1
    return y


env.filters['jround'] = jround
env.filters['plus1'] = plus1


class Realisation(db.Model):
    __tablename__ = "realisations"
    id = db.Column(db.Integer, primary_key=True)
    agent = db.Column(db.String(250), nullable=False)
    date = db.Column(db.Date(), nullable=False)
    production = db.Column(db.String(250), nullable=False)
    value = db.Column(db.Float(20), nullable=False)
    price = db.Column(db.Float(20), nullable=False)
    cost = db.Column(db.Float(20), nullable=False)


class Grain(db.Model):
    __tablename__ = "grains"
    id = db.Column(db.Integer, primary_key=True)
    agent = db.Column(db.String(250), nullable=False)
    date = db.Column(db.Date(), nullable=False)
    value = db.Column(db.Float(20), nullable=False)
    discount = db.Column(db.Float(20), nullable=False)
    final_value = db.Column(db.Float(20), nullable=False)
    price = db.Column(db.Float(20), nullable=False)
    cost = db.Column(db.Float(20), nullable=False)


class Production(db.Model):
    __tablename__ = "productions"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date(), nullable=False)
    highest = db.Column(db.Float(20), nullable=False)
    first = db.Column(db.Float(20), nullable=False)
    bran = db.Column(db.Float(20), nullable=False)
    waste = db.Column(db.Float(20), nullable=False)
    second = db.Column(db.Float(20), nullable=False)
    exit = db.Column(db.Float(20), nullable=False)


class Stock(UserMixin, db.Model):
    __tablename__ = "store"
    id = db.Column(db.Integer, primary_key=True)
    highest = db.Column(db.Float(20), nullable=False)
    first = db.Column(db.Float(20), nullable=False)
    bran = db.Column(db.Float(20), nullable=False)
    waste = db.Column(db.Float(20), nullable=False)
    second = db.Column(db.Float(20), nullable=False)
    grain = db.Column(db.Float(20), nullable=False)

#db.create_all()



@login_manager.user_loader
def load_user(user_id):
    return Stock.query.get(user_id)


def logged_only(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        try:
            if current_user.highest == 'melprodukt':

                return f(*args, **kwargs)
        except:

            return abort(403)
    return decorated_func


@application.route('/')
def main_page():
    return render_template('front.html')


@application.route('/g', methods=['GET', 'POST'])
def login():

    try:
        if current_user.highest == 'melprodukt':

            return redirect('/gf')
    except:
        login_form = Logmein()

        if login_form.validate_on_submit():
            login = login_form.name.data
            password = login_form.password.data

            user = Stock.query.filter_by(highest=login).first()

            try:
                if check_password_hash(user.first, password):

                    login_user(user)

                    return redirect('/gf')
                else:
                    flash('Неверный пароль')
                    return redirect('/g')
            except:
                flash('Неверный логин')
                pass

        return render_template('login.html', form=login_form)

@application.route('/gf', methods=['GET', 'POST'])
@logged_only
def front_page():
    stock = Stock.query.filter_by(id=1).first()

    return render_template('index.html', first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '),
                           onclick1='onclick=', onclick2='onclick=', onclick3='onclick=',
                           onclick11='onclick=', onclick22='onclick=', onclick33='onclick='
                           )


@application.route('/gf/real/add', methods=['GET', 'POST'])
def real_add():
    stock = Stock.query.filter_by(id=1).first()
    realisation_form = AddRealisation(date=dt.datetime.now())
    table = db.session.query(Realisation).filter(Realisation.date <= dt.datetime.now(), Realisation.date >= dt.datetime.now()-dt.timedelta(days=30)).order_by(Realisation.date).all()

    if realisation_form.validate_on_submit():
        stock_now = Stock.query.filter_by(id=1).first()

        new_realisation = Realisation(
            agent=realisation_form.agent.data,
            date=realisation_form.date.data,
            production=realisation_form.production.data,
            value=realisation_form.value.data,
            price=float(realisation_form.price.data.replace(',', '.')),
            cost=realisation_form.value.data * float(realisation_form.price.data.replace(',', '.'))
        )
        db.session.add(new_realisation)

        if realisation_form.production.data == 'Первый сорт':
            stock = stock_now.first
            stock_now.first = stock - realisation_form.value.data

        if realisation_form.production.data == 'Высший сорт':
            stock = stock_now.highest
            stock_now.highest = stock - realisation_form.value.data

        if realisation_form.production.data == 'Второй сорт':
            stock = stock_now.second
            stock_now.second = stock - realisation_form.value.data

        if realisation_form.production.data == 'Отруби':
            stock = stock_now.bran
            stock_now.bran = stock - realisation_form.value.data

        if realisation_form.production.data == 'Зерноотходы':
            stock = stock_now.waste
            stock_now.waste = stock - realisation_form.value.data

        db.session.commit()

        return redirect('/gf/real')

    return render_template('realadd.html', title='Реализация', form=realisation_form, first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '),
                           button='real', target='real', onclick2='onclick=', onclick3='onclick=',
                           table=reversed(table), onclick22='onclick=', onclick33='onclick=', bcolor='#a1ff92',
                           mright='50px'
                           )


@application.route('/gf/real', methods=['GET', 'POST'])
def real():
    stock = Stock.query.filter_by(id=1).first()
    realisation_form = AddRealisation(date=dt.datetime.now())
    table = db.session.query(Realisation).filter(Realisation.date <= dt.datetime.now(), Realisation.date >= dt.datetime.now()-dt.timedelta(days=30)).order_by(Realisation.date).all()

    return render_template('real.html', title='Реализация', form=realisation_form, first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '),
                           button='real', target='real', onclick11='onclick=', onclick2='onclick=', onclick3='onclick=',
                           table=reversed(table), onclick22='onclick=', onclick33='onclick=', bcolor='#a1ff92',
                           mright='50px'
                           )


@application.route('/gf/grain/add', methods=['GET', 'POST'])
def grain_add():
    stock = Stock.query.filter_by(id=1).first()
    grain_form = AddGrain(discount=0, date=dt.datetime.now())
    table = db.session.query(Grain).filter(Grain.date <= dt.datetime.now(),
                                                 Grain.date >= dt.datetime.now() - dt.timedelta(
                                                     days=30)).order_by(Grain.date).all()

    if grain_form.validate_on_submit():
        stock = Stock.query.filter_by(id=1).first()

        discount = float(grain_form.discount.data.replace(',', '.'))
        final_value = (grain_form.value.data - grain_form.value.data / 100 * discount)
        price = float(grain_form.price.data.replace(',', '.'))

        new_grain = Grain(
            agent=grain_form.agent.data,
            date=grain_form.date.data,
            value=grain_form.value.data,
            discount=discount,
            final_value=final_value,
            price=price,
            cost=final_value * price
        )
        db.session.add(new_grain)
        db.session.commit()

        stock.grain = grain_form.value.data + stock.grain
        db.session.commit()

        return redirect('/gf/grain')

    return render_template('grainadd.html', title='Зерно', form=grain_form, first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '),
                           table=reversed(table), button='grain', target='grain', onclick1='onclick=',
                           onclick2='onclick=', onclick3='onclick=', onclick11='onclick=', onclick33='onclick=',
                           bcolor='#ffa775', mright='350px'
                           )


@application.route('/gf/grain', methods=['GET', 'POST'])
def grain():
    stock = Stock.query.filter_by(id=1).first()
    grain_form = AddGrain(discount=0, date=dt.datetime.now())
    table = db.session.query(Grain).filter(Grain.date <= dt.datetime.now(),
                                                 Grain.date >= dt.datetime.now() - dt.timedelta(
                                                     days=30)).order_by(Grain.date).all()



    return render_template('grain.html', title='Зерно', form=grain_form, first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '), table=reversed(table),
                           button='grain', target='grain', onclick1='onclick=', onclick22='onclick=', onclick3='onclick=',
                           onclick11='onclick=', onclick33='onclick=', bcolor='#ffa775',
                           mright='350px'
                           )


@application.route('/gf/prod/add', methods=['GET', 'POST'])
def prod_add():
    prod_form = AddProduction(date=dt.datetime.now(), highest=0, second=0, waste=0)
    stock = Stock.query.filter_by(id=1).first()
    table = db.session.query(Production).filter(Production.date <= dt.datetime.now(),
                                           Production.date >= dt.datetime.now() - dt.timedelta(
                                               days=30)).order_by(Production.date).all()

    if prod_form.validate_on_submit():

        new_production = Production(
            date=prod_form.date.data,
            highest=prod_form.highest.data,
            first=prod_form.first.data,
            bran=prod_form.bran.data,
            waste=prod_form.waste.data,
            second=prod_form.second.data,
            exit=(prod_form.highest.data + prod_form.first.data + prod_form.second.data)/((prod_form.highest.data + prod_form.first.data + prod_form.second.data + prod_form.bran.data + prod_form.waste.data)/100)
        )

        db.session.add(new_production)

        stock.grain -= prod_form.highest.data + prod_form.first.data + prod_form.bran.data\
                       + prod_form.waste.data + prod_form.second.data

        stock.highest += prod_form.highest.data
        stock.first += prod_form.first.data
        stock.bran += prod_form.bran.data
        stock.waste += prod_form.waste.data
        stock.second += prod_form.second.data

        db.session.commit()

        return redirect('/gf/prod')

    return render_template('prodadd.html', title='Выработка', form=prod_form, first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '),
                           button='prod', target='prod', onclick1='onclick=', onclick2='onclick=',
                           table=reversed(table), onclick11='onclick=', onclick22='onclick=', bcolor='#ffcd6b',
                           mright='200px'
                           )


@application.route('/gf/prod', methods=['GET', 'POST'])
def prod():
    prod_form = AddProduction(date=dt.datetime.now(), highest=0, second=0, waste=0)
    stock = Stock.query.filter_by(id=1).first()
    table = db.session.query(Production).filter(Production.date <= dt.datetime.now(),
                                           Production.date >= dt.datetime.now() - dt.timedelta(
                                               days=30)).order_by(Production.date).all()

    return render_template('prod.html', title='Выработка', form=prod_form, first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '),
                           button='prod', target='prod', onclick1='onclick=', onclick2='onclick=', onclick33='onclick=',
                           table=reversed(table), onclick11='onclick=', onclick22='onclick=', bcolor='#ffcd6b',
                           mright='200px'
                           )


@application.route('/gf/real/del', methods=['GET', 'POST'])
def delete_real():
    stock = Stock.query.filter_by(id=1).first()

    del_id = request.form['agnt']
    del_value = request.form['vlue']
    del_product = request.form['prdct']
    line_to_delete = Realisation.query.get(del_id)
    db.session.delete(line_to_delete)

    if del_product == 'Первый сорт':
        stock.first += float(del_value)
    if del_product == 'Высший сорт':
        stock.highest += float(del_value)
    if del_product == 'Отруби':
        stock.bran += float(del_value)
    if del_product == 'Зерноотходы':
        stock.waste += float(del_value)
    if del_product == 'Второй сорт':
        stock.second += float(del_value)

    db.session.commit()
    return redirect('/gf/real')


@application.route('/gf/grain/del', methods=['GET', 'POST'])
def delete_grain():
    stock = Stock.query.filter_by(id=1).first()

    del_id = request.form['agnt']
    del_value = request.form['vlue']
    line_to_delete = Grain.query.get(del_id)
    db.session.delete(line_to_delete)

    stock.grain -= float(del_value)

    db.session.commit()

    return redirect('/gf/grain')


@application.route('/gf/prod/del', methods=['GET', 'POST'])
def delete_prod():
    stock = Stock.query.filter_by(id=1).first()

    del_id = request.form['agnt']
    del_highest = request.form['high']
    del_first = request.form['frst']
    del_second = request.form['scnd']
    del_bran = request.form['brn']
    del_waste = request.form['wst']

    line_to_delete = Production.query.get(del_id)
    db.session.delete(line_to_delete)

    stock.highest -= float(del_highest)
    stock.first -= float(del_first)
    stock.second -= float(del_second)
    stock.bran -= float(del_bran)
    stock.waste -= float(del_waste)
    stock.grain += float(del_highest) + float(del_bran) + float(del_waste) + float(del_second) + float(del_first)

    db.session.commit()
    return redirect('/gf/prod')


@application.route('/gf/real/edit', methods=['GET', 'POST'])
def real_edit():
    stock = Stock.query.filter_by(id=1).first()
    table = db.session.query(Realisation).filter(Realisation.date <= dt.datetime.now(),
                                                 Realisation.date >= dt.datetime.now() - dt.timedelta(
                                                     days=30)).order_by(Realisation.date).all()

    item_id = request.args.get('item_id')
    position = Realisation.query.filter_by(id=int(item_id)).first()

    current_highest = stock.highest
    current_first = stock.first
    current_second = stock.second
    current_bran = stock.bran
    current_waste = stock.waste

    if position.production == 'Высшийый сорт':
        stock.highest = current_highest + position.value
    if position.production == 'Первый сорт':
        stock.first = current_first + position.value
    if position.production == 'Отруби':
        stock.bran = current_bran + position.value
    if position.production == 'Зерноотходы':
        stock.waste = current_waste + position.value
    if position.production == 'Второй сорт':
        stock.second = current_second + position.value

    realisation_form = AddRealisation(agent=position.agent, date=position.date, production=position.production,
                                      value=position.value, price=position.price)

    if realisation_form.validate_on_submit():
        db.session.commit()
        stock = Stock.query.filter_by(id=1).first()

        if realisation_form.production.data == 'Первый сорт':
            stock.first -= realisation_form.value.data


        if realisation_form.production.data == 'Высший сорт':
            stock.highest -= realisation_form.value.data

        if realisation_form.production.data == 'Второй сорт':
            stock.second -= realisation_form.value.data

        if realisation_form.production.data == 'Отруби':
            stock.bran -= realisation_form.value.data

        if realisation_form.production.data == 'Зерноотходы':
            stock.waste -= realisation_form.value.data

        position.agent = realisation_form.agent.data
        position.date = realisation_form.date.data
        position.production = realisation_form.production.data
        position.value = realisation_form.value.data
        position.price = float(realisation_form.price.data.replace(',', '.'))
        position.cost = realisation_form.value.data * float(realisation_form.price.data.replace(',', '.'))

        db.session.commit()

        return redirect('/gf/real')

    return render_template('realadd.html', title='Реализация', form=realisation_form, first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '),
                           button='real', target='real', onclick2='onclick=', onclick3='onclick=',
                           table=reversed(table), onclick22='onclick=', onclick33='onclick=', bcolor='#a1ff92',
                           mright='50px'
                           )


@application.route('/gf/grain/edit', methods=['GET', 'POST'])
def grain_edit():
    stock = Stock.query.filter_by(id=1).first()
    table = db.session.query(Grain).filter(Grain.date <= dt.datetime.now(),
                                           Grain.date >= dt.datetime.now() - dt.timedelta(
                                               days=30)).order_by(Grain.date).all()

    item_id = request.args.get('item_id')
    position = Grain.query.get(item_id)

    grain_form = AddGrain(agent=position.agent, date=position.date, value=position.value, discount=position.discount,
                          price=position.price)

    if grain_form.validate_on_submit():
        stock.grain -= position.value
        db.session.commit()

        stock = Stock.query.filter_by(id=1).first()
        stock.grain += grain_form.value.data

        position.agent = grain_form.agent.data
        position.date = grain_form.date.data
        position.value = grain_form.value.data
        position.discount = float(grain_form.discount.data.replace(',', '.'))
        position.price = float(grain_form.price.data.replace(',', '.'))
        position.final_value = (grain_form.value.data - grain_form.value.data / 100 * position.discount)
        position.cost = position.final_value * position.price

        db.session.commit()

        return redirect('/gf/grain')

    return render_template('grainadd.html', title='Зерно', form=grain_form, first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '),
                           table=reversed(table), button='grain', target='grain', onclick1='onclick=',
                           onclick2='onclick=', onclick3='onclick=', onclick11='onclick=', onclick33='onclick=',
                           bcolor='#ffa775', mright='350px'
                           )


@application.route('/gf/prod/edit', methods=['GET', 'POST'])
def prod_edit():

    stock = Stock.query.filter_by(id=1).first()
    table = db.session.query(Production).filter(Production.date <= dt.datetime.now(),
                                                Production.date >= dt.datetime.now() - dt.timedelta(
                                                    days=30)).order_by(Production.date).all()

    item_id = request.args.get('item_id')
    position = Production.query.get(item_id)

    prod_form = AddProduction(date=position.date, highest=position.highest, second=position.second,
                              waste=position.waste, first=position.first, bran=position.bran
                              )

    if prod_form.validate_on_submit():

        stock.highest -= position.highest
        stock.first -= position.first
        stock.second -= position.second
        stock.bran -= position.bran
        stock.waste -= position.waste
        stock.grain += position.highest + position.first + position.second + position.bran + position.waste

        db.session.commit()

        stock = Stock.query.filter_by(id=1).first()

        position.highest = prod_form.highest.data
        position.first = prod_form.first.data
        position.second = prod_form.second.data
        position.bran = prod_form.bran.data
        position.waste = prod_form.waste.data

        stock.highest += prod_form.highest.data
        stock.first += prod_form.first.data
        stock.second += prod_form.second.data
        stock.bran += prod_form.bran.data
        stock.waste += prod_form.waste.data
        stock.grain -= prod_form.highest.data + prod_form.first.data + prod_form.second.data + prod_form.bran.data + prod_form.waste.data

        db.session.commit()

        return redirect('/gf/prod')

    return render_template('prodadd.html', title='Выработка', form=prod_form,
                           first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '),
                           button='prod', target='prod', onclick1='onclick=', onclick2='onclick=',
                           table=reversed(table), onclick11='onclick=', onclick22='onclick=', bcolor='#ffcd6b',
                           mright='200px'
                           )


@application.route('/gf/stat', methods=['GET', 'POST'])
def stat():
    stock = Stock.query.filter_by(id=1).first()
    now_year = dt.datetime.now().year
    past_year = (dt.datetime.now() - dt.timedelta(days=365)).year
    before_past_year = (dt.datetime.now() - dt.timedelta(days=730)).year

    grain_this_year = db.session.query(Grain).filter(
        Grain.date <= f'{now_year}-12-31', Grain.date >= f'{now_year}-01-01').all()

    grain_past_year = db.session.query(Grain).filter(
        Grain.date <= f'{past_year}-12-31', Grain.date >= f'{past_year}-01-01').all()

    grain_before_past_year = db.session.query(Grain).filter(
        Grain.date <= f'{before_past_year}-12-31', Grain.date >= f'{before_past_year}-01-01').all()

    grain_value_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                             'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}


    grain_cost_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                            'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}


    grain_value_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                             'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    grain_cost_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                            'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    grain_value_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                    'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    grain_cost_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                   'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    for i in grain_this_year:
        if i.date.month == 1:
            grain_value_this_year['jan'] += i.value
            grain_cost_this_year['jan'] += i.cost
        if i.date.month == 2:
            grain_value_this_year['feb'] += i.value
            grain_cost_this_year['feb'] += i.cost
        if i.date.month == 3:
            grain_value_this_year['mar'] += i.value
            grain_cost_this_year['mar'] += i.cost
        if i.date.month == 4:
            grain_value_this_year['apr'] += i.value
            grain_cost_this_year['apr'] += i.cost
        if i.date.month == 5:
            grain_value_this_year['may'] += i.value
            grain_cost_this_year['may'] += i.cost
        if i.date.month == 6:
            grain_value_this_year['jun'] += i.value
            grain_cost_this_year['jun'] += i.cost
        if i.date.month == 7:
            grain_value_this_year['jul'] += i.value
            grain_cost_this_year['jul'] += i.cost
        if i.date.month == 8:
            grain_value_this_year['aug'] += i.value
            grain_cost_this_year['aug'] += i.cost
        if i.date.month == 9:
            grain_value_this_year['sep'] += i.value
            grain_cost_this_year['sep'] += i.cost
        if i.date.month == 10:
            grain_value_this_year['oct'] += i.value
            grain_cost_this_year['oct'] += i.cost
        if i.date.month == 11:
            grain_value_this_year['nov'] += i.value
            grain_cost_this_year['nov'] += i.cost
        if i.date.month == 12:
            grain_value_this_year['dec'] += i.value
            grain_cost_this_year['dec'] += i.cost

    for i in grain_past_year:
        if i.date.month == 1:
            grain_value_past_year['jan'] += i.value
            grain_cost_past_year['jan'] += i.cost
        if i.date.month == 2:
            grain_value_past_year['feb'] += i.value
            grain_cost_past_year['feb'] += i.cost
        if i.date.month == 3:
            grain_value_past_year['mar'] += i.value
            grain_cost_past_year['mar'] += i.cost
        if i.date.month == 4:
            grain_value_past_year['apr'] += i.value
            grain_cost_past_year['apr'] += i.cost
        if i.date.month == 5:
            grain_value_past_year['may'] += i.value
            grain_cost_past_year['may'] += i.cost
        if i.date.month == 6:
            grain_value_past_year['jun'] += i.value
            grain_cost_past_year['jun'] += i.cost
        if i.date.month == 7:
            grain_value_past_year['jul'] += i.value
            grain_cost_past_year['jul'] += i.cost
        if i.date.month == 8:
            grain_value_past_year['aug'] += i.value
            grain_cost_past_year['aug'] += i.cost
        if i.date.month == 9:
            grain_value_past_year['sep'] += i.value
            grain_cost_past_year['sep'] += i.cost
        if i.date.month == 10:
            grain_value_past_year['oct'] += i.value
            grain_cost_past_year['oct'] += i.cost
        if i.date.month == 11:
            grain_value_past_year['nov'] += i.value
            grain_cost_past_year['nov'] += i.cost
        if i.date.month == 12:
            grain_value_past_year['dec'] += i.value
            grain_cost_past_year['dec'] += i.cost

    for i in grain_before_past_year:
        if i.date.month == 1:
            grain_value_before_past_year['jan'] += i.value
            grain_cost_before_past_year['jan'] += i.cost
        if i.date.month == 2:
            grain_value_before_past_year['feb'] += i.value
            grain_cost_before_past_year['feb'] += i.cost
        if i.date.month == 3:
            grain_value_before_past_year['mar'] += i.value
            grain_cost_before_past_year['mar'] += i.cost
        if i.date.month == 4:
            grain_value_before_past_year['apr'] += i.value
            grain_cost_before_past_year['apr'] += i.cost
        if i.date.month == 5:
            grain_value_before_past_year['may'] += i.value
            grain_cost_before_past_year['may'] += i.cost
        if i.date.month == 6:
            grain_value_before_past_year['jun'] += i.value
            grain_cost_before_past_year['jun'] += i.cost
        if i.date.month == 7:
            grain_value_before_past_year['jul'] += i.value
            grain_cost_before_past_year['jul'] += i.cost
        if i.date.month == 8:
            grain_value_before_past_year['aug'] += i.value
            grain_cost_before_past_year['aug'] += i.cost
        if i.date.month == 9:
            grain_value_before_past_year['sep'] += i.value
            grain_cost_before_past_year['sep'] += i.cost
        if i.date.month == 10:
            grain_value_before_past_year['oct'] += i.value
            grain_cost_before_past_year['oct'] += i.cost
        if i.date.month == 11:
            grain_value_before_past_year['nov'] += i.value
            grain_cost_before_past_year['nov'] += i.cost
        if i.date.month == 12:
            grain_value_before_past_year['dec'] += i.value
            grain_cost_before_past_year['dec'] += i.cost

    grain_value_this_year_all = sum(grain_value_this_year.values())
    grain_value_past_year_all = sum(grain_value_past_year.values())
    grain_value_before_past_year_all = sum(grain_value_before_past_year.values())

    grain_cost_this_year_all = sum(grain_cost_this_year.values())
    grain_cost_past_year_all = sum(grain_cost_past_year.values())
    grain_cost_before_past_year_all = sum(grain_cost_before_past_year.values())




    production_this_year = db.session.query(Production).filter(
        Production.date <= f'{now_year}-12-31', Production.date >= f'{now_year}-01-01').all()

    production_past_year = db.session.query(Production).filter(
        Production.date <= f'{past_year}-12-31', Production.date >= f'{past_year}-01-01').all()

    production_before_past_year = db.session.query(Production).filter(
        Production.date <= f'{before_past_year}-12-31', Production.date >= f'{before_past_year}-01-01').all()

    production_highest_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                    'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    production_first_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                  'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    production_second_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                   'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    production_bran_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                 'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    production_waste_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                  'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    production_highest_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                    'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    production_first_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                  'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    production_second_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                   'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    production_bran_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                 'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    production_waste_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                  'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    production_highest_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                           'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    production_first_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                         'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    production_second_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                          'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    production_bran_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                        'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    production_waste_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                         'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    for i in production_this_year:
        if i.date.month == 1:
            production_highest_this_year['jan'] += i.highest
            production_first_this_year['jan'] += i.first
            production_second_this_year['jan'] += i.second
            production_bran_this_year['jan'] += i.bran
            production_waste_this_year['jan'] += i.waste

        if i.date.month == 2:
            production_highest_this_year['feb'] += i.highest
            production_first_this_year['feb'] += i.first
            production_second_this_year['feb'] += i.second
            production_bran_this_year['feb'] += i.bran
            production_waste_this_year['feb'] += i.waste

        if i.date.month == 3:
            production_highest_this_year['mar'] += i.highest
            production_first_this_year['mar'] += i.first
            production_second_this_year['mar'] += i.second
            production_bran_this_year['mar'] += i.bran
            production_waste_this_year['mar'] += i.waste

        if i.date.month == 4:
            production_highest_this_year['apr'] += i.highest
            production_first_this_year['apr'] += i.first
            production_second_this_year['apr'] += i.second
            production_bran_this_year['apr'] += i.bran
            production_waste_this_year['apr'] += i.waste

        if i.date.month == 5:
            production_highest_this_year['may'] += i.highest
            production_first_this_year['may'] += i.first
            production_second_this_year['may'] += i.second
            production_bran_this_year['may'] += i.bran
            production_waste_this_year['may'] += i.waste

        if i.date.month == 6:
            production_highest_this_year['jun'] += i.highest
            production_first_this_year['jun'] += i.first
            production_second_this_year['jun'] += i.second
            production_bran_this_year['jun'] += i.bran
            production_waste_this_year['jun'] += i.waste

        if i.date.month == 7:
            production_highest_this_year['jul'] += i.highest
            production_first_this_year['jul'] += i.first
            production_second_this_year['jul'] += i.second
            production_bran_this_year['jul'] += i.bran
            production_waste_this_year['jul'] += i.waste

        if i.date.month == 8:
            production_highest_this_year['aug'] += i.highest
            production_first_this_year['aug'] += i.first
            production_second_this_year['aug'] += i.second
            production_bran_this_year['aug'] += i.bran
            production_waste_this_year['aug'] += i.waste

        if i.date.month == 9:
            production_highest_this_year['sep'] += i.highest
            production_first_this_year['sep'] += i.first
            production_second_this_year['sep'] += i.second
            production_bran_this_year['sep'] += i.bran
            production_waste_this_year['sep'] += i.waste

        if i.date.month == 10:
            production_highest_this_year['oct'] += i.highest
            production_first_this_year['oct'] += i.first
            production_second_this_year['oct'] += i.second
            production_bran_this_year['oct'] += i.bran
            production_waste_this_year['oct'] += i.waste

        if i.date.month == 11:
            production_highest_this_year['nov'] += i.highest
            production_first_this_year['nov'] += i.first
            production_second_this_year['nov'] += i.second
            production_bran_this_year['nov'] += i.bran
            production_waste_this_year['nov'] += i.waste

        if i.date.month == 12:
            production_highest_this_year['dec'] += i.highest
            production_first_this_year['dec'] += i.first
            production_second_this_year['dec'] += i.second
            production_bran_this_year['dec'] += i.bran
            production_waste_this_year['dec'] += i.waste

    for i in production_past_year:
        if i.date.month == 1:
            production_highest_past_year['jan'] += i.highest
            production_first_past_year['jan'] += i.first
            production_second_past_year['jan'] += i.second
            production_bran_past_year['jan'] += i.bran
            production_waste_past_year['jan'] += i.waste

        if i.date.month == 2:
            production_highest_past_year['feb'] += i.highest
            production_first_past_year['feb'] += i.first
            production_second_past_year['feb'] += i.second
            production_bran_past_year['feb'] += i.bran
            production_waste_past_year['feb'] += i.waste

        if i.date.month == 3:
            production_highest_past_year['mar'] += i.highest
            production_first_past_year['mar'] += i.first
            production_second_past_year['mar'] += i.second
            production_bran_past_year['mar'] += i.bran
            production_waste_past_year['mar'] += i.waste

        if i.date.month == 4:
            production_highest_past_year['apr'] += i.highest
            production_first_past_year['apr'] += i.first
            production_second_past_year['apr'] += i.second
            production_bran_past_year['apr'] += i.bran
            production_waste_past_year['apr'] += i.waste

        if i.date.month == 5:
            production_highest_past_year['may'] += i.highest
            production_first_past_year['may'] += i.first
            production_second_past_year['may'] += i.second
            production_bran_past_year['may'] += i.bran
            production_waste_past_year['may'] += i.waste

        if i.date.month == 6:
            production_highest_past_year['jun'] += i.highest
            production_first_past_year['jun'] += i.first
            production_second_past_year['jun'] += i.second
            production_bran_past_year['jun'] += i.bran
            production_waste_past_year['jun'] += i.waste

        if i.date.month == 7:
            production_highest_past_year['jul'] += i.highest
            production_first_past_year['jul'] += i.first
            production_second_past_year['jul'] += i.second
            production_bran_past_year['jul'] += i.bran
            production_waste_past_year['jul'] += i.waste

        if i.date.month == 8:
            production_highest_past_year['aug'] += i.highest
            production_first_past_year['aug'] += i.first
            production_second_past_year['aug'] += i.second
            production_bran_past_year['aug'] += i.bran
            production_waste_past_year['aug'] += i.waste

        if i.date.month == 9:
            production_highest_past_year['sep'] += i.highest
            production_first_past_year['sep'] += i.first
            production_second_past_year['sep'] += i.second
            production_bran_past_year['sep'] += i.bran
            production_waste_past_year['sep'] += i.waste

        if i.date.month == 10:
            production_highest_past_year['oct'] += i.highest
            production_first_past_year['oct'] += i.first
            production_second_past_year['oct'] += i.second
            production_bran_past_year['oct'] += i.bran
            production_waste_past_year['oct'] += i.waste

        if i.date.month == 11:
            production_highest_past_year['nov'] += i.highest
            production_first_past_year['nov'] += i.first
            production_second_past_year['nov'] += i.second
            production_bran_past_year['nov'] += i.bran
            production_waste_past_year['nov'] += i.waste

        if i.date.month == 12:
            production_highest_past_year['dec'] += i.highest
            production_first_past_year['dec'] += i.first
            production_second_past_year['dec'] += i.second
            production_bran_past_year['dec'] += i.bran
            production_waste_past_year['dec'] += i.waste

    for i in production_before_past_year:

        if i.date.month == 1:
            production_highest_before_past_year['jan'] += i.highest
            production_first_before_past_year['jan'] += i.first
            production_second_before_past_year['jan'] += i.second
            production_bran_before_past_year['jan'] += i.bran
            production_waste_before_past_year['jan'] += i.waste

        if i.date.month == 2:
            production_highest_before_past_year['feb'] += i.highest
            production_first_before_past_year['feb'] += i.first
            production_second_before_past_year['feb'] += i.second
            production_bran_before_past_year['feb'] += i.bran
            production_waste_before_past_year['feb'] += i.waste

        if i.date.month == 3:
            production_highest_before_past_year['mar'] += i.highest
            production_first_before_past_year['mar'] += i.first
            production_second_before_past_year['mar'] += i.second
            production_bran_before_past_year['mar'] += i.bran
            production_waste_before_past_year['mar'] += i.waste

        if i.date.month == 4:
            production_highest_before_past_year['apr'] += i.highest
            production_first_before_past_year['apr'] += i.first
            production_second_before_past_year['apr'] += i.second
            production_bran_before_past_year['apr'] += i.bran
            production_waste_before_past_year['apr'] += i.waste

        if i.date.month == 5:
            production_highest_before_past_year['may'] += i.highest
            production_first_before_past_year['may'] += i.first
            production_second_before_past_year['may'] += i.second
            production_bran_before_past_year['may'] += i.bran
            production_waste_before_past_year['may'] += i.waste

        if i.date.month == 6:
            production_highest_before_past_year['jun'] += i.highest
            production_first_before_past_year['jun'] += i.first
            production_second_before_past_year['jun'] += i.second
            production_bran_before_past_year['jun'] += i.bran
            production_waste_before_past_year['jun'] += i.waste

        if i.date.month == 7:
            production_highest_before_past_year['jul'] += i.highest
            production_first_before_past_year['jul'] += i.first
            production_second_before_past_year['jul'] += i.second
            production_bran_before_past_year['jul'] += i.bran
            production_waste_before_past_year['jul'] += i.waste

        if i.date.month == 8:
            production_highest_before_past_year['aug'] += i.highest
            production_first_before_past_year['aug'] += i.first
            production_second_before_past_year['aug'] += i.second
            production_bran_before_past_year['aug'] += i.bran
            production_waste_before_past_year['aug'] += i.waste

        if i.date.month == 9:
            production_highest_before_past_year['sep'] += i.highest
            production_first_before_past_year['sep'] += i.first
            production_second_before_past_year['sep'] += i.second
            production_bran_before_past_year['sep'] += i.bran
            production_waste_before_past_year['sep'] += i.waste

        if i.date.month == 10:
            production_highest_before_past_year['oct'] += i.highest
            production_first_before_past_year['oct'] += i.first
            production_second_before_past_year['oct'] += i.second
            production_bran_before_past_year['oct'] += i.bran
            production_waste_before_past_year['oct'] += i.waste

        if i.date.month == 11:
            production_highest_before_past_year['nov'] += i.highest
            production_first_before_past_year['nov'] += i.first
            production_second_before_past_year['nov'] += i.second
            production_bran_before_past_year['nov'] += i.bran
            production_waste_before_past_year['nov'] += i.waste

        if i.date.month == 12:
            production_highest_before_past_year['dec'] += i.highest
            production_first_before_past_year['dec'] += i.first
            production_second_before_past_year['dec'] += i.second
            production_bran_before_past_year['dec'] += i.bran
            production_waste_before_past_year['dec'] += i.waste

    production_highest_this_year_all = sum(production_highest_this_year.values())
    production_highest_past_year_all = sum(production_highest_past_year.values())
    production_highest_before_past_year_all = sum(production_highest_before_past_year.values())

    production_first_this_year_all = sum(production_first_this_year.values())
    production_first_past_year_all = sum(production_first_past_year.values())
    production_first_before_past_year_all = sum(production_first_before_past_year.values())

    production_second_this_year_all = sum(production_second_this_year.values())
    production_second_past_year_all = sum(production_second_past_year.values())
    production_second_before_past_year_all = sum(production_second_before_past_year.values())

    production_bran_this_year_all = sum(production_bran_this_year.values())
    production_bran_past_year_all = sum(production_bran_past_year.values())
    production_bran_before_past_year_all = sum(production_bran_before_past_year.values())

    production_waste_this_year_all = sum(production_waste_this_year.values())
    production_waste_past_year_all = sum(production_waste_past_year.values())
    production_waste_before_past_year_all = sum(production_waste_before_past_year.values())





    realisation_this_year = db.session.query(Realisation).filter(
        Realisation.date <= f'{now_year}-12-31', Realisation.date >= f'{now_year}-01-01').all()

    realisation_past_year = db.session.query(Realisation).filter(
        Realisation.date <= f'{past_year}-12-31', Realisation.date >= f'{past_year}-01-01').all()

    realisation_before_past_year = db.session.query(Realisation).filter(
        Realisation.date <= f'{before_past_year}-12-31', Realisation.date >= f'{before_past_year}-01-01').all()

    realisation_value_highest_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                           'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_cost_highest_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                          'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_value_first_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                         'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_cost_first_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                        'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_value_second_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                          'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_cost_second_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                         'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_value_bran_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                        'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_cost_bran_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                       'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_value_waste_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                         'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_cost_waste_this_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                        'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_value_highest_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                           'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_cost_highest_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                          'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_value_first_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                         'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_cost_first_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                        'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_value_second_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                          'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_cost_second_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                         'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_value_bran_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                        'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_cost_bran_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                       'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_value_waste_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                         'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_cost_waste_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                        'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_value_highest_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                                  'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_cost_highest_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                                 'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_value_first_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                                'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_cost_first_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                               'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_value_second_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                                 'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_cost_second_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                                'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_value_bran_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                               'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_cost_bran_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                              'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_value_waste_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                                'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    realisation_cost_waste_before_past_year = {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                                               'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0}

    for i in realisation_this_year:
        if i.date.month == 1:
            if i.production == 'Высший сорт':
                realisation_value_highest_this_year['jan'] += i.value
                realisation_cost_highest_this_year['jan'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_this_year['jan'] += i.value
                realisation_cost_first_this_year['jan'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_this_year['jan'] += i.value
                realisation_cost_second_this_year['jan'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_this_year['jan'] += i.value
                realisation_cost_bran_this_year['jan'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_this_year['jan'] += i.value
                realisation_cost_waste_this_year['jan'] += i.cost

        if i.date.month == 2:
            if i.production == 'Высший сорт':
                realisation_value_highest_this_year['feb'] += i.value
                realisation_cost_highest_this_year['feb'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_this_year['feb'] += i.value
                realisation_cost_first_this_year['feb'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_this_year['feb'] += i.value
                realisation_cost_second_this_year['feb'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_this_year['feb'] += i.value
                realisation_cost_bran_this_year['feb'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_this_year['feb'] += i.value
                realisation_cost_waste_this_year['feb'] += i.cost

        if i.date.month == 3:
            if i.production == 'Высший сорт':
                realisation_value_highest_this_year['mar'] += i.value
                realisation_cost_highest_this_year['mar'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_this_year['mar'] += i.value
                realisation_cost_first_this_year['mar'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_this_year['mar'] += i.value
                realisation_cost_second_this_year['mar'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_this_year['mar'] += i.value
                realisation_cost_bran_this_year['mar'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_this_year['mar'] += i.value
                realisation_cost_waste_this_year['mar'] += i.cost

        if i.date.month == 4:
            if i.production == 'Высший сорт':
                realisation_value_highest_this_year['apr'] += i.value
                realisation_cost_highest_this_year['apr'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_this_year['apr'] += i.value
                realisation_cost_first_this_year['apr'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_this_year['apr'] += i.value
                realisation_cost_second_this_year['apr'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_this_year['apr'] += i.value
                realisation_cost_bran_this_year['apr'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_this_year['apr'] += i.value
                realisation_cost_waste_this_year['apr'] += i.cost

        if i.date.month == 5:
            if i.production == 'Высший сорт':
                realisation_value_highest_this_year['may'] += i.value
                realisation_cost_highest_this_year['may'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_this_year['may'] += i.value
                realisation_cost_first_this_year['may'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_this_year['may'] += i.value
                realisation_cost_second_this_year['may'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_this_year['may'] += i.value
                realisation_cost_bran_this_year['may'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_this_year['may'] += i.value
                realisation_cost_waste_this_year['may'] += i.cost

        if i.date.month == 6:
            if i.production == 'Высший сорт':
                realisation_value_highest_this_year['jun'] += i.value
                realisation_cost_highest_this_year['jun'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_this_year['jun'] += i.value
                realisation_cost_first_this_year['jun'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_this_year['jun'] += i.value
                realisation_cost_second_this_year['jun'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_this_year['jun'] += i.value
                realisation_cost_bran_this_year['jun'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_this_year['jun'] += i.value
                realisation_cost_waste_this_year['jun'] += i.cost

        if i.date.month == 7:
            if i.production == 'Высший сорт':
                realisation_value_highest_this_year['jul'] += i.value
                realisation_cost_highest_this_year['jul'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_this_year['jul'] += i.value
                realisation_cost_first_this_year['jul'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_this_year['jul'] += i.value
                realisation_cost_second_this_year['jul'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_this_year['jul'] += i.value
                realisation_cost_bran_this_year['jul'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_this_year['jul'] += i.value
                realisation_cost_waste_this_year['jul'] += i.cost

        if i.date.month == 8:
            if i.production == 'Высший сорт':
                realisation_value_highest_this_year['aug'] += i.value
                realisation_cost_highest_this_year['aug'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_this_year['aug'] += i.value
                realisation_cost_first_this_year['aug'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_this_year['aug'] += i.value
                realisation_cost_second_this_year['aug'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_this_year['aug'] += i.value
                realisation_cost_bran_this_year['aug'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_this_year['aug'] += i.value
                realisation_cost_waste_this_year['aug'] += i.cost

        if i.date.month == 9:
            if i.production == 'Высший сорт':
                realisation_value_highest_this_year['sep'] += i.value
                realisation_cost_highest_this_year['sep'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_this_year['sep'] += i.value
                realisation_cost_first_this_year['sep'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_this_year['sep'] += i.value
                realisation_cost_second_this_year['sep'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_this_year['sep'] += i.value
                realisation_cost_bran_this_year['sep'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_this_year['sep'] += i.value
                realisation_cost_waste_this_year['sep'] += i.cost

        if i.date.month == 10:
            if i.production == 'Высший сорт':
                realisation_value_highest_this_year['oct'] += i.value
                realisation_cost_highest_this_year['oct'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_this_year['oct'] += i.value
                realisation_cost_first_this_year['oct'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_this_year['oct'] += i.value
                realisation_cost_second_this_year['oct'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_this_year['oct'] += i.value
                realisation_cost_bran_this_year['oct'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_this_year['oct'] += i.value
                realisation_cost_waste_this_year['oct'] += i.cost

        if i.date.month == 11:
            if i.production == 'Высший сорт':
                realisation_value_highest_this_year['nov'] += i.value
                realisation_cost_highest_this_year['nov'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_this_year['nov'] += i.value
                realisation_cost_first_this_year['nov'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_this_year['nov'] += i.value
                realisation_cost_second_this_year['nov'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_this_year['nov'] += i.value
                realisation_cost_bran_this_year['nov'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_this_year['nov'] += i.value
                realisation_cost_waste_this_year['nov'] += i.cost

        if i.date.month == 12:
            if i.production == 'Высший сорт':
                realisation_value_highest_this_year['dec'] += i.value
                realisation_cost_highest_this_year['dec'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_this_year['dec'] += i.value
                realisation_cost_first_this_year['dec'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_this_year['dec'] += i.value
                realisation_cost_second_this_year['dec'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_this_year['dec'] += i.value
                realisation_cost_bran_this_year['dec'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_this_year['dec'] += i.value
                realisation_cost_waste_this_year['dec'] += i.cost

    for i in realisation_past_year:
        if i.date.month == 1:
            if i.production == 'Высший сорт':
                realisation_value_highest_past_year['jan'] += i.value
                realisation_cost_highest_past_year['jan'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_past_year['jan'] += i.value
                realisation_cost_first_past_year['jan'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_past_year['jan'] += i.value
                realisation_cost_second_past_year['jan'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_past_year['jan'] += i.value
                realisation_cost_bran_past_year['jan'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_past_year['jan'] += i.value
                realisation_cost_waste_past_year['jan'] += i.cost

        if i.date.month == 2:
            if i.production == 'Высший сорт':
                realisation_value_highest_past_year['feb'] += i.value
                realisation_cost_highest_past_year['feb'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_past_year['feb'] += i.value
                realisation_cost_first_past_year['feb'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_past_year['feb'] += i.value
                realisation_cost_second_past_year['feb'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_past_year['feb'] += i.value
                realisation_cost_bran_past_year['feb'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_past_year['feb'] += i.value
                realisation_cost_waste_past_year['feb'] += i.cost

        if i.date.month == 3:
            if i.production == 'Высший сорт':
                realisation_value_highest_past_year['mar'] += i.value
                realisation_cost_highest_past_year['mar'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_past_year['mar'] += i.value
                realisation_cost_first_past_year['mar'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_past_year['mar'] += i.value
                realisation_cost_second_past_year['mar'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_past_year['mar'] += i.value
                realisation_cost_bran_past_year['mar'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_past_year['mar'] += i.value
                realisation_cost_waste_past_year['mar'] += i.cost

        if i.date.month == 4:
            if i.production == 'Высший сорт':
                realisation_value_highest_past_year['apr'] += i.value
                realisation_cost_highest_past_year['apr'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_past_year['apr'] += i.value
                realisation_cost_first_past_year['apr'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_past_year['apr'] += i.value
                realisation_cost_second_past_year['apr'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_past_year['apr'] += i.value
                realisation_cost_bran_past_year['apr'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_past_year['apr'] += i.value
                realisation_cost_waste_past_year['apr'] += i.cost

        if i.date.month == 5:
            if i.production == 'Высший сорт':
                realisation_value_highest_past_year['may'] += i.value
                realisation_cost_highest_past_year['may'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_past_year['may'] += i.value
                realisation_cost_first_past_year['may'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_past_year['may'] += i.value
                realisation_cost_second_past_year['may'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_past_year['may'] += i.value
                realisation_cost_bran_past_year['may'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_past_year['may'] += i.value
                realisation_cost_waste_past_year['may'] += i.cost

        if i.date.month == 6:
            if i.production == 'Высший сорт':
                realisation_value_highest_past_year['jun'] += i.value
                realisation_cost_highest_past_year['jun'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_past_year['jun'] += i.value
                realisation_cost_first_past_year['jun'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_past_year['jun'] += i.value
                realisation_cost_second_past_year['jun'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_past_year['jun'] += i.value
                realisation_cost_bran_past_year['jun'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_past_year['jun'] += i.value
                realisation_cost_waste_past_year['jun'] += i.cost

        if i.date.month == 7:
            if i.production == 'Высший сорт':
                realisation_value_highest_past_year['jul'] += i.value
                realisation_cost_highest_past_year['jul'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_past_year['jul'] += i.value
                realisation_cost_first_past_year['jul'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_past_year['jul'] += i.value
                realisation_cost_second_past_year['jul'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_past_year['jul'] += i.value
                realisation_cost_bran_past_year['jul'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_past_year['jul'] += i.value
                realisation_cost_waste_past_year['jul'] += i.cost

        if i.date.month == 8:
            if i.production == 'Высший сорт':
                realisation_value_highest_past_year['aug'] += i.value
                realisation_cost_highest_past_year['aug'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_past_year['aug'] += i.value
                realisation_cost_first_past_year['aug'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_past_year['aug'] += i.value
                realisation_cost_second_past_year['aug'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_past_year['aug'] += i.value
                realisation_cost_bran_past_year['aug'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_past_year['aug'] += i.value
                realisation_cost_waste_past_year['aug'] += i.cost

        if i.date.month == 9:
            if i.production == 'Высший сорт':
                realisation_value_highest_past_year['sep'] += i.value
                realisation_cost_highest_past_year['sep'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_past_year['sep'] += i.value
                realisation_cost_first_past_year['sep'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_past_year['sep'] += i.value
                realisation_cost_second_past_year['sep'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_past_year['sep'] += i.value
                realisation_cost_bran_past_year['sep'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_past_year['sep'] += i.value
                realisation_cost_waste_past_year['sep'] += i.cost

        if i.date.month == 10:
            if i.production == 'Высший сорт':
                realisation_value_highest_past_year['oct'] += i.value
                realisation_cost_highest_past_year['oct'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_past_year['oct'] += i.value
                realisation_cost_first_past_year['oct'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_past_year['oct'] += i.value
                realisation_cost_second_past_year['oct'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_past_year['oct'] += i.value
                realisation_cost_bran_past_year['oct'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_past_year['oct'] += i.value
                realisation_cost_waste_past_year['oct'] += i.cost

        if i.date.month == 11:
            if i.production == 'Высший сорт':
                realisation_value_highest_past_year['nov'] += i.value
                realisation_cost_highest_past_year['nov'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_past_year['nov'] += i.value
                realisation_cost_first_past_year['nov'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_past_year['nov'] += i.value
                realisation_cost_second_past_year['nov'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_past_year['nov'] += i.value
                realisation_cost_bran_past_year['nov'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_past_year['nov'] += i.value
                realisation_cost_waste_past_year['nov'] += i.cost

        if i.date.month == 12:
            if i.production == 'Высший сорт':
                realisation_value_highest_past_year['dec'] += i.value
                realisation_cost_highest_past_year['dec'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_past_year['dec'] += i.value
                realisation_cost_first_past_year['dec'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_past_year['dec'] += i.value
                realisation_cost_second_past_year['dec'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_past_year['dec'] += i.value
                realisation_cost_bran_past_year['dec'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_past_year['dec'] += i.value
                realisation_cost_waste_past_year['dec'] += i.cost

    for i in realisation_before_past_year:
        if i.date.month == 1:
            if i.production == 'Высший сорт':
                realisation_value_highest_before_past_year['jan'] += i.value
                realisation_cost_highest_before_past_year['jan'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_before_past_year['jan'] += i.value
                realisation_cost_first_before_past_year['jan'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_before_past_year['jan'] += i.value
                realisation_cost_second_before_past_year['jan'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_before_past_year['jan'] += i.value
                realisation_cost_bran_before_past_year['jan'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_before_past_year['jan'] += i.value
                realisation_cost_waste_before_past_year['jan'] += i.cost

        if i.date.month == 2:
            if i.production == 'Высший сорт':
                realisation_value_highest_before_past_year['feb'] += i.value
                realisation_cost_highest_before_past_year['feb'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_before_past_year['feb'] += i.value
                realisation_cost_first_before_past_year['feb'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_before_past_year['feb'] += i.value
                realisation_cost_second_before_past_year['feb'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_before_past_year['feb'] += i.value
                realisation_cost_bran_before_past_year['feb'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_before_past_year['feb'] += i.value
                realisation_cost_waste_before_past_year['feb'] += i.cost

        if i.date.month == 3:
            if i.production == 'Высший сорт':
                realisation_value_highest_before_past_year['mar'] += i.value
                realisation_cost_highest_before_past_year['mar'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_before_past_year['mar'] += i.value
                realisation_cost_first_before_past_year['mar'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_before_past_year['mar'] += i.value
                realisation_cost_second_before_past_year['mar'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_before_past_year['mar'] += i.value
                realisation_cost_bran_before_past_year['mar'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_before_past_year['mar'] += i.value
                realisation_cost_waste_before_past_year['mar'] += i.cost

        if i.date.month == 4:
            if i.production == 'Высший сорт':
                realisation_value_highest_before_past_year['apr'] += i.value
                realisation_cost_highest_before_past_year['apr'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_before_past_year['apr'] += i.value
                realisation_cost_first_before_past_year['apr'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_before_past_year['apr'] += i.value
                realisation_cost_second_before_past_year['apr'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_before_past_year['apr'] += i.value
                realisation_cost_bran_before_past_year['apr'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_before_past_year['apr'] += i.value
                realisation_cost_waste_before_past_year['apr'] += i.cost

        if i.date.month == 5:
            if i.production == 'Высший сорт':
                realisation_value_highest_before_past_year['may'] += i.value
                realisation_cost_highest_before_past_year['may'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_before_past_year['may'] += i.value
                realisation_cost_first_before_past_year['may'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_before_past_year['may'] += i.value
                realisation_cost_second_past_year['may'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_before_past_year['may'] += i.value
                realisation_cost_bran_past_year['may'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_before_past_year['may'] += i.value
                realisation_cost_waste_before_past_year['may'] += i.cost

        if i.date.month == 6:
            if i.production == 'Высший сорт':
                realisation_value_highest_before_past_year['jun'] += i.value
                realisation_cost_highest_before_past_year['jun'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_before_past_year['jun'] += i.value
                realisation_cost_first_before_past_year['jun'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_before_past_year['jun'] += i.value
                realisation_cost_second_before_past_year['jun'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_before_past_year['jun'] += i.value
                realisation_cost_bran_before_past_year['jun'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_before_past_year['jun'] += i.value
                realisation_cost_waste_before_past_year['jun'] += i.cost

        if i.date.month == 7:
            if i.production == 'Высший сорт':
                realisation_value_highest_before_past_year['jul'] += i.value
                realisation_cost_highest_before_past_year['jul'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_before_past_year['jul'] += i.value
                realisation_cost_first_before_past_year['jul'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_before_past_year['jul'] += i.value
                realisation_cost_second_before_past_year['jul'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_before_past_year['jul'] += i.value
                realisation_cost_bran_before_past_year['jul'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_before_past_year['jul'] += i.value
                realisation_cost_waste_before_past_year['jul'] += i.cost

        if i.date.month == 8:
            if i.production == 'Высший сорт':
                realisation_value_highest_before_past_year['aug'] += i.value
                realisation_cost_highest_before_past_year['aug'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_before_past_year['aug'] += i.value
                realisation_cost_first_before_past_year['aug'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_before_past_year['aug'] += i.value
                realisation_cost_second_before_past_year['aug'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_before_past_year['aug'] += i.value
                realisation_cost_bran_before_past_year['aug'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_before_past_year['aug'] += i.value
                realisation_cost_waste_before_past_year['aug'] += i.cost

        if i.date.month == 9:
            if i.production == 'Высший сорт':
                realisation_value_highest_before_past_year['sep'] += i.value
                realisation_cost_highest_before_past_year['sep'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_before_past_year['sep'] += i.value
                realisation_cost_first_before_past_year['sep'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_before_past_year['sep'] += i.value
                realisation_cost_second_before_past_year['sep'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_before_past_year['sep'] += i.value
                realisation_cost_bran_before_past_year['sep'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_before_past_year['sep'] += i.value
                realisation_cost_waste_before_past_year['sep'] += i.cost

        if i.date.month == 10:
            if i.production == 'Высший сорт':
                realisation_value_highest_before_past_year['oct'] += i.value
                realisation_cost_highest_before_past_year['oct'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_before_past_year['oct'] += i.value
                realisation_cost_first_before_past_year['oct'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_before_past_year['oct'] += i.value
                realisation_cost_second_before_past_year['oct'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_before_past_year['oct'] += i.value
                realisation_cost_bran_before_past_year['oct'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_before_past_year['oct'] += i.value
                realisation_cost_waste_before_past_year['oct'] += i.cost

        if i.date.month == 11:
            if i.production == 'Высший сорт':
                realisation_value_highest_before_past_year['nov'] += i.value
                realisation_cost_highest_before_past_year['nov'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_before_past_year['nov'] += i.value
                realisation_cost_first_before_past_year['nov'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_before_past_year['nov'] += i.value
                realisation_cost_second_before_past_year['nov'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_before_past_year['nov'] += i.value
                realisation_cost_bran_before_past_year['nov'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_past_year['nov'] += i.value
                realisation_cost_waste_past_year['nov'] += i.cost

        if i.date.month == 12:
            if i.production == 'Высший сорт':
                realisation_value_highest_before_past_year['dec'] += i.value
                realisation_cost_highest_before_past_year['dec'] += i.cost
            if i.production == 'Первый сорт':
                realisation_value_first_before_past_year['dec'] += i.value
                realisation_cost_first_before_past_year['dec'] += i.cost
            if i.production == 'Второй сорт':
                realisation_value_second_before_past_year['dec'] += i.value
                realisation_cost_second_before_past_year['dec'] += i.cost
            if i.production == 'Отруби':
                realisation_value_bran_before_past_year['dec'] += i.value
                realisation_cost_bran_before_past_year['dec'] += i.cost
            if i.production == 'Зерноотходы':
                realisation_value_waste_before_past_year['dec'] += i.value
                realisation_cost_waste_before_past_year['dec'] += i.cost

    realisation_value_highest_this_year_all = sum(realisation_value_highest_this_year.values())
    realisation_cost_highest_this_year_all = sum(realisation_cost_highest_this_year.values())

    realisation_value_first_this_year_all = sum(realisation_value_first_this_year.values())
    realisation_cost_first_this_year_all = sum(realisation_cost_first_this_year.values())

    realisation_value_second_this_year_all = sum(realisation_value_second_this_year.values())
    realisation_cost_second_this_year_all = sum(realisation_cost_second_this_year.values())

    realisation_value_bran_this_year_all = sum(realisation_value_bran_this_year.values())
    realisation_cost_bran_this_year_all = sum(realisation_cost_bran_this_year.values())

    realisation_value_waste_this_year_all = sum(realisation_value_waste_this_year.values())
    realisation_cost_waste_this_year_all = sum(realisation_cost_waste_this_year.values())

    realisation_value_highest_past_year_all = sum(realisation_value_highest_past_year.values())
    realisation_cost_highest_past_year_all = sum(realisation_cost_highest_past_year.values())

    realisation_value_first_past_year_all = sum(realisation_value_first_past_year.values())
    realisation_cost_first_past_year_all = sum(realisation_cost_first_past_year.values())

    realisation_value_second_past_year_all = sum(realisation_value_second_past_year.values())
    realisation_cost_second_past_year_all = sum(realisation_cost_second_past_year.values())

    realisation_value_bran_past_year_all = sum(realisation_value_bran_past_year.values())
    realisation_cost_bran_past_year_all = sum(realisation_cost_bran_past_year.values())

    realisation_value_waste_past_year_all = sum(realisation_value_waste_past_year.values())
    realisation_cost_waste_past_year_all = sum(realisation_cost_waste_past_year.values())

    realisation_value_highest_before_past_year_all = sum(realisation_value_highest_before_past_year.values())
    realisation_cost_highest_before_past_year_all = sum(realisation_cost_highest_before_past_year.values())

    realisation_value_first_before_past_year_all = sum(realisation_value_first_before_past_year.values())
    realisation_cost_first_before_past_year_all = sum(realisation_cost_first_before_past_year.values())

    realisation_value_second_before_past_year_all = sum(realisation_value_second_before_past_year.values())
    realisation_cost_second_before_past_year_all = sum(realisation_cost_second_before_past_year.values())

    realisation_value_bran_before_past_year_all = sum(realisation_value_bran_before_past_year.values())
    realisation_cost_bran_before_past_year_all = sum(realisation_cost_bran_before_past_year.values())

    realisation_value_waste_before_past_year_all = sum(realisation_value_waste_before_past_year.values())
    realisation_cost_waste_before_past_year_all = sum(realisation_cost_waste_before_past_year.values())


    return render_template('stat.html', first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '),
                           onclick1='onclick=', onclick2='onclick=', onclick3='onclick=',
                           onclick11='onclick=', onclick22='onclick=', onclick33='onclick=',
                           bcolor='#add8e6', title='Статистика', mright='500px',
                           grain_value_this_year=grain_value_this_year, now_year=now_year,
                           grain_cost_this_year=grain_cost_this_year,
                           grain_value_this_year_all=grain_value_this_year_all,
                           grain_value_past_year_all=grain_value_past_year_all,
                           grain_value_before_past_year_all=grain_value_before_past_year_all,
                           grain_cost_this_year_all=grain_cost_this_year_all,
                           grain_cost_past_year_all=grain_cost_past_year_all,
                           grain_cost_before_past_year_all=grain_cost_before_past_year_all,
                           grain_value_past_year=grain_value_past_year, past_year=past_year,
                           grain_cost_past_year=grain_cost_past_year,
                           grain_value_before_past_year=grain_value_before_past_year, before_past_year=before_past_year,
                           grain_cost_before_past_year=grain_cost_before_past_year,
                           production_highest_this_year=production_highest_this_year,
                           production_first_this_year=production_first_this_year,
                           production_second_this_year=production_second_this_year,
                           production_bran_this_year=production_bran_this_year,
                           production_waste_this_year=production_waste_this_year,
                           production_highest_past_year=production_highest_past_year,
                           production_first_past_year=production_first_past_year,
                           production_second_past_year=production_second_past_year,
                           production_bran_past_year=production_bran_past_year,
                           production_waste_past_year=production_waste_past_year,
                           production_highest_before_past_year=production_highest_before_past_year,
                           production_first_before_past_year=production_first_before_past_year,
                           production_second_before_past_year=production_second_before_past_year,
                           production_bran_before_past_year=production_bran_before_past_year,
                           production_waste_before_past_year=production_waste_before_past_year,
                           production_highest_this_year_all=production_highest_this_year_all,
                           production_highest_past_year_all=production_highest_past_year_all,
                           production_highest_before_past_year_all=production_highest_before_past_year_all,
                           production_first_this_year_all=production_first_this_year_all,
                           production_first_past_year_all=production_first_past_year_all,
                           production_first_before_past_year_all=production_first_before_past_year_all,
                           production_second_this_year_all=production_second_this_year_all,
                           production_second_past_year_all=production_second_past_year_all,
                           production_second_before_past_year_all=production_second_before_past_year_all,
                           production_bran_this_year_all=production_bran_this_year_all,
                           production_bran_past_year_all=production_bran_past_year_all,
                           production_bran_before_past_year_all=production_bran_before_past_year_all,
                           production_waste_this_year_all=production_waste_this_year_all,
                           production_waste_past_year_all=production_waste_past_year_all,
                           production_waste_before_past_year_all=production_waste_before_past_year_all,
                           realisation_value_highest_this_year=realisation_value_highest_this_year,
                           realisation_cost_highest_this_year=realisation_cost_highest_this_year,
                           realisation_value_first_this_year=realisation_value_first_this_year,
                           realisation_cost_first_this_year=realisation_cost_first_this_year,
                           realisation_value_second_this_year=realisation_value_second_this_year,
                           realisation_cost_second_this_year=realisation_cost_second_this_year,
                           realisation_value_bran_this_year=realisation_value_bran_this_year,
                           realisation_cost_bran_this_year=realisation_cost_bran_this_year,
                           realisation_value_waste_this_year=realisation_value_waste_this_year,
                           realisation_cost_waste_this_year=realisation_cost_waste_this_year,
                           realisation_value_highest_past_year=realisation_value_highest_past_year,
                           realisation_cost_highest_past_year=realisation_cost_highest_past_year,
                           realisation_value_first_past_year=realisation_value_first_past_year,
                           realisation_cost_first_past_year=realisation_cost_first_past_year,
                           realisation_value_second_past_year=realisation_value_second_past_year,
                           realisation_cost_second_past_year=realisation_cost_second_past_year,
                           realisation_value_bran_past_year=realisation_value_bran_past_year,
                           realisation_cost_bran_past_year=realisation_cost_bran_past_year,
                           realisation_value_waste_past_year=realisation_value_waste_past_year,
                           realisation_cost_waste_past_year=realisation_cost_waste_past_year,
                           realisation_value_highest_before_past_year=realisation_value_highest_before_past_year,
                           realisation_cost_highest_before_past_year=realisation_cost_highest_before_past_year,
                           realisation_value_first_before_past_year=realisation_value_first_before_past_year,
                           realisation_cost_first_before_past_year=realisation_cost_first_before_past_year,
                           realisation_value_second_before_past_year=realisation_value_second_before_past_year,
                           realisation_cost_second_before_past_year=realisation_cost_second_before_past_year,
                           realisation_value_bran_before_past_year=realisation_value_bran_before_past_year,
                           realisation_cost_bran_before_past_year=realisation_cost_bran_before_past_year,
                           realisation_value_waste_before_past_year=realisation_value_waste_before_past_year,
                           realisation_cost_waste_before_past_year=realisation_cost_waste_before_past_year,
                           realisation_value_highest_this_year_all=realisation_value_highest_this_year_all,
                           realisation_cost_highest_this_year_all=realisation_cost_highest_this_year_all,
                           realisation_value_first_this_year_all=realisation_value_first_this_year_all,
                           realisation_cost_first_this_year_all=realisation_cost_first_this_year_all,
                           realisation_value_second_this_year_all=realisation_value_second_this_year_all,
                           realisation_cost_second_this_year_all=realisation_cost_second_this_year_all,
                           realisation_value_bran_this_year_all=realisation_value_bran_this_year_all,
                           realisation_cost_bran_this_year_all=realisation_cost_bran_this_year_all,
                           realisation_value_waste_this_year_all=realisation_value_waste_this_year_all,
                           realisation_cost_waste_this_year_all=realisation_cost_waste_this_year_all,
                           realisation_value_highest_past_year_all=realisation_value_highest_past_year_all,
                           realisation_cost_highest_past_year_all=realisation_cost_highest_past_year_all,
                           realisation_value_first_past_year_all=realisation_value_first_past_year_all,
                           realisation_cost_first_past_year_all=realisation_cost_first_past_year_all,
                           realisation_value_second_past_year_all=realisation_value_second_past_year_all,
                           realisation_cost_second_past_year_all=realisation_cost_second_past_year_all,
                           realisation_value_bran_past_year_all=realisation_value_bran_past_year_all,
                           realisation_cost_bran_past_year_all=realisation_cost_bran_past_year_all,
                           realisation_value_waste_past_year_all=realisation_value_waste_past_year_all,
                           realisation_cost_waste_past_year_all=realisation_cost_waste_past_year_all,
                           realisation_value_highest_before_past_year_all=realisation_value_highest_before_past_year_all,
                           realisation_cost_highest_before_past_year_all=realisation_cost_highest_before_past_year_all,
                           realisation_value_first_before_past_year_all=realisation_value_first_before_past_year_all,
                           realisation_cost_first_before_past_year_all=realisation_cost_first_before_past_year_all,
                           realisation_value_second_before_past_year_all=realisation_value_second_before_past_year_all,
                           realisation_cost_second_before_past_year_all=realisation_cost_second_before_past_year_all,
                           realisation_value_bran_before_past_year_all=realisation_value_bran_before_past_year_all,
                           realisation_cost_bran_before_past_year_all=realisation_cost_bran_before_past_year_all,
                           realisation_value_waste_before_past_year_all=realisation_value_waste_before_past_year_all,
                           realisation_cost_waste_before_past_year_all=realisation_cost_waste_before_past_year_all,
    )

if __name__ == '__main__':
    application.run(host='0.0.0.0')
