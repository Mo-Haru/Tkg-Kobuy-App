from kobuy_app import app, db, admin_required, login_required, rule_required
from flask import render_template,  request, redirect, send_from_directory, url_for, flash, Blueprint, abort, session
from kobuy_app.models.models import Agreement, Menu, User, Notification, Reserved, Contact, Stock, Sale_state, Menu_category
from kobuy_app.forms import LoginForm, RegisterForm, ReserveForm, MenueditForm, MenudeleteForm, MenucreateForm, ContactForm
from flask_login import login_user, logout_user, current_user
from datetime import datetime
from werkzeug.utils import secure_filename
import os

main = Blueprint('main', __name__)

# ユーザー情報とwebtitleの関数
def current_webdata(webtitle: str) -> dict:
    """
    ログインしているユーザー情報とページのタイトルを辞書形式で返す関数。
    """
    if current_user.is_authenticated:
        
        data = {
            "webtitle": webtitle,
            "current_user_id": current_user.id,
            "current_user_email": current_user.email,
            "current_user_lastname": current_user.lastname,
            "current_user_firstname": current_user.firstname,
            "current_user_grade": current_user.grade,
            "current_user_cls": current_user.cls,
            "current_user_num": current_user.num,
            "role": str(current_user.roles)
        }
    else:
        data = {
            "webtitle": webtitle,
            "current_user_id": None,
            "current_user_email": None,
            "current_user_lastname": "",
            "current_user_firstname": "ゲスト",
            "current_user_grade": None,
            "current_user_cls": None,
            "current_user_num": None,
            "role": None
        }
    return data

def file_upload(img) -> str:
    """
    画像のファイルオブジェクトを受け取り、アップロードしてファイルパスを返す関数。
    <form method="POST" 「enctype="multipart/form-data"」<-これ大事>
    """
    if img is None:
        print("画像がアップロードされていません")
        return None  # 画像がアップロードされていない場合
    
    filename = secure_filename(img.data.filename)
    if filename is not None:
        filepath = f"kobuy_app/static/uploads/{filename}"
        img.data.save(filepath)  # 直接ファイルオブジェクトを保存
        return f"uploads/{filename}"
    return "error"

def reserve_items(request):
    if Sale_state.query.filter_by(id=0).first().state == True:
        item_slot = []
        reserve_item_cnt = 0
        try:
            for i in range(5):
                reserve_item = request.form.get(f"reserve_item_{i}")
                if reserve_item is not None:
                    if not reserve_item is None:
                        continue
                    if not reserve_item.isdigit():
                        flash("不正な商品IDがありました。予約を確認してください。問題があれば、キャンセルご再度予約をしてください。", "error")
                    if Stock.query.filter_by(id=int(reserve_item)).first().today_stock > 0:
                        item_slot.append(int(reserve_item))
                        reserve_item_cnt += 1
                    else:
                        flash(f"商品:{Menu.query.filter_by(id=int(reserve_item)).first().productname}は在庫がないため予約できませんでした。", "error")
                if reserve_item_cnt == 0:
                    flash("商品が選択されていないか在庫がないため、予約することができませんでした。", "error")
                    return redirect(url_for("reserve"))

        except Exception as e:
            flash("エラーが発生しました。予約はされていません。", "error")
            flash(f"{e}", "error")
            return redirect(url_for("reserve"))

        try:
            for i in item_slot:
                Menu.query.filter_by(id=i).first().buy_cnt += 1
                db.session.commit()
            while len(item_slot) < 5:
                item_slot.append(None)
        except:
            flash("エラーが発生しました。予約はされていません。", "error")
            db.session.rollback()
            return redirect(url_for("reserve"))

        try:
            for i in item_slot:
                if i is not None:
                    if Stock.query.filter_by(id=i).first().today_stock > 0:
                        Stock.query.filter_by(id=i).first().today_stock -= 1
                        db.session.commit()
                    else:
                        flash(f"{Menu.quary.filter_by(id=i).first().productname}は在庫がないため予約できませんでした", "error")
        except:
            flash("エラーが発生しました。予約はされていません。", "error")
            db.session.rollback()
            return redirect(url_for("reserve"))
        
        try:
            reserve = Reserved(
                user_id=current_user.id,
                product_id_0=item_slot[0],
                product_id_1=item_slot[1],
                product_id_2=item_slot[2],
                product_id_3=item_slot[3],
                product_id_4=item_slot[4],
                reserve_day=Reserved.current_date(),
                reserve_time=Reserved.current_time(),
                price=Reserved.price_sum(item_slot[0], item_slot[1], item_slot[2], item_slot[3], item_slot[4]),
                state="予約済み"
            )
            db.session.add(reserve)
            db.session.commit()
            flash("予約が完了しました", "success")
            return redirect(url_for("reserve_done"))
        
        except Exception as e:
            flash("エラーが発生しました", "error")
            flash(f"{e}", "error")
            db.session.rollback()
            return redirect(url_for("reserve"))
                
    flash("現在予約可能時間でないため予約することができません", "error")
    return redirect(url_for("reserve"))



