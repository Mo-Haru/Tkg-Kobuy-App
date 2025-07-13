from kobuy_app import db, create_app

create_db = 0
# 0(app.run) or 1(create database)
app = create_app()

if __name__ == '__main__':
    if create_db == 0:
        app.run(host="0.0.0.0",port="80", threaded=True)
        # サーバー上で動かすときはhost="0.0.0.0",port="80", threaded=True
        
    if create_db == 1:
        with app.app_context():
            db.create_all()
            print("データベースを作成しました")
            from kobuy_app.models.models import Sale_state
            from kobuy_app.models.models import Role
            if Sale_state.query.filter_by(id=0).first() is None:
                tpm = Sale_state(
                    id = 0,
                    state = False,
                    state_name = "販売停止中"
                )
                tmps = Role(
                    id = 1,
                    name = "admin"
                )
                db.session.add(tmps)
                db.session.add(tpm)
                db.session.commit()
                print("DBの初期設定完了")