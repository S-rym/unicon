from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/graph')
def graph():
    return render_template('graph.html')

@app.route('/map')
def map():
    return render_template('map.html')

# search_reservation.html用ルート追加
@app.route('/search_reservation')
def search_reservation():
    return render_template('search_reservation.html')

# setting.html用ルート追加
@app.route('/setting')
def setting():
    return render_template('setting.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