@app.route('/')
def index():
    data = current_webdata("トップページ")
    menu_rank = Menu.query.order_by(Menu.buy_cnt.desc()).limit(2)
    f_items = {
        "f_item_1" : menu_rank[0],
        "f_item_2" : menu_rank[1],
        "f_item_3" : menu_rank[2]
    }
    menu = Menu.query.all()
    if current_user.is_authenticated:
        reserve_items = Reserved.query.order_by(Reserved.id.desc()).filter_by(user_id=current_user.id).first()
        if reserve_items is not None:
            if reserve_items.state == "キャンセル(購買側都合)":
                flash("購買側の都合でキャンセルされました", "error")
    else:
        reserve_items = None
    return render_template('main/index.html', data = data, f_items = f_items, reserve_items = reserve_items, menus = menu)



@app.route("/login", methods=['GET', 'POST'])
def login():
    data = current_webdata("ログイン")  # ページデータの取得
    form = LoginForm()  # ログインフォームの初期化
    if form.validate_on_submit():  # フォームの送信後にバデーションをチェック
        user = User.query.filter_by(email=form.email.data).first()  # ユーザー情報の取得
        if user and user.check_password(form.password.data):  # ユーザー確認とパスワード検証
            login_user(user)  # ユーザーをログイン状態にする
            flash("ログイン完了", "success")  # ログイン成功メッセージ
            next_page = request.args.get('next') or session.pop('next_url', None)  # リダイレクト先を取得
            if not next_page or not next_page.startswith('/'):  # 安全なリダイレクト先を確認
                next_page = url_for('index')  # デフォルトリダイレクト先
            return redirect(next_page)
        
        else:
            flash("ログインに失敗しました。情報を確認して再度お試しください。", "error")  # エラーメッセージ
    
    return render_template('main/login.html', form=form, data=data)  # ログインページを表示



@app.route("/register", methods=["GET", "POST"])
def register():
    data = current_webdata("ユーザー登録")
    form = RegisterForm()
    con_code = "12345678"
    if request.method == 'POST' and form.validate():
        print(form.confirm_code.data)
        if form.confirm_code.data == con_code:
            if form.password.data is None or form.confirm.data is None:
                flash('パスワードを入力してください', "error")
                return redirect(url_for('register'))
            
            if form.password.data != form.confirm.data:
                flash('パスワードが一致しません', "error")
                return redirect(url_for('register'))
            
            if form.lastname.data is None or form.firstname.data is None:
                flash('名前を入力してください', "error")
                return redirect(url_for('register'))

            if form.email.data is None:
                flash('メールアドレスを入力してください', "error")
                return redirect(url_for('register'))
            
            if User.query.filter_by(email=form.email.data).first():
                flash('このメールアドレスでは登録できません。', 'error')
                return redirect(url_for('register'))
            
            allowed_domains = ["fukui-ed.jp"]
            if not any(form.email.data.endswith(domain) for domain in allowed_domains):
                flash('指定されたメールアドレスを使用してください。', "error")
                return redirect(url_for('register'))
            
            if form.grade.data > 4 or form.grade.data < 1 or form.grade.data is None:
                flash('学年が不正です。', "error")
                return redirect(url_for('register'))
            
            if form.cls.data > 4 or form.cls.data < 1 or form.cls.data is None:
                flash('組が不正です。', "error")
                return redirect(url_for('register'))
            
            if form.num.data > 40 or form.num.data < 1 or form.num.data is None:
                flash('出席番号が不正です。', "error")
                return redirect(url_for('register'))

            else:
                try:
                    user = User(
                        lastname=form.lastname.data,
                        firstname=form.firstname.data,
                        grade=form.grade.data,
                        cls=form.cls.data,
                        num=form.num.data,
                        email=form.email.data
                    )
                    user.set_password(form.password.data)
                    db.session.add(user)
                    db.session.commit()
                    agree = Agreement(
                        user_id=user.id,
                        agreed=False
                    )
                    db.session.add(agree)
                    db.session.commit()
                    if form.grade.data == 4 and form.cls.data == 1 and form.num.data == 1:
                        flash(f'{form.lastname.data}{form.firstname.data}先生ご登録ありがとうございます。', "success")
                        return redirect(url_for('login'))
                    flash(f'{form.lastname.data}{form.firstname.data}さん登録ありがとうございます。', "success")
                    return redirect(url_for('login'))
                except Exception as e:
                    flash(f"エラーが発生しました: {e}", "error")
                    flash("何度も発生する場合、管理者に連絡してください。", "error")
                    return redirect(url_for('register'))
            
        else:
            print("確認コード不一致")
            flash('確認コードが一致しません', "error")
            return redirect(url_for('register'))
        
    return render_template('main/register.html', form=form, data = data)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))



