from flask import Flask, request, session, redirect, render_template
from itsdangerous import URLSafeSerializer
import mysql.connector, json

app = Flask(__name__)

#database has these tables:
#users: users for assert
#devurls: format (devid text, url text)
#developers: format (uuid text, secretkey text)

def database():
    return mysql.connector.connect(host="host", user="user", password="password", database="database")

def safeEncrypt(data):
    auths = URLSafeSerializer("SECRETKEY1", "SECRETKEY2")
    return auths.dumps(data)

def safeDecrypt(data):
    auths = URLSafeSerializer("SECRETKEY1", "SECRETKEY2")
    return auths.loads(data)

@app.route('/')
def index():
    if not 'id' in session:
        return "The Assert Developer Portal will be coming soon!"
    uuid=session['id']
    conn = database()
    cur = conn.cursor()
    cur.execute(f"select urls from developers where id='{uuid}';")
    links = json.loads(cur.fetchall()[0][0])
    urls = []
    try:
        areThereLinks = True
        for link in links:
            urls.append(
                {"url":link}
            )
    except:
        areThereLinks = False
    return render_template('developers.html', links=areThereLinks, urls=urls)

@app.route('/auth')
def auth():
    return redirect('https://assertapp.net/auth?redir=https://dev.assertapp.net/authconfirm')

@app.route('/authconfirm', defaults={'token': None})
@app.route('/authconfirm/<token>')
def authconfirm(token):
    token = request.args.get('token')
    if not token:
        return "Token not specified"
    token = safeDecrypt(token)
    uuid = token["sub"]
    conn = database()
    cur = conn.cursor()
    cur.execute(f"select id from users where id='{uuid}';")
    try:
        if not cur.fetchall()[0][0]==uuid:
            return "Error"
    except:
        return "Error"
    session['id']=uuid
    cur.execute(f"select id from developers where id='{uuid}';")
    try:
        if not cur.fetchall()[0][0]==uuid:
            return "I have no idea what happened here"
    except:
        encrypted = safeEncrypt({'id': uuid})
        cur.execute(f"insert into developers values ('{uuid}','{encrypted}','');")
        conn.commit()
        conn.close()
    return redirect('/')

@app.route('/submitLink', defaults={'link': None})
@app.route('/submitLink/<link>')
def submitLink(link):
    link = request.args.get('link')
    if not link:
        return redirect('/')
    if not 'id' in session:
        return redirect('/auth')
    uuid = session['id']
    conn = database()
    cur = conn.cursor()
    cur.execute(f"select urls from developers where id='{uuid}';")
    results = cur.fetchall()
    try:
        data = json.loads(results[0][0])
        if link in data:
            return redirect('/')
        data.append(link)
        returnJSON = json.dumps(data)
    except:
        returnJSON = json.dumps([link])
    cur.execute(f"update developers set urls='{returnJSON}' where id='{uuid}';")
    conn.commit()
    conn.close()
    return redirect('/')

if __name__=='__main__':
    app.run()
