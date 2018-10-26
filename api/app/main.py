from flask import Flask
from flask import jsonify
import mysql.connector

app = Flask(__name__)

@app.route('/search/')
def empty_search():
    return jsonify('Please specify a search term')

@app.route('/search/<q>')
def search(q):
    sqlQ = '''
        SELECT num, month, link, news, save_title, transcript, alt, img, title,
            day
        FROM comics
        WHERE MATCH(title,save_title,alt,transcript) AGAINST(%s)'''

    db = mysql.connector.connect(
      host="127.0.0.1",
      user="root",
      passwd="",
      database="xkcd-search"
    )

    if(not db):
        return jsonify({
            'error': True,
            'cause': 'Could not establish a database connection. Please start screaming now.'
        }), 500

    cursor = db.cursor(prepared=True)
    cursor.execute(sqlQ, (q,))
    res = cursor.fetchall()

    answer = []
    for row in res:
        answer.append({
            'num':        row[0],
            'month':      row[1],
            'link':       row[2],
            'news':       row[3],
            'save_title': row[4].decode('utf-8'),
            'transcript': row[5],
            'alt':        row[6].decode('utf-8'),
            'img':        row[7].decode('utf-8'),
            'title':      row[8].decode('utf-8'),
            'day':        row[9]
        })
    
    return jsonify(answer)