@app.route("/rule", methods=["POST", "GET"])
@login_required
def rule():
    if request.method == "GET":
        data = current_webdata("ルール確認")
        agt = Agreement.query.filter_by(user_id=current_user.id).first()
        if agt is None:
            # ユーザーの同意記録がない場合に新規作成する
            agree = Agreement(
                user_id=current_user.id,
                agreed=False
            )
            db.session.add(agree)
            db.session.commit()
            agt = agree  # 作成したオブジェクトを再利用
        if not agt.agreed:
            flash("同意してないと使えないよ")
            return render_template("main/rule.html", data=data)
        
        else:
            flash("すでに同意しています")
            return render_template("main/rule.html", data=data)

    if request.method == "POST":
        if current_user.is_authenticated:
            try:
                agt = Agreement.query.filter_by(user_id=current_user.id).first()
                if agt:
                    agt.agreed = True
                else:
                    agt = Agreement(user_id=current_user.id, agreed=True)
                    db.session.add(agt)
                db.session.commit()
                flash("同意が記録されました", "success")
                return redirect(url_for("index"))
            
            except Exception as e:
                flash(f"エラーが発生しました: {e}", "error")
                return redirect(url_for("rule"))



@app.route("/menu")
def menu():
    data = current_webdata("メニュー")
    menu_items = Menu.query.order_by(Menu.orders).all()
    return render_template("main/menu.html", data=data, menu_items=menu_items)



@app.route("/menu/<int:menu_id>", methods = ["GET", "POST"])
def menu_detail(menu_id):
    if request.method == "GET":
        data = current_webdata("メニュー詳細")
        menu_item = Menu.query.get(menu_id)
        if menu_item is None:
            flash(f"menuID:{ menu_id }のメニューが存在しません", "error")
            return redirect(url_for("menu"))
        
        return render_template("main/menu_detail.html", menu_item=menu_item, data=data)
    
    if request.method == "POST":
        try:
            if  Sale_state.query.filter_by(id=0).first().state == True:    
                stock_item = Stock.query.filter_by(id=menu_id).first()
                item = Menu.query.filter_by(id=menu_id).first()
                if stock_item.today_stock > 0:
                    stock_item.today_stock -= 1
                    item.buy_cnt += 1
                    db.session.commit()
                    reserve = Reserved(
                    user_id=current_user.id,
                    product_id_0=menu_id,
                    product_id_1=None,
                    product_id_2=None,
                    product_id_3=None,
                    product_id_4=None,
                    reserve_day=Reserved.current_date(),
                    reserve_time=Reserved.current_time(),
                    price=Reserved.price_sum(menu_id, None, None, None, None),
                    state="予約済み"
                    )
                    db.session.add(reserve)
                else:
                    flash("在庫がないため予約できませんでした", "error")
                    return redirect(url_for("reserve"))
                
                db.session.commit()
                flash("予約が完了しました", "success")
                return redirect(url_for("reserve_done"))
                
            else:
                flash("現在予約可能時間でないため予約することができません", "error")
                return redirect(url_for("reserve"))
            
        except Exception as e:
            flash("エラー：エラーが発生しました。")
            flash(f"{e}", "error")
            db.session.rollback()
            return redirect(url_for("reserve"))



@app.route("/contact", methods = ["GET", "POST"])
@login_required
def contact():
    if request.method == "GET":
        data = current_webdata("お問い合わせ")
        return render_template("main/contact.html", data = data)
    
    if request.method == "POST":
        title = request.form.get("title")
        print(title)
        content = request.form.get("content")
        print(content)
        contact = Contact(
            user_id=current_user.id,
            title = title,
            content = content,
            contact_day=Contact.current_date(),
            contact_time=Contact.current_time(),
        )
        db.session.add(contact)
        db.session.commit()
        flash("お問い合わせが完了しました", "success")
        return redirect(url_for("index"))



