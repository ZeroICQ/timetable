import fdb
from flask import Flask
from flask import request

app = Flask(__name__)

@app.route("/")
def hello():
    con = fdb.connect(
        dsn='db/TIMETABLE.FDB',
        user='SYSDBA',
        password='masterkey',
        charset='UTF8'
    )

    cur = con.cursor()
    query = 'SELECT * FROM WEEKDAYS';
    cur.execute(query);
    s = ''

    for r in cur.fetchall():
        s += str(r) + '<br>'
    return s