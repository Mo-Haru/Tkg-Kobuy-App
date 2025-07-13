from kobuy_app import app, db, admin_required, login_required, rule_required
from flask import render_template,  request, redirect, send_from_directory, url_for, flash, Blueprint, abort, session, jsonify
from kobuy_app.models.models import Agreement, Menu, User, Notification, Reserved, Contact, Stock, Sale_state, Menu_category, PushSubscription, AppNotification
from kobuy_app.forms import LoginForm, RegisterForm, ReserveForm, MenueditForm, MenudeleteForm, MenucreateForm, ContactForm
from flask_login import login_user, logout_user, current_user
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import json
from pywebpush import webpush, WebPushException
import base64

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
        return ""  # 画像がアップロードされていない場合
    
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

# Ajax対応のエンドポイント
@app.route('/api/login', methods=['POST'])
def api_login():
    """Ajax用ログインエンドポイント"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'メールアドレスとパスワードを入力してください'
            }), 400
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return jsonify({
                'success': True,
                'message': 'ログインが完了しました',
                'redirect': url_for('index')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'メールアドレスまたはパスワードが正しくありません'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'エラーが発生しました'
        }), 500

@app.route('/api/register', methods=['POST'])
def api_register():
    """Ajax用アカウント作成エンドポイント"""
    try:
        data = request.get_json()
        con_code = "12345678"
        
        # バリデーション
        if data.get('confirm_code') != con_code:
            return jsonify({
                'success': False,
                'message': '確認コードが正しくありません'
            }), 400
        
        if data.get('password') != data.get('confirm'):
            return jsonify({
                'success': False,
                'message': 'パスワードが一致しません'
            }), 400
        
        # データの取得と変換
        lastname = data.get('lastname')
        firstname = data.get('firstname')
        grade = data.get('grade')
        cls = data.get('cls')
        num = data.get('num')
        email = data.get('email')
        
        # 必須フィールドのチェック
        if not all([lastname, firstname, grade, cls, num, email]):
            return jsonify({
                'success': False,
                'message': '必須項目が入力されていません'
            }), 400
        
        # ユーザー作成
        user = User()
        user.lastname = lastname
        user.firstname = firstname
        user.grade = int(grade)
        user.cls = int(cls)
        user.num = int(num)
        user.email = email
        user.set_password(data.get('password'))
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'アカウントが作成されました',
            'redirect': url_for('login')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'エラーが発生しました'
        }), 500

@app.route('/api/menu/search')
def api_menu_search():
    """Ajax用メニュー検索エンドポイント"""
    try:
        query = request.args.get('q', '')
        category = request.args.get('category', 'all')
        
        menu_query = Menu.query
        
        if query:
            menu_query = menu_query.filter(
                Menu.productname.contains(query)
            )
        
        if category != 'all':
            menu_query = menu_query.filter_by(category=category)
        
        menus = menu_query.all()
        
        # HTMLレスポンスを生成
        html = render_template('partials/menu_items.html', menus=menus)
        
        return html
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '検索中にエラーが発生しました'
        }), 500

@app.route('/api/reserve', methods=['POST'])
@login_required
def api_reserve():
    """Ajax用予約エンドポイント"""
    try:
        data = request.get_json()
        items = data.get('items', [])
        
        if not items:
            return jsonify({
                'success': False,
                'message': '商品が選択されていません'
            }), 400
        
        # 在庫チェック
        for item in items:
            stock = Stock.query.filter_by(id=item['id']).first()
            if not stock or stock.today_stock is None or stock.today_stock < item['quantity']:
                return jsonify({
                    'success': False,
                    'message': f'商品ID {item["id"]} の在庫が不足しています'
                }), 400
        
        # 予約処理
        item_slot = []
        for item in items:
            for _ in range(item['quantity']):
                item_slot.append(item['id'])
        
        # 5個までに調整
        while len(item_slot) < 5:
            item_slot.append(None)
        item_slot = item_slot[:5]
        
        # 在庫を減らす
        for item_id in item_slot:
            if item_id:
                stock = Stock.query.filter_by(id=item_id).first()
                stock.today_stock -= 1
                Menu.query.filter_by(id=item_id).first().buy_cnt += 1
        
        # 予約を作成
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
        
        return jsonify({
            'success': True,
            'message': '予約が完了しました',
            'redirect': url_for('reserve_done')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '予約中にエラーが発生しました'
        }), 500

@app.route('/api/stock/<int:menu_id>', methods=['GET'])
def api_stock(menu_id):
    """Ajax用在庫確認エンドポイント"""
    try:
        stock = Stock.query.filter_by(id=menu_id).first()
        if stock:
            return jsonify({
                'success': True,
                'stock': stock.today_stock
            })
        else:
            return jsonify({
                'success': False,
                'message': '商品が見つかりません'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'エラーが発生しました'
        }), 500

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
    
    # Ajaxリクエストの場合はJSONレスポンス
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return api_login()
    
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
    
    # Ajaxリクエストの場合はJSONレスポンス
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return api_register()
    
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
def admin():
    data = current_webdata("管理者ページ")
    
    # 統計情報を取得
    user_count = User.query.count()
    today_reservations = Reserved.query.filter_by(reserve_day=Reserved.current_date()).count()
    menu_count = Menu.query.count()
    pending_reservations = Reserved.query.filter_by(state="予約済み").count()
    users = User.query.all()
    
    return render_template("admin/adminmain.html", 
                         data=data, 
                         user_count=user_count,
                         today_reservations=today_reservations,
                         menu_count=menu_count,
                         pending_reservations=pending_reservations,
                         users=users)

# 予約者リスト
@app.route("/admin/reserve_list")
@login_required
@admin_required
def reserve_list():
    data = current_webdata("予約者リスト")
    allday = True
    reserve = Reserved.query.order_by(Reserved.id.desc()).all()
    
    # AJAXリクエストの場合は部分的なコンテンツのみを返す
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template("admin/reserve_list.html", reserve=reserve, allday=allday, data=data)
    
    return render_template("admin/reserve_list.html", reserve=reserve, allday=allday, data=data)



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
    
    # 通知を送信
    send_reservation_status_notification(reserve_id, "準備完了")
    
    flash(f"{reserve_id}は準備完了に変更されました", "success")
    return redirect(url_for("reserve_list"))

@app.route("/admin/reserve/state_completed/<int:reserve_id>" , methods = ["POST", "GET"])
@login_required
@admin_required
def reserve_s_completed(reserve_id):
    reserve_edit = Reserved.query.filter_by(id=reserve_id).first()
    reserve_edit.state = "受取済み"
    db.session.commit()
    
    # 通知を送信
    send_reservation_status_notification(reserve_id, "受取済み")
    
    flash(f"{reserve_id}は受取済みに変更されました", "success")
    return redirect(url_for("reserve_list"))

@app.route("/admin/reserve/state_cancelled/<int:reserve_id>" , methods = ["POST", "GET"])
@login_required
@admin_required
def reserve_s_cancelled(reserve_id):
    reserve_edit = Reserved.query.filter_by(id=reserve_id).first()
    reserve_edit.state = "キャンセル"
    db.session.commit()
    
    # 通知を送信
    send_reservation_status_notification(reserve_id, "キャンセル")
    
    flash(f"{reserve_id}はキャンセルに変更されました", "success")
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
    
    # AJAXリクエストの場合は部分的なコンテンツのみを返す
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template("admin/menu_main_edit.html", menu=menu, data=data, stock=stock, menu_categorys=menu_categorys)
    
    return render_template("admin/menu_main_edit.html", menu=menu, data=data, stock=stock, menu_categorys=menu_categorys)


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

# Admin Ajax API Endpoints
@app.route("/api/admin/product/<int:product_id>")
@login_required
@admin_required
def admin_product_detail(product_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            menu = Menu.query.get_or_404(product_id)
            stock = Stock.query.get(product_id)
            category = Menu_category.query.get(menu.category_id) if menu.category_id else None
            
            return jsonify({
                'success': True,
                'product': {
                    'id': menu.id,
                    'name': menu.productname,
                    'price': menu.price,
                    'description': menu.explanation,
                    'image': url_for('static', filename=menu.product_image) if menu.product_image else None,
                    'sales': menu.buy_cnt,
                    'order': menu.order
                },
                'stock': {
                    'current': stock.today_stock if stock else 0,
                    'limit': stock.today_stock_limit if stock else 0
                },
                'category': {
                    'name': category.category if category else '未分類'
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': False, 'message': 'Invalid request'}), 400

@app.route("/api/admin/product/<int:product_id>", methods=['DELETE'])
@login_required
@admin_required
def admin_delete_product(product_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            menu = Menu.query.get_or_404(product_id)
            db.session.delete(menu)
            db.session.commit()
            return jsonify({'success': True, 'message': '商品を削除しました'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': False, 'message': 'Invalid request'}), 400

@app.route("/api/admin/reservation/<int:reservation_id>")
@login_required
@admin_required
def admin_reservation_detail(reservation_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            reservation = Reserved.query.get_or_404(reservation_id)
            user = reservation.user
            
            return jsonify({
                'success': True,
                'reservation': {
                    'id': reservation.id,
                    'date': reservation.reserve_day,
                    'time': reservation.reserve_time,
                    'total': reservation.price,
                    'status': reservation.state,
                    'product_0': {
                        'name': reservation.menu_item_0.productname,
                        'price': reservation.menu_item_0.price
                    } if reservation.menu_item_0 else None,
                    'product_1': {
                        'name': reservation.menu_item_1.productname,
                        'price': reservation.menu_item_1.price
                    } if reservation.menu_item_1 else None,
                    'product_2': {
                        'name': reservation.menu_item_2.productname,
                        'price': reservation.menu_item_2.price
                    } if reservation.menu_item_2 else None,
                    'product_3': {
                        'name': reservation.menu_item_3.productname,
                        'price': reservation.menu_item_3.price
                    } if reservation.menu_item_3 else None,
                    'product_4': {
                        'name': reservation.menu_item_4.productname,
                        'price': reservation.menu_item_4.price
                    } if reservation.menu_item_4 else None
                },
                'user': {
                    'grade': user.grade,
                    'cls': user.cls,
                    'num': user.num,
                    'lastname': user.lastname,
                    'firstname': user.firstname
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': False, 'message': 'Invalid request'}), 400

@app.route("/api/admin/reservation/<int:reservation_id>/status", methods=['POST'])
@login_required
@admin_required
def admin_update_reservation_status(reservation_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = request.get_json()
            status = data.get('status')
            
            reservation = Reserved.query.get_or_404(reservation_id)
            
            if status == 'ready':
                reservation.state = "準備完了"
            elif status == 'completed':
                reservation.state = "受取済み"
            elif status == 'cancelled':
                reservation.state = "キャンセル"
            else:
                return jsonify({'success': False, 'message': '無効なステータスです'}), 400
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'ステータスを更新しました'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': False, 'message': 'Invalid request'}), 400

@app.route("/api/admin/stock/<int:product_id>/<action>", methods=['POST'])
@login_required
@admin_required
def admin_update_stock(product_id, action):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            stock = Stock.query.get_or_404(product_id)
            
            if action == 'increase':
                if stock.today_stock < stock.today_stock_limit:
                    stock.today_stock += 1
                else:
                    return jsonify({'success': False, 'message': '在庫上限に達しています'}), 400
            elif action == 'decrease':
                if stock.today_stock > 0:
                    stock.today_stock -= 1
                else:
                    return jsonify({'success': False, 'message': '在庫が0です'}), 400
            else:
                return jsonify({'success': False, 'message': '無効な操作です'}), 400
            
            db.session.commit()
            return jsonify({
                'success': True, 
                'message': '在庫を更新しました',
                'newStock': stock.today_stock
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': False, 'message': 'Invalid request'}), 400

@app.route("/api/admin/contact/<int:contact_id>")
@login_required
@admin_required
def admin_contact_detail(contact_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            contact = Contact.query.get_or_404(contact_id)
            user = contact.user
            
            return jsonify({
                'success': True,
                'contact': {
                    'id': contact.id,
                    'title': contact.title,
                    'content': contact.content,
                    'date': contact.contact_day,
                    'time': contact.contact_time
                },
                'user': {
                    'lastname': user.lastname,
                    'firstname': user.firstname,
                    'email': user.email
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': False, 'message': 'Invalid request'}), 400

@app.route("/admin/statistics")
@login_required
@admin_required
def admin_statistics():
    data = current_webdata("統計情報")
    
    # 統計データを取得
    total_users = User.query.count()
    total_reservations = Reserved.query.count()
    total_products = Menu.query.count()
    
    # 今日の予約数
    today = datetime.now().date()
    today_reservations = Reserved.query.filter(
        Reserved.reserve_day == today
    ).count()
    
    # 今月の予約数
    current_month = datetime.now().month
    current_year = datetime.now().year
    month_reservations = Reserved.query.filter(
        db.extract('month', Reserved.reserve_day) == current_month,
        db.extract('year', Reserved.reserve_day) == current_year
    ).count()
    
    # 人気商品トップ5
    popular_products = Menu.query.order_by(Menu.buy_cnt.desc()).limit(5).all()
    
    # 予約状態の統計
    status_stats = db.session.query(
        Reserved.state,
        db.func.count(Reserved.id)
    ).group_by(Reserved.state).all()
    
    # 売上統計
    total_sales = db.session.query(db.func.sum(Reserved.price)).scalar() or 0
    today_sales = db.session.query(db.func.sum(Reserved.price)).filter(
        Reserved.reserve_day == today
    ).scalar() or 0
    
    # AJAXリクエストの場合は部分的なコンテンツのみを返す
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template(
            "admin/statistics.html",
            data=data,
            total_users=total_users,
            total_reservations=total_reservations,
            total_products=total_products,
            today_reservations=today_reservations,
            month_reservations=month_reservations,
            popular_products=popular_products,
            status_stats=status_stats,
            total_sales=total_sales,
            today_sales=today_sales
        )
    
    return render_template(
        "admin/statistics.html",
        data=data,
        total_users=total_users,
        total_reservations=total_reservations,
        total_products=total_products,
        today_reservations=today_reservations,
        month_reservations=month_reservations,
        popular_products=popular_products,
        status_stats=status_stats,
        total_sales=total_sales,
        today_sales=today_sales
    )

# 通知機能
def send_push_notification(user_id, title, message, data=None):
    """プッシュ通知を送信する"""
    try:
        subscriptions = PushSubscription.query.filter_by(user_id=user_id).all()
        
        for subscription in subscriptions:
            try:
                webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {
                            "p256dh": subscription.p256dh,
                            "auth": subscription.auth
                        }
                    },
                    data=json.dumps({
                        "title": title,
                        "message": message,
                        "data": data or {}
                    }),
                    vapid_private_key=app.config.get('VAPID_PRIVATE_KEY'),
                    vapid_claims={
                        "sub": "mailto:admin@kobuy-app.com"
                    }
                )
            except WebPushException as e:
                print(f"Push notification failed: {e}")
                # 失敗したサブスクリプションを削除
                db.session.delete(subscription)
        
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error sending push notification: {e}")
        return False

def create_app_notification(user_id, title, message, notification_type='info', reservation_id=None):
    """アプリ内通知を作成する"""
    try:
        notification = AppNotification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            related_reservation_id=reservation_id
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    except Exception as e:
        print(f"Error creating app notification: {e}")
        return None

@app.route('/api/push/subscribe', methods=['POST'])
@login_required
def subscribe_push():
    """プッシュ通知のサブスクリプションを登録する"""
    try:
        data = request.get_json()
        subscription_info = data.get('subscription')
        
        if not subscription_info:
            return jsonify({'success': False, 'message': 'Subscription info is required'}), 400
        
        # 既存のサブスクリプションを削除
        PushSubscription.query.filter_by(user_id=current_user.id).delete()
        
        # 新しいサブスクリプションを作成
        subscription = PushSubscription(
            user_id=current_user.id,
            endpoint=subscription_info['endpoint'],
            p256dh=subscription_info['keys']['p256dh'],
            auth=subscription_info['keys']['auth']
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Subscription registered successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    """ユーザーの通知一覧を取得する"""
    try:
        notifications = AppNotification.query.filter_by(user_id=current_user.id).order_by(AppNotification.created_at.desc()).limit(20).all()
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.type,
                'is_read': notification.is_read,
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
                'reservation_id': notification.related_reservation_id
            })
        
        return jsonify({'success': True, 'notifications': notifications_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """通知を既読にする"""
    try:
        notification = AppNotification.query.filter_by(id=notification_id, user_id=current_user.id).first()
        
        if not notification:
            return jsonify({'success': False, 'message': 'Notification not found'}), 404
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Notification marked as read'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """すべての通知を既読にする"""
    try:
        AppNotification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'All notifications marked as read'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 管理者用通知送信API
@app.route('/admin/send-notification', methods=['POST'])
@login_required
@admin_required
def send_notification():
    """管理者が通知を送信する"""
    try:
        data = request.get_json()
        title = data.get('title')
        message = data.get('message')
        notification_type = data.get('type', 'info')
        user_ids = data.get('user_ids', [])  # 空の場合は全ユーザー
        
        if not title or not message:
            return jsonify({'success': False, 'message': 'Title and message are required'}), 400
        
        # 対象ユーザーを取得
        if user_ids:
            users = User.query.filter(User.id.in_(user_ids)).all()
        else:
            users = User.query.all()
        
        success_count = 0
        for user in users:
            # アプリ内通知を作成
            app_notification = create_app_notification(
                user.id, title, message, notification_type
            )
            
            # プッシュ通知を送信
            push_success = send_push_notification(user.id, title, message)
            
            if app_notification or push_success:
                success_count += 1
        
        return jsonify({
            'success': True, 
            'message': f'Notification sent to {success_count} users'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 予約状態変更時の通知送信
def send_reservation_status_notification(reservation_id, new_status):
    """予約状態変更時に通知を送信する"""
    try:
        reservation = Reserved.query.get(reservation_id)
        if not reservation:
            return False
        
        user = User.query.get(reservation.user_id)
        if not user:
            return False
        
        status_messages = {
            '準備完了': {
                'title': '商品の準備が完了しました',
                'message': f'予約番号#{reservation.id}の商品の準備が完了しました。昼休み中に購買部でお受け取りください。',
                'type': 'success'
            },
            '受取済み': {
                'title': '商品を受け取りました',
                'message': f'予約番号#{reservation.id}の商品を受け取りました。ご利用ありがとうございました。',
                'type': 'info'
            },
            'キャンセル': {
                'title': '予約がキャンセルされました',
                'message': f'予約番号#{reservation.id}がキャンセルされました。',
                'type': 'warning'
            }
        }
        
        if new_status in status_messages:
            message_data = status_messages[new_status]
            
            # アプリ内通知を作成
            create_app_notification(
                user.id,
                message_data['title'],
                message_data['message'],
                message_data['type'],
                reservation.id
            )
            
            # プッシュ通知を送信
            send_push_notification(
                user.id,
                message_data['title'],
                message_data['message'],
                {'reservation_id': reservation.id, 'status': new_status}
            )
            
            return True
        
        return False
    except Exception as e:
        print(f"Error sending reservation status notification: {e}")
        return False