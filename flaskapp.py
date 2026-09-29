from io import BytesIO
from flask import Flask, render_template, request, redirect, send_file, url_for
import sqlite3

app = FLASK(__name__)

DB_PATH = '/var/www/html/flaskapp/hitesj.db'

# SQLite setup
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users 
            ( id INTEGER PRIAMRY KEY AUTOINCREMENT,
                username TEXT NO NULL,
                password TEXT NOT NULL,
                email TEXT NOT NULL,
                address TEXT,
                firstname TEXT,
                lastname TEXT )''')
c.execute('''CREATE TABLE IF NOT EXISTS files
            ( id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                content BLOB NOT NULL,
                username TEXT)''')
conn.commit()
conn.close()

@app.route('/')
def index():
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("SELECT id FROM users WHERE username = ?", (username,))
            idRes = c.fetchone()
            if idRes is None:
                return render_template('login.html', error='User not found. Please register.')

            else:
                c.execute("SELECT COUNT(*) FROM users WHERE id = ? AND password = ?", (idRes[0], password))
                userFoundRes = c.fetchone()
                if int(userFoundRes[0]) < 1:
                    return render_template('login.html', error='Unknown username or password. Please try again.')
                else:
                    return redirect(url_for('profile', username=username))

        except sqlite3.Error as error:
            conn.close()
            return f"Login Failed: {error}", 500


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        address = request.form['address']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try: 
            c.execute("INSERT INTO users (username, password, firstname, lastname, email, address) VALUES (?, ?, ?, ?, ?, ?)",
                (username, lastname, firstname, lastname, email, address))
            conn.commit()
            conn.close()
            return redirect(url_for('profile', username=username))

        except sqlite3.Error as error:
            conn.close()
            return f"Registration Failed: {error}", 500
        

@app.route('/profile/<username>', methods=['GET', 'POST'])
def profile(username):
    conn =  sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if request.method == 'GET':
        try:
            c.execute("SELECT username, firstname, lastname, email, address FROM users WHERE username = ?", (username,))
            user = c.fetchone()

            c.execute("SELECT * FROM files WHERE username=?", (username,))
            file = c.fetchone()
            filelist = []
            while file is not None:
                id, filename, content, username = file
                id = "/download/" + str(id)
                numWords = len(content.decode('utf8').split())
                filelist.append({"id": id, "name": filename, "words": numWords})

                file = c.fetchone()

            conn.close()
            return render_template('profile.html', user=user, files=filelist)

        except sqlite3.Error as error:
            conn.close()
            return f"Failed to find a file: {error}", 500

    elif request.method == 'POST':
        upload_file = request.files['file']

        if upload_file and upload_file.filename:
            content = upload_file.read()
            filename = uplaod_file.filename

            try:
                c.execute("INSERT INTO files (name, content, username) VALUES (?, ?, ?)", (filename, content, username))
                conn.commit()
                conn.close()
                return redirect(url_for('profile', username=username))

            except sqlite3.Error as error:
                conn.close()
                return f"Failed to upload a file: {error}", 500

@app.route('/download/<fileid>')
def download(fileid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM files WHERE id=?", (fileid,))
    fileRes = c.fetchone()
    if fileRes is not None:
        id, filename, content, username = fileRes
        return send_file(
            BytesIO(content),
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name=filename or "download"
        )
    
    else:
        return "File not found", 404


if __name__ == '__main__':
    app.run(debug=True)