@app.route("/reserve", methods = ["GET", "POST"])
@login_required
@rule_required
def reserve():
    data = current_webdata("予約ページ")
    menu_items = Menu.query.order_by(Menu.orders).all()
    menu_stock = Stock.query.all()
    menu_category = Menu_category.query.all()
    sale_state = Sale_state.query.filter_by(id=0).first()
    form = ReserveForm()
    if request.method == "GET":
        return render_template("main/reserve.html", data=data, menu_items=menu_items, menu_stock=menu_stock,form=form, sale_state = sale_state, menu_categories = menu_category)

    if request.method == "POST":
        # print(request.form)
        # return reserve_items(request)
        try:
            if sale_state.state == True:
                reserve_item_0 = request.form.get("reserve_item_0")
                print(reserve_item_0)
                if not reserve_item_0 or reserve_item_0 == "None":
                    flash("商品を選択してください", "error")
                    return redirect(url_for("reserve"))
                
                item_slot = []
                for i in range(5):
                    reserve_item_id = request.form.get(f"reserve_item_{i}")
                    if not reserve_item_id:  # 商品が選択されていない場合
                        if i == 0:
                            flash("商品を選択してください", "error")
                            return redirect(url_for("reserve"))  

                        flash(f"商品 {i + 1} が選択されていません。", "error")
                        item_slot.append(None)
                        print(f"{item_slot.i}")
                    else:
                        menu_item = Menu.query.filter_by(id=reserve_item_id).first()
                        menu_stock = Stock.query.filter_by(id=reserve_item_id).first()
                        if menu_item:
                            if menu_stock.today_stock > 0:
                                menu_stock.today_stock -= 1
                                db.session.commit()
                                item_slot.append(reserve_item_id)
                            else:
                                if i == 0:
                                    flash("1番目の商品の在庫がないため予約できませんでした。予約はされていません。", "error")
                                    return redirect(url_for("reserve"))
                                
                                flash(f"{i+1}個目の{menu_item.productname}は在庫がないため予約できませんでした。在庫がない商品以外は予約されました。キャンセルする場合は予約履歴からキャンセルしてください。", "error")
                                item_slot.append(None)
                        else:
                            item_slot.append(None)  # 該当する商品がない場合も None を追加
                # ここで item_slot のサイズは必ず5になっていることを保証
                while len(item_slot) < 5:
                    item_slot.append(None)  # 保険として足りない場合は None で埋める
                for i in item_slot:
                    if i is not None:
                        Menu.query.filter_by(id=i).first().buy_cnt += 1
                db.session.commit()
                reserve = Reserved(
                    user_id=current_user.id,
                    product_id_0=item_slot[0],
                    product_id_1=item_slot[1],
                    product_id_2=item_slot[2],
                    product_id_3=item_slot[3],
                    product_id_4=item_slot[4],
                    reserve_day=Reserved.current_date(),
                    reserve_time=Reserved.current_time(),
                    price=Reserved.price_sum(item_slot[0], item_slot[1], item_slot[2], item_slot[3], item_slot[4]),
                    state="予約済み"
                )
                db.session.add(reserve)
                db.session.commit()
                flash("予約が完了しました", "success")
                return redirect(url_for("reserve_done"))
            
            flash("現在予約することができません", "error")
            return redirect(url_for("reserve"))
        
        except Exception as e:
            flash("エラーが発生しました", "error")
            flash(f"{e}", "error")
            print(e)
            return redirect(url_for("reserve"))


# @app.route("/reserve/filter/<int:category_id>", methods = ["GET", "POST"])
# @login_required
# def reserve_filter(category_id):
#     data = current_webdata("商品の絞り込み")
#     menu_items = Menu.query.filter_by(category_id=category_id).all()
#     menu_stock = Stock.query.all()
#     menu_category = Menu_category.query.all()
#     sale_state = Sale_state.query.filter_by(id=0).first()
#     form = ReserveForm()
#     if request.method == "GET":
#         return render_template("main/reserve.html", data=data, menu_items=menu_items, menu_stock=menu_stock,form=form, sale_state = sale_state, menu_categories = menu_category)

#     if request.method == "POST":
#         return reserve_items(request)


@app.route("/reserve/item/<int:item_id>", methods = ["GET", "POST"])
@login_required
def reserve_item(item_id):
    if request.method == "GET":
        data = current_webdata("商品の予約")
        item = Menu.query.filter_by(id=item_id).first()
        return render_template("main/reserve_item.html", data = data, item = item)
    
    if request.method == "POST":
        try:
            if Sale_state.query.filter_by(id=0).first().state == True:    
                stock_item = Stock.query.filter_by(id=item_id).first()
                item = Menu.query.filter_by(id=item_id).first()
                if stock_item.today_stock > 0:
                    stock_item.today_stock -= 1
                    print(item.buy_cnt)
                    item.buy_cnt += 1
                    print(item.buy_cnt)
                    db.session.commit()
                    reserve = Reserved(
                    user_id=current_user.id,
                    product_id_0=item_id,
                    product_id_1=None,
                    product_id_2=None,
                    product_id_3=None,
                    product_id_4=None,
                    reserve_day=Reserved.current_date(),
                    reserve_time=Reserved.current_time(),
                    price=Reserved.price_sum(item_id, None, None, None, None),
                    state="予約済み"
                    )
                    db.session.add(reserve)
                else:
                    flash("在庫がないため予約できませんでした", "error")
                    return redirect(url_for("reserve"))
                
                db.session.commit()
                flash("予約が完了しました", "success")
                return redirect(url_for("reserve_done"))
                
            else:
                flash("現在予約可能時間でないため予約することができません", "error")
                return redirect(url_for("reserve"))
            
        except Exception as e:
            flash("エラー：エラーが発生しました。")
            flash(f"{e}", "error")
            db.session.rollback()
            return redirect(url_for("reserve"))



