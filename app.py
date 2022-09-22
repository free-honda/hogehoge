from flask import Flask, request, redirect, render_template, session, flash
import flask_login
from models import dbConnect
from util.user import User
from datetime import timedelta
import hashlib
import uuid
import re


app = Flask(__name__)
app.secret_key = 'secret_key'
app.permanent_session_lifetime = timedelta(minutes=60)


@app.route('/signup')
def signup():
    return render_template('registration/signup.html')

@app.route('/signup', methods=['POST'])
def userSignup():
    #フロントからの情報を受け取る
    name = request.form.get('name')
    email = request.form.get('email')
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')

    pattern = "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

    if name == '' or email =='' or password1 == '' or password2 == '':
        flash('空のフォームがあるようです')
    elif password1 != password2:
        flash('二つのパスワードの値が違っています')
    elif re.match(pattern, email) is None:
        flash('正しいメールアドレスの形式ではありません')
    else:
        uid = uuid.uuid4()
        password = hashlib.sha256(password1.encode('utf-8')).hexdigest()
        user = User(uid, name, email, password)
        user_name= dbConnect.getUserName(email)
        user_email= dbConnect.getUserEmail(name)

        if user_name == name or user_email == email:
            flash('既に登録されているようです')
        elif user_name == None and user_email == None:
            dbConnect.createUser(user)
            UserId = str(uid)
            session['uid'] = UserId
            return redirect('/')
    return redirect('/signup')


@app.route('/login')
def login():
    return render_template('registration/login.html')

@app.route('/login', methods=['POST'])
def userLogin():
    #パラメーターを受け取る
    email = request.form.get('email')
    password = request.form.get('password')

    #値が空かどうかの精査をする。空であればloginへ
    if email =='' or password == '':
        flash('空のフォームがあるようです')
    else:
        user = dbConnect.getUser(email)
        if user is None:
            flash('このユーザーは存在しません')
        else:
            hashPassword = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if hashPassword != user["password"]:
                flash('パスワードが間違っています！')
            else:
                session['uid'] = user["uid"]
                return redirect('/')
    return redirect('/login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def index():
    uid = session.get("uid")
    if uid is None:
        return redirect('/login')
    else:
        channels = dbConnect.getChannelAll()
    return render_template('index.html', channels=channels, uid=uid)

@app.route('/', methods=['POST'])
def add_channel():
    uid = session.get('uid')
    print(uid)
    if uid is None:
        return redirect('/login')
    channel_name = request.form.get('channel-title')
    channel = dbConnect.getChannelByName(channel_name)
    if channel == None:
        channel_description = request.form.get('channel-description')
        dbConnect.addChannel(uid, channel_name, channel_description)
        return redirect('/')
    else:
        error = '既に同じチャンネルが存在しています'
        return render_template('error/error.html', error_message=error)


@app.route('/update_channel', methods=['POST'])
def update_channel():
    cid = request.form.get('cid')
    return 'update'


@app.route('/delete/<cid>')
def delete_channel(cid):
    uid = session.get("uid")
    print(uid)
    if uid is None:
        return redirect('/login')
    else:
        channel = dbConnect.getChannelById(cid)
        print(channel["uid"] == uid)
        if channel["uid"] != uid:
            flash('チャンネルは作成者のみ削除可能です')
            return redirect ('/')
        else:
            dbConnect.deleteChannel(cid)
            channels = dbConnect.getChannelAll()
            return render_template('index.html', channels=channels, uid=uid)


# uidもmessageと一緒に返す
@app.route('/detail/<cid>')
def detail(cid):
    uid = session.get("uid")
    if uid is None:
        return redirect('/login')
    cid = cid
    channel = dbConnect.getChannelById(cid)
    messages = dbConnect.getMessageAll(cid)

    return render_template('detail.html', messages=messages, channel=channel, uid=uid)

@app.route('/message', methods=['GET'])
def show_message():
    cid = 1
    messages = dbConnect.getMessageAll(cid)
    return render_template('hello.html', messages=messages)

# TODO
# sessionからuser_idを取り出してcreateMessageに引数で渡す
@app.route('/message', methods=['POST'])
def add_message():
    uid = session.get("uid")
    if uid is None:
        return redirect('/login')

    message = request.form.get('message')
    channel_id = request.form.get('channel_id')

    if message:
        dbConnect.createMessage(uid, channel_id, message)

    channel = dbConnect.getChannelById(channel_id)
    messages = dbConnect.getMessageAll(channel_id)

    return render_template('detail.html', messages=messages, channel=channel, uid=uid)

@app.route('/delete_message', methods=['POST'])
def delete_message():
    uid = session.get("uid")
    if uid is None:
        return redirect('/login')

    message_id = request.form.get('message_id')
    cid = request.form.get('channel_id')
    print(message_id)
    if message_id:
        dbConnect.deleteMessage(message_id)

    channel = dbConnect.getChannelById(cid)
    messages = dbConnect.getMessageAll(cid)

    return render_template('detail.html', messages=messages, channel=channel, uid=uid)


@app.errorhandler(404)
def show_error404(error):
    return render_template('error/404.html')

@app.errorhandler(500)
def show_error500(error):
    return render_template('error/500.html')

# テスト表示用
@app.route('/error500')
def test_show_error500():
    return render_template('error/500.html')

if __name__ == '__main__':
    app.run(debug=True)