from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from forms import AddRealisation, AddGrain, AddProduction
from flask_sqlalchemy import SQLAlchemy
import datetime as dt
import jinja2


app = Flask(__name__)
app.config['SECRET_KEY'] = '123'
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintable.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

loader = jinja2.FileSystemLoader('temp')
# инициализация среды окружения
env = jinja2.Environment(loader=loader, trim_blocks=True)


@app.template_filter('jround')
def jround(x):
    y = round(x, 2)
    return y


@app.template_filter('plus1')
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


class Stock(db.Model):
    __tablename__ = "store"
    id = db.Column(db.Integer, primary_key=True)
    highest = db.Column(db.Float(20), nullable=False)
    first = db.Column(db.Float(20), nullable=False)
    bran = db.Column(db.Float(20), nullable=False)
    waste = db.Column(db.Float(20), nullable=False)
    second = db.Column(db.Float(20), nullable=False)
    grain =  db.Column(db.Float(20), nullable=False)

# db.create_all()


@app.route('/', methods=['GET', 'POST'])
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


@app.route('/real/add', methods=['GET', 'POST'])
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

        return redirect('/real')

    return render_template('realadd.html', title='Реализация', form=realisation_form, first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '),
                           button='real', target='real', onclick2='onclick=', onclick3='onclick=',
                           table=reversed(table), onclick22='onclick=', onclick33='onclick='
                           )


@app.route('/real', methods=['GET', 'POST'])
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
                           table=reversed(table), onclick22='onclick=', onclick33='onclick='
                           )


@app.route('/grain/add', methods=['GET', 'POST'])
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

        return redirect('/grain')

    return render_template('grainadd.html', title='Зерно', form=grain_form, first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '),
                           table=reversed(table), button='grain', target='grain', onclick1='onclick=',
                           onclick2='onclick=', onclick3='onclick=', onclick11='onclick=', onclick33='onclick='
                           )


@app.route('/grain', methods=['GET', 'POST'])
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
                           onclick11='onclick=', onclick33='onclick='
                           )


@app.route('/prod/add', methods=['GET', 'POST'])
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
            second=prod_form.second.data
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

        return redirect('/prod')

    return render_template('prodadd.html', title='Выработка', form=prod_form, first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '),
                           button='prod', target='prod', onclick1='onclick=', onclick2='onclick=',
                           table=reversed(table), onclick11='onclick=', onclick22='onclick='
                           )


@app.route('/prod', methods=['GET', 'POST'])
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
                           table=reversed(table), onclick11='onclick=', onclick22='onclick='
                           )


@app.route('/real/del', methods=['GET', 'POST'])
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
    return redirect('/real')


@app.route('/grain/del', methods=['GET', 'POST'])
def delete_grain():
    stock = Stock.query.filter_by(id=1).first()

    del_id = request.form['agnt']
    del_value = request.form['vlue']
    line_to_delete = Grain.query.get(del_id)
    db.session.delete(line_to_delete)

    stock.grain -= float(del_value)

    db.session.commit()

    return redirect('/grain')


@app.route('/prod/del', methods=['GET', 'POST'])
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
    return redirect('/prod')


@app.route('/real/edit', methods=['GET', 'POST'])
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

        return redirect('/real')

    return render_template('realadd.html', title='Реализация', form=realisation_form, first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '),
                           button='real', target='real', onclick2='onclick=', onclick3='onclick=',
                           table=reversed(table), onclick22='onclick=', onclick33='onclick='
                           )


@app.route('/grain/edit', methods=['GET', 'POST'])
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

        db.session.commit()

        return redirect('/grain')

    return render_template('grainadd.html', title='Зерно', form=grain_form, first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '),
                           table=reversed(table), button='grain', target='grain', onclick1='onclick=',
                           onclick2='onclick=', onclick3='onclick=', onclick11='onclick=', onclick33='onclick='
                           )


@app.route('/prod/edit', methods=['GET', 'POST'])
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

        return redirect('/prod')

    return render_template('prodadd.html', title='Выработка', form=prod_form,
                           first='{:,}'.format(stock.first).replace(',', ' '),
                           second='{:,}'.format(stock.second).replace(',', ' '),
                           highest='{:,}'.format(stock.highest).replace(',', ' '),
                           bran='{:,}'.format(stock.bran).replace(',', ' '),
                           waste='{:,}'.format(stock.waste).replace(',', ' '),
                           grain='{:,}'.format(stock.grain).replace(',', ' '),
                           button='prod', target='prod', onclick1='onclick=', onclick2='onclick=',
                           table=reversed(table), onclick11='onclick=', onclick22='onclick='
                           )


if __name__ == '__main__':
    app.run(debug=True)
