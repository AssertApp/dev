from flask import Flask, request, session, redirect, render_template
from itsdangerous import URLSafeSerializer
import mysql.connector, json
from uuid import uuid4 as genUUID

app = Flask(__name__)

itsdangerous1 = ""
itsdangerous2 = ""

#database has these tables:
#users: users for assert
#
#devurls:
#+-------+------+---------------+
#| devid | url  | urlIdentifier |
#+-------+------+---------------+
#| TEXT  | TEXT | TEXT          |
#+-------+------+---------------+
#
#developers: format (uuid text, secretkey text)

def URLValidate(url):
    if url.startswith("http://"):
        return url.replace("http://","https://")
    if not url.startswith("https://"):
        return "https://" + url
    return url

def database():
    return mysql.connector.connect(host="HOST", user="USER", password="PASSWORD", database="DATABASE")

def safeEncrypt(data):
    auths = URLSafeSerializer(itsdangerous1, itsdangerous2)
    return auths.dumps(data)

def safeDecrypt(data):
    auths = URLSafeSerializer(itsdangerous1, itsdangerous2)
    return auths.loads(data)

@app.route('/')
def index():
    if not 'id' in session:
        return "The Assert Developer Portal will be coming soon!"
    uuid=session['id']
    conn = database()
    cur = conn.cursor()
    cur.execute(f"select uuid from developers where uuid='{uuid}';")
    try:
        assert cur.fetchall()[0][0]==uuid
    except:
        return redirect('/auth')
    cur.execute(f"select url, urlIdentifier from devurls where devid='{uuid}';")
    results = cur.fetchall()
    try:
        urls = []
        for link in results:
            urls.append({"url":link[0],"uuid":link[1]})
    except:
        urls = False
    return render_template('developers.html', urls=urls)

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
    cur.execute(f"select uuid from developers where uuid='{uuid}';")
    try:
        if not cur.fetchall()[0][0]==uuid:
            return "I have no idea what happened here"
    except:
        encrypted = safeEncrypt({'id': uuid})
        cur.execute(f"insert into developers values ('{uuid}','{encrypted}');")
        conn.commit()
        conn.close()
    return redirect('/')

@app.route('/submitLink', defaults={'link': None})
@app.route('/submitLink/<link>')
def submitLink(link):
    try:
        link = URLValidate(request.args.get('link'))
    except:
        return redirect('/')
    if not 'id' in session:
        return redirect('/auth')
    uuid = session['id']
    conn = database()
    cur = conn.cursor()
    cur.execute(f"select uuid from developers where uuid='{uuid}';")
    try:
        assert cur.fetchall()[0][0]==uuid
    except:
        return redirect('/auth')
    cur.execute(f"select url from devurls where devid='{uuid}';")
    results = cur.fetchall()
    executeSQL = True
    for result in results:
        if result[0].startswith(link):
            cur.execute(f"update devurls set url='{link}' where url='{result[0]}';")
            executeSQL = False
        if link.startswith(result[0]):
            return redirect('/')
            executeSQL = False
    done = False
    while not done:
        newUUID = genUUID()
        cur.execute(f"select urlIdentifier from devurls where urlIdentifier='{newUUID}' and devid='{uuid}';")
        try:
            assert cur.fetchall()[0][0]==newUUID
        except:
            done = True
    if executeSQL:
        cur.execute(f"insert into devurls values ('{uuid}','{link}','{newUUID}');")
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/delete', defaults={"link": None})
@app.route('/delete/<link>')
def delete(link):
    link = request.args.get('link')
    if not link:
        return redirect('/')
    conn = database()
    cur = conn.cursor()
    cur.execute(f"select * from devurls where urlIdentifier='{link}' and devid='{session['id']}';")
    try:
        assert cur.fetchall()[0][0]
    except:
        return redirect('/')
    cur.execute(f"delete from devurls where urlIdentifier='{link}' and devid='{session['id']}';")
    conn.commit()
    conn.close()
    return redirect('/')

if __name__=='__main__':
    app.run()