@app.route("/reserve_done")
@login_required
def reserve_done():
    data = current_webdata("予約完了")
    return render_template("main/reserve_done.html", data = data, r_data = Reserved.query.filter_by(user_id=current_user.id).order_by(Reserved.id.desc()).first())


# 予約キャンセル
@app.route("/cancel_reserve/<int:reserve_id>", methods = ["GET", "POST"])
@login_required
def reserve_cancel(reserve_id):
    if request.method == "GET":
        data = current_webdata("予約のキャンセル")
        return render_template("main/cancel.html", data = data)

    if request.method == "POST":
        if current_user.id == Reserved.query.filter_by(id=reserve_id).first().user_id:
            reserve = Reserved.query.filter_by(id=reserve_id).first()
            if reserve is None:
                flash("予約が存在しません", "error")
                return redirect(url_for("my_reserve_lis"))
            
            if reserve.state == "キャンセル":
                flash("すでにキャンセルされています", "error")
                return redirect(url_for("my_reserve_lis"))
            
            if reserve.state == "受取済み":
                flash("すでに受取済みです", "error")
                return redirect(url_for("my_reserve_lis"))
            
            if reserve.state == "確認済み" or reserve.state == "予約済み" or reserve.state == "準備完了":
                reserve.state = "キャンセル"
                flash("注文の取り消しが完了しました。以後キャンセルしないようにしてください。", "success")
                db.session.commit()
                return redirect(url_for("my_reserve_lis"))

            flash("エラーが発生しました。注文の取り消しはされていません","error")
            return redirect(url_for("my_reserve_lis"))
        
        flash("ご注文された本人のアカウントでキャンセルしてください", "error")
        return redirect(url_for("my_reserve_lis"))


# ユーザー情報表示＆編集
@app.route("/profile")
@login_required
def profile():
    data = current_webdata("ユーザー情報")
    return render_template("main/profile.html", data=data)



@app.route("/my_reserved_list")
@login_required
def my_reserve_lis():
    data = current_webdata("予約済み商品")
    reserved = Reserved.query.order_by(Reserved.id.desc()).filter_by(user_id = current_user.id).all()
    return render_template("main/reserved_list.html", data = data, reserved = reserved)



@app.route("/my_reserved_list/detail/<int:reserve_id>")
@login_required
def my_reserve_list_detail(reserve_id):
    data = current_webdata("予約済み商品詳細")
    reserved = Reserved.query.filter_by(id = reserve_id).first()
    menus = Menu.query.all()
    if reserved is None:
        flash("エラー: このIDの予約は存在しません", "error")
        return redirect(url_for("my_reserve_lis"))

    if reserved.user_id == current_user.id:
        data = current_webdata("予約済み商品詳細")
        return render_template("main/reserved_detail.html", data = data, reserved = reserved, menus = menus)

    else:
        flash("エラー: このIDの予約は存在しません", "error")
        return redirect(url_for("my_reserve_lis"))



@app.route("/help")
def help():
    data = current_webdata("ヘルプ")
    return render_template("main/help.html", data = data)



# -----------------------管理側-----------------------
@app.route("/admin")
@login_required
@admin_required
def adminmain():
    data = current_webdata("管理トップページ")
    return render_template("admin/adminmain.html", data = data)


# 予約者リスト
@app.route("/admin/reserve_list")
@login_required
@admin_required
def reserve_list():
    data = current_webdata("予約者リスト")
    allday = True
    reserve = Reserved.query.order_by(Reserved.id.desc()).all()
    return render_template("admin/reserve_list.html", reserve=reserve, allday=allday, data = data)



@app.route("/admin/reserve/detail/<int:reserve_id>")
@login_required
@admin_required
def reserve_detail(reserve_id):
    data = current_webdata("予約詳細")
    reserve = Reserved.query.filter_by(id=reserve_id).first()
    reserve_user = User.query.filter_by(id=reserve.user_id).first()
    return render_template("admin/reserve_detail.html", reserve=reserve, data = data, reserve_user=reserve_user)



@app.route("/admin/menu/<int:menu_id>/reserve")
@login_required
@admin_required
def reserve_detail_menu(menu_id):
    data=current_webdata("本日の商品ごとの予約者リスト")
    reserve = Reserved.query.filter_by(reserve_day=Reserved.current_date).all()
    # 途中 =====================================================================================================================================================================


@app.route("/admin/reserve_list/today")
@login_required
@admin_required
def reserve_list_a():
    data = current_webdata("今日の予約者リスト")
    allday = False
    today = datetime.now().date()
    reservelis = Reserved.query.order_by(Reserved.id.desc()).filter_by(reserve_day = today).all()
    return render_template("admin/reserve_list.html", reserve=reservelis, allday=allday, data = data)



@app.route("/admin/reserve/state_rdy/<int:reserve_id>" , methods = ["POST", "GET"])
@login_required
@admin_required
def reserve_s_rdy(reserve_id):
    reserve_edit = Reserved.query.filter_by(id=reserve_id).first()
    reserve_edit.state = "準備完了"
    db.session.commit()
    flash(f"{reserve_id}は準備完了に変更されました", "success")
    return redirect(url_for("reserve_list"))



@app.route("/admin/reserve/state_rcp/<int:reserve_id>" , methods = ["POST", "GET"])
@login_required
@admin_required
def reserve_s_rcp(reserve_id):
    reserve_edit = Reserved.query.filter_by(id=reserve_id).first()
    reserve_edit.state = "受取済み"
    db.session.commit()
    flash(f"{reserve_id}は受取済みに変更されました", "success")
    return redirect(url_for("reserve_list"))



@app.route("/admin/reserve/state_cancel/<int:reserve_id>")
@login_required
@admin_required
def reserve_s_cancel(reserve_id):
    reserve = Reserved.query.filter_by(id=reserve_id).first()
    reserve.state = "キャンセル(購買側都合)"
    db.session.commit()
    flash("購買側都合でキャンセルされました", "success")
    return redirect(url_for("reserve_list"))


# メニュー編集リスト
@app.route("/admin/menu/edit")
@login_required
@admin_required
def menu_edit():
    data = current_webdata("メニュー編集")
    menu=Menu.query.order_by(Menu.orders).all()
    stock = Stock.query.all()
    menu_categorys = Menu_category.query.all()
    return render_template("admin/menu_main_edit.html", menu=menu, data = data, stock=stock, menu_categorys = menu_categorys)


@app.route("/admin/menu/up/<int:menu_id>")
@login_required
@admin_required
def menu_up(menu_id):
    up_menu = Menu.query.filter_by(id=menu_id).first()
    if up_menu is None:
        flash(f"menuID:{ menu_id }のメニューが存在しません", "error")
        return redirect(url_for("menu_edit"))

    if up_menu.orders <= 1:
        flash("この商品はすでに一番上にあるため移動できません", "error")
        return redirect(url_for("menu_edit"))
    
    down_menu = Menu.query.filter_by(orders=up_menu.orders - 1).first()
    if down_menu is None:
        flash(f"order:{ up_menu.orders - 1 }のメニューが存在しません", "error")
        return redirect(url_for("menu_edit"))

    # メニューの順序を入れ替える
    up_menu.orders, down_menu.orders = down_menu.orders, up_menu.orders
    db.session.commit()
    flash(f"menuID:{ menu_id }のメニューを一つ上に移動しました", "success")
    return redirect(url_for("menu_edit"))


@app.route("/admin/menu/down/<int:menu_id>")
@login_required
@admin_required
def menu_down(menu_id):
    down_menu = Menu.query.filter_by(id=menu_id).first()
    if down_menu is None:
        flash(f"menuID:{ menu_id }のメニューが存在しません", "error")
        return redirect(url_for("menu_edit"))
    
    if down_menu.orders >= Menu.query.count():
        flash("この商品はすでに一番下にあるため移動できません", "error")
        return redirect(url_for("menu_edit"))

    up_menu = Menu.query.filter_by(orders=down_menu.orders + 1).first()
    if up_menu is None:
        flash(f"order:{ down_menu.orders + 1 }のメニューが存在しません", "error")
        return redirect(url_for("menu_edit"))
    
    # メニューの順序を入れ替える
    down_menu.orders, up_menu.orders = up_menu.orders, down_menu.orders
    db.session.commit()
    flash(f"menuID:{ menu_id }のメニューを一つ下に移動しました", "success")
    return redirect(url_for("menu_edit"))



# メニュー編集リスト->一つの商品の詳細なページ
@app.route("/admin/menu/<int:menuid>")
@login_required
@admin_required
def menu_edit_detail(menuid:int):
    menu = Menu.query.filter_by(id=menuid).first()
    if menu is None:
        flash(f"menuID:{ menuid }のメニューが存在しません", "error")
        return redirect(url_for("menu_edit"))

    data = current_webdata(f"{menu.productname}の詳細")
    category = Menu_category.query.filter_by(id=menu.category_id).first()
    stock = Stock.query.filter_by(id=menuid).first()    
    return render_template("admin/menu_detail.html", menu=menu, data=data, category=category, stock=stock)



@app.route("/admin/menu/stock_update/<int:menuid>", methods=["POST"])
@login_required
@admin_required
def menu_stock_update(menuid:int):
    if request.method == "POST":
        if request.form.get("stock_post").isdigit() == True:
            Stock.query.filter_by(id=menuid).first().today_stock_limit = int(request.form.get("stock_post"))
            db.session.commit()
            flash(f"{menuid}の在庫が更新されました", "success")
            return redirect(url_for("menu_edit"))

        flash("在庫は数字で入力してください", "error")
        return redirect(url_for("menu_edit"))



@app.route("/admin/menu/stock/first_setup", methods=["GET", "POST"])
@login_required
@admin_required
def menu_stock_f_setup():
    data = current_webdata("在庫設定")
    menu = Menu.query.all()
    stock = Stock.query.all()
    if request.method == "GET":
        return render_template("admin/stock_f_setup.html", menu=menu, stock=stock,data=data)

    if request.method == "POST":
        for menu in menu:
            try:
                if Stock.query.filter_by(id=menu.id).first() is None:
                    new_stock = Stock(
                        id=menu.id,
                        today_stock_limit=0,
                        today_stock=0
                    )
                    try:
                        db.session.add(new_stock)
                        db.commit()
                    except:
                        flash("DBに新規の在庫データ作成に失敗しました", "error")
                request_stock = int(request.form.get(f"stock_post_{menu.id}"))
                if request_stock is None:
                    stock_tmp = 0
                if request_stock > 0:
                    stock_tmp = 0

                stock_tmp = Stock(
                    id = int(menu.id),
                    today_stock_limit = int(request.form.get(f"stock_post_{menu.id}")),
                    today_stock = int(request.form.get(f"stock_post_{menu.id}"))
                )
                try:
                    db.session.merge(stock_tmp)
                    db.session.commit()
                except:
                    flash(f"ID:{menu.id}の在庫設定に失敗しました", "error")
            except:
                flash(f"ID:{menu.id}の在庫設定に失敗しました", "error")
        flash("在庫設定が完了しました", "success")
        return redirect(url_for("menu_edit"))



@app.route("/admin/menu/stock")
@login_required
@admin_required
def menu_stock():
    data = current_webdata("在庫")
    menu = Menu.query.all()
    stock = Stock.query.all()
    return render_template("admin/stock.html", menus=menu, stocks=stock, data=data)



@app.route("/admin/menu/stock/dec/<int:menuid>")
@login_required
@admin_required
def menu_stock_dec(menuid:int):
    try:
        stock = Stock.query.filter_by(id=menuid).first()
        if stock.today_stock > 0:
            if stock.today_stock_limit > 0:
                stock.today_stock -= 1
                stock.today_stock_limit -= 1
                db.session.commit()
                return redirect(url_for("menu_stock"))
            
        flash("在庫の数を０以下にできません", "error")
        return redirect(url_for("menu_stock"))

    except Exception as e:
        print(e)
        flash("エラーが発生しました", "error")
        return redirect(url_for("menu_stock"))



@app.route("/admin/menu/stock/inc/<int:menuid>")
@login_required
@admin_required
def menu_stock_inc(menuid:int):
    try:
        stock = Stock.query.filter_by(id=menuid).first()
        if stock.today_stock >= 0:
            if stock.today_stock_limit >= 0:
                stock.today_stock += 1
                stock.today_stock_limit += 1
                db.session.commit()
                return redirect(url_for("menu_stock"))
            
        else:
            stock.today_stock = 0
            stock.today_stock_limit = 0
            db.session.commit()
            flash("在庫の数が不正だったためリセットしました", "error")
        return redirect(url_for("menu_stock"))
    
    except:
        flash("エラーが発生しました" , "error")
        return redirect(url_for("menu_stock"))


# メニュー更新
@app.route("/admin/menu/edit/<int:menuid>", methods=["GET", "POST"])
@login_required
@admin_required
def menu_edit_edit(menuid: int):
    data = current_webdata("メニュー更新")
    form = MenueditForm()
    menu = Menu.query.filter_by(id=menuid).first()
    stock = Stock.query.filter_by(id=menuid).first()
    category = Menu_category.query.filter_by(id=menu.category_id).first()
    categorys = Menu_category.query.all()
    if request.method == "GET":
        menu_dic = {
            "productname": menu.productname,
            "price": menu.price,
            "explanation": menu.explanation,
            "product_image": menu.product_image,
            "stock": stock.today_stock_limit,
            "buy_cnt": menu.buy_cnt,
            "category_id": menu.category_id
        }
        return render_template("admin/menu_edit.html", menu=menu, data=data, menuid=menuid, form=form, menu_dic=menu_dic, category=category, categorys=categorys)
    
    elif form.validate_on_submit and request.method == "POST":
        if not form.product_image.data:
            img_tmp = menu.product_image
        else:
            img_tmp = file_upload(form.product_image.data)
            # ファイルが存在するかどうかを確認してから削除する
            if os.path.exists(f"kobuy_app/static/{menu.product_image}"):
                os.remove(f"kobuy_app/static/{menu.product_image}")
                print("正常に画像が削除されました")
            else:
                print(f"ファイルが存在しません: static/{menu.product_image}")
        edi_menu = Menu(
            id=menuid,
            productname=form.product_name.data,
            price=form.product_price.data,
            explanation=form.explanation.data,
            product_image=img_tmp,
            category_id=form.category.data
        )
        db.session.merge(edi_menu)
        db.session.commit()
        return redirect(url_for('menu_edit'))
    
    flash("エラーが発生しました", "error")
    return redirect(url_for('menu_edit'))


#メニュー削除
@app.route("/admin/menu/delete/<int:menuid>" , methods =["GET", "POST"])
@login_required
@admin_required
def menu_delete(menuid:int):
    data = current_webdata("メニュー削除")
    form = MenudeleteForm()
    menu=Menu.query.filter_by(id=menuid).first()
    if request.method == "GET":
        menu_dic = {
        "id" : menu.id,
        "product_name" : menu.productname,
        "product_price" : menu.price,
        "explanation" : menu.explanation,
        "product_image" : menu.product_image
        }
        return render_template("admin/menu_delete.html", menu=menu, data = data, menu_dic=menu_dic, form=form)
    
    elif form.validate_on_submit and "POST":
        try:
            delete_menu = Menu.query.filter_by(id=menuid).first()
            delete_stock = Stock.query.filter_by(id=menuid).first()
            db.session.delete(delete_menu)
            db.session.delete(delete_stock)
            db.session.commit()
            flash(f"正常に{menu.productname}は削除されました", "success")
            return redirect("/admin/menu/edit")
        
        except:
            flash("エラーが発生しました", "error")
            return redirect("/admin/menu/edit")
        
    return "error"


# メニュー追加
@app.route("/admin/menu/new", methods=["GET", "POST"])
@login_required
@admin_required
def menu_new():
    data = current_webdata("メニュー追加")
    form = MenucreateForm()
    if request.method == "GET":
        return render_template("admin/menu_new.html", data = data, form=form)
    elif form.validate_on_submit:
        print(form.product_image.data)
        if form.product_image.data:
            tmp_image = file_upload(form.product_image)
        else:
            tmp_image = None
        new_menu = Menu(
            productname = form.product_name.data,
            price = form.product_price.data,
            explanation = form.explanation.data,
            buy_cnt = 0,
            product_image = tmp_image
        )
        print(new_menu)
        db.session.add(new_menu)
        db.session.commit()
        new_stock = Stock(
            id = new_menu.id,
            today_stock_limit = 0,
            today_stock = 0
        )
        db.session.add(new_stock)
        db.session.commit()
        flash(f"正常に{form.product_name.data}を追加しました", "success")
        return redirect("/admin/menu/edit")
    
    return "error"


# メニュー画像表示
@app.route("/admin/menu/img/<int:menu_id>")
@login_required
@admin_required
def menu_img(menu_id):
    menu = Menu.query.filter_by(id=menu_id).first()
    if menu.product_image is None:
        flash(f"menuID:{ menu_id }の画像かメニューが存在しません", "error")
        return redirect(url_for("menu_edit"))
    
    data = current_webdata(f"{menu.productname}の画像")
    return send_from_directory("static", menu.product_image)



@app.route("/admin/reset_stock")
@login_required
@admin_required
def reset_stock():
    menu = Menu.query.all()
    for m in menu:
        m.stock = 0
    db.session.commit()
    stock = Stock.query.all()
    for s in stock:
        s.today_stock = 0
        s.today_stock_limit = 0
    db.session.commit()
    flash("在庫をリセットしました", "success")
    return redirect("/admin/menu/edit")



@app.route("/admin/option")
@login_required
@admin_required
def sale_option():
    data = current_webdata("販売オプション")
    sale_state = Sale_state.query.filter_by(id=0).first()
    return render_template("/admin/sale_option.html", data = data, sale_state = sale_state)



@app.route("/admin/start_sale")
@login_required
@admin_required
def start_sale():
    try:
        sale_state = Sale_state.query.filter_by(id = 0).first()
        sale_state.state = True
        sale_state.state_name = "販売中"
        db.session.commit()
        flash("販売を開始しました", "success")
        return redirect("/admin/option")
    
    except Exception as e:
        flash("エラーが発生しました", "error")
        print(e)
        db.session.rollback()
        return redirect("/admin/option")



@app.route("/admin/end_sale")
@login_required
@admin_required
def stop_sale():
    try:
        sale_state = Sale_state.query.filter_by(id = 0).first()
        sale_state.state = False
        sale_state.state_name = "販売停止中"
        db.session.commit()
        flash("販売を終了しました", "success")
        return redirect("/admin/option")
    
    except Exception as e:
        flash("エラーが発生しました", "error")
        print(e)
        db.session.rollback()
        return redirect("/admin/option")



@app.route("/admin/contact_list")
@login_required
@admin_required
def contact_view():
    data = current_webdata("お問い合わせ一覧")
    contacts = Contact.query.all()
    return render_template("admin/contact_list.html", data = data, contacts = contacts)



@app.route("/admin/contact_list/detail/<int:contact_id>")
@login_required
@admin_required
def contact_detail(contact_id):
    data = current_webdata("お問い合わせ詳細")
    contact = Contact.query.filter_by(id = contact_id).first()
    return render_template("admin/contact_list_detail.html", data = data, contact = contact)