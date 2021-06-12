from flask import Flask, render_template, request, redirect, url_for, session, flash
from bson.objectid import ObjectId
from pymongo import MongoClient
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename
import os
import datetime 

app = Flask(__name__)
app.secret_key = 'software_engineering'

uri = "mongodb+srv://jhs1v1:jhs!157227@2021se.mpzwr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
cluster = MongoClient(uri)

database = cluster["2021SE"]
diaryDB = database["Diary"]
userDB = database["User"]

app.config['MONGO_URI']=uri
mongo = PyMongo(app)

@app.route('/')
## first page is signin page (user can signin / signup)
def root():
  return redirect(url_for('signin'))


@app.route('/signin', methods=['POST', 'GET'])
def signin():
  if request.method == 'GET':
    return render_template('signin.html')
  elif request.method == 'POST':
    id = request.form.get('id')
    password = request.form.get('password')

    ## Check authority
    user = userDB.find(  
      {'id': id }
    )

    if user is None:
      flash("ID / 비밀번호가 틀렸습니다.")
      return redirect(url_for('signin'))
    else:
      session['id'] = id
      return redirect(url_for('main'))


@app.route('/signout')
def signout():
  session.pop('id', None)
  return redirect('/')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
  if request.method == 'GET':
    return render_template('signup.html')
  elif request.method == 'POST':
    email = request.form.get('email')
    id = request.form.get('id')
    password = request.form.get('password')
    pwcheck = request.form.get('pwcheck')

    if not(email and id and password and pwcheck):
          flash("모든 정보를 입력해주세요.")
    elif password != pwcheck:
          flash("비밀번호가 일치하지 않습니다.")
    else:    
      addUser = userDB.find_one( 
        {'id': id }
      )
      if addUser is None:
        userDB.insert({
          'email': email,
          'id': id,
          'password': password,
        })
        flash("회원가입이 완료되었습니다. 환영합니다!!!")
        return redirect(url_for('signin'))
      else:
        flash("이미 존재하는 ID 입니다.")
  return render_template('signup.html')


#need to show the diaries in newly added order
@app.route('/main', methods=['GET'])
def main():
  if request.method == 'GET':
    if 'id' in session:
      id = session['id']
    diary = mongo.db.users 
    output = []

    task = userDB.find_one({'id': id})

    for item in diary.find():
      output.append({
        'id': item['_id'],
        'title': item['title'],
        'content': item['content'],
        'image_name': item['image_name'],
        'date': item['date']
      })
    output.reverse()
    return render_template('main.html', output=output, id=id)
  

@app.route('/addDiary', methods=['POST', 'GET'])
def addDiary():
  if request.method == 'GET':
    return render_template('addDiary.html')
  elif request.method == 'POST':
    title = request.form.get('title')
    content = request.form.get('content')
    f = request.files['image']

    if not os.path.exists("./data"):
      os.makedirs('./data')
    filename = secure_filename(f.filename)

    mongo.save_file(f.filename, f)
    mongo.db.users.insert_one({
      'title': title,
      'content': content,
      'image_name': f.filename,
      'date': datetime.datetime.now()
    })
    return redirect(url_for('main'))
 
@app.route('/<filename>')
def file(filename):
  return mongo.send_file(filename)

@app.route('/profile/<title>')
def profile(title):
  user = mongo.db.users.find_one_or_404({'title' : title})
  return f'''
    <h1>title: {title}</h1>
    <p>content: {user['content']}<p>
    <img src="{url_for('file',filename=user['image_name'])}" width="200">
  '''

@app.route('/edit', methods=['POST', 'GET'])
def edit():
  if request.method == 'GET':
    temp_id = request.args.get('id')
    task = mongo.db.users.find_one({'_id': ObjectId(temp_id)})
    return render_template('edit.html',id = task['_id'], title = task['title'], content = task['content'])

  elif request.method == 'POST':
    id = request.form.get('id')
    title = request.form.get('title')
    content = request.form.get('content')
    f = request.files['image']

    if not os.path.exists("./data"):
      os.makedirs('./data')
    filename = secure_filename(f.filename)

    mongo.save_file(f.filename, f)

    mongo.db.users.update_one({'_id': ObjectId(id)}, {'$set': {
        'title': title,
        'content': content,
        'image_name': f.filename
      }})

    return redirect(url_for('main'))

@app.route('/delete', methods=['POST'])
def delete():
  if request.method == 'POST':
    title = request.form.get('title')
    delete_diary = mongo.db.users
    delete_diary.delete_one({
      'title': title
    }) 
    return redirect(url_for('main'))


if __name__ == "__main__":
  app.run(debug=True)
