from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, TextAreaField, DateField, TimeField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import DataRequired, Length, Email, EqualTo

class LoginForm(FlaskForm):
    email = StringField('メールアドレス', validators=[DataRequired(), Email()],render_kw={"placeholder": "メールアドレスを入力"})
    password = PasswordField('パスワード', validators=[DataRequired(), Length(min=8)],render_kw={"placeholder": "パスワードを入力"})
    submit = SubmitField('ログイン')


class RegisterForm(FlaskForm):
    lastname = StringField('',validators=[DataRequired()],render_kw={"placeholder": "姓"})
    firstname = StringField('', validators=[DataRequired()],render_kw={"placeholder": "名"})
    grade = IntegerField("", validators=[DataRequired()],render_kw={"placeholder": "学年"})
    cls = IntegerField("", validators=[DataRequired()],render_kw={"placeholder": "組"})
    num = IntegerField("", validators=[DataRequired()],render_kw={"placeholder": "番号"})
    email = StringField('', validators=[DataRequired(), Email()],render_kw={"placeholder": "メールアドレス"})
    password = PasswordField('', validators=[DataRequired(), Length(min=8, max=50)],render_kw={"placeholder": "真新しいパスワード"})
    confirm = PasswordField('', validators=[DataRequired(), Length(min=8, max=50), EqualTo('password')],render_kw={"placeholder": "パスワードの確認"})
    confirm_code = PasswordField("", validators=[DataRequired()], render_kw={"placeholder": "確認コード"})
    submit = SubmitField('アカウントの作成')

    
class ReserveForm(FlaskForm):
    product_id_0 = IntegerField("予約した商品１つ目")
    product_id_1 = IntegerField("予約した商品２つ目")
    product_id_2 = IntegerField("予約した商品３つ目")
    product_id_3 = IntegerField("予約した商品４つ目")
    product_id_4 = IntegerField("予約した商品５つ目")
    submit = SubmitField('予約送信')


class MenueditForm(FlaskForm):
    product_name = StringField("商品名")
    product_price = IntegerField("価格")
    explanation = StringField("商品説明")
    stock = IntegerField("在庫")
    buy_cnt = IntegerField("購入回数")
    product_image = FileField('画像を選択してください', validators=[
        FileAllowed(['jpg', 'png'], '画像形式はjpgまたはpngのみです')
    ])
    category = IntegerField("カテゴリー")
    submit = SubmitField('更新')

class MenucreateForm(FlaskForm):
    product_name = StringField("商品名")
    product_price = IntegerField("価格")
    explanation = StringField("商品説明")
    product_image = FileField('画像を選択してください', validators=[
        FileAllowed(['jpg', 'png'], '画像形式はjpgまたはpngのみです')
    ])
    category = IntegerField("カテゴリー")
    submit = SubmitField('追加')


class MenudeleteForm(FlaskForm):
    delete_submit = SubmitField("メニュー削除")


class ContactForm(FlaskForm):
    title = StringField("タイトル")
    content = TextAreaField("内容")
    submit = SubmitField("送信")


