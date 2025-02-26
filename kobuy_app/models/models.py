from kobuy_app import db
from flask_login import UserMixin
import datetime
from werkzeug.security import check_password_hash, generate_password_hash


# ------------------------ユーザーとロールを関連付ける------------------------
roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)
# ------------------------ユーザー------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    lastname = db.Column(db.String, nullable=False)
    firstname = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    grade = db.Column(db.Integer, nullable=False)
    cls = db.Column(db.Integer, nullable=False)
    num = db.Column(db.Integer, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        return role_name in [role.name for role in self.roles]



    def __repr__(self):
        return f'<User {self.username}>'

# ------------------------ロール------------------------
class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    def __repr__(self):
        return f'<Role {self.name}>'

# ------------------------メニュー------------------------
class Menu(db.Model):
    __tablename__ = 'menu'
    id = db.Column(db.Integer, primary_key=True)
    orders = db.Column(db.Integer, nullable=False, default=0)
    productname = db.Column(db.String(255))
    price = db.Column(db.String(255))
    buy_cnt = db.Column(db.Integer) # 購入された回数
    explanation = db.Column(db.String(255))
    product_image = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('menu_category.id'))

    def item_price(id):
        item = Menu.query.filter_by(id=id).first()
        if item is None:
            print(f"商品ID {id} が見つかりませんでした。")
            return 0  # 該当する商品がない場合は0を返す
        return item.price

# ------------------------メニューカテゴリー------------------------
class Menu_category(db.Model):
    __tablename__ = 'menu_category'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(255))

    def __repr__(self):
        return f'<Menu_category {self.category}>'


# ------------------------在庫設定------------------------

class Stock(db.Model):
    __tablename__ = 'stock'
    id = db.Column(db.Integer, db.ForeignKey('menu.id'), primary_key=True)
    today_stock_limit = db.Column(db.Integer)
    today_stock = db.Column(db.Integer)


    menu_item = db.relationship('Menu', foreign_keys=[id])





# ------------------------お知らせ------------------------
class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    post_date = db.Column(db.DateTime, default = datetime.datetime.now().date())
    post_time = db.Column(db.DateTime, default = datetime.datetime.now().time())
    poster = db.Column(db.String(128), nullable=False)


#----------------------予約された商品----------------------
class Reserved(db.Model):
    # 現在の日時を取得する関数
    @staticmethod
    def current_date():
        return datetime.datetime.now().date()

    @staticmethod
    def current_time():
        """
        現在の時刻を取得し、ミリ秒を1/10秒単位に丸める
        """
        now = datetime.datetime.now()
        microseconds = now.microsecond // 100000  # ミリ秒を1/10秒単位に丸める
        rounded_time = now.replace(microsecond=microseconds * 100000)
        return rounded_time.time()
    def price_sum(pid0:int, pid1:int, pid2:int, pid3:int, pid4:int) ->int:
        """

        予約した商品の合計を求める関数です

        price_sum(商品ID1, 商品ID2, 商品ID3, 商品ID4, 商品ID5)
            return 商品価格の合計

        """
        # Menu.price_sum(...)で使えます
        t_price = 0 
        t_price = int(Menu.item_price(pid0))

        # 各商品IDが None でない場合に価格を加算する
        if pid1 is not None:
            t_price += int(Menu.item_price(pid1))
        if pid2 is not None:
            t_price += int(Menu.item_price(pid2))
        if pid3 is not None:
            t_price += int(Menu.item_price(pid3))
        if pid4 is not None:
            t_price += int(Menu.item_price(pid4))

        return t_price


    __tablename__ = 'reserved'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id_0 = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=False)
    product_id_1 = db.Column(db.Integer, db.ForeignKey('menu.id'), default=None)
    product_id_2 = db.Column(db.Integer, db.ForeignKey('menu.id'), default=None)
    product_id_3 = db.Column(db.Integer, db.ForeignKey('menu.id'), default=None)
    product_id_4 = db.Column(db.Integer, db.ForeignKey('menu.id'), default=None)
    reserve_day = db.Column(db.Date, default=current_date)
    reserve_time = db.Column(db.Time, default=current_time)
    price = db.Column(db.Integer)
    state = db.Column(db.String(255))

    # リレーションシップを定義
    user = db.relationship('User', backref='reservations')
    menu_item_0 = db.relationship('Menu', foreign_keys=[product_id_0])
    menu_item_1 = db.relationship('Menu', foreign_keys=[product_id_1])
    menu_item_2 = db.relationship('Menu', foreign_keys=[product_id_2])
    menu_item_3 = db.relationship('Menu', foreign_keys=[product_id_3])
    menu_item_4 = db.relationship('Menu', foreign_keys=[product_id_4])

class Contact(db.Model):
    def current_date():
        return datetime.datetime.now().date()

    def current_time():
        return datetime.datetime.now().time()

    __tablename__ = 'contact'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    contact_day = db.Column(db.Date, default=datetime.datetime.now().date)
    contact_time = db.Column(db.Time, default=datetime.datetime.now().time)

    user = db.relationship('User', backref='contact')


class Sale_state(db.Model):
    __tablename__ = 'sale_state'
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.Boolean)
    state_name = db.Column(db.String(255))


class Agreement(db.Model):
    __tablename__ = 'agree_rule'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True, nullable=False) # 主キーをユーザーIDにして ID, agreeeeeeeedだけにしてもいいかも
    agreed = db.Column(db.Boolean, nullable=False)