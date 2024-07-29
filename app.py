from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///polls.db'
db = SQLAlchemy(app)
socketio = SocketIO(app)

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(200), nullable=False)
    options = db.relationship('Option', backref='poll', lazy=True)
    


class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False)
    votes = db.Column(db.Integer, default=0)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)

@app.route('/')
def index():
    polls = Poll.query.all()
    return render_template('index.html', polls=polls)

@app.route('/create_poll', methods=['POST'])
def create_poll():
    question = request.form['question']
    options = request.form.getlist('options')
    poll = Poll(question=question)
    db.session.add(poll)
    db.session.commit()
    for option_text in options:
        option = Option(text=option_text, poll_id=poll.id)
        db.session.add(option)
    db.session.commit()
    return jsonify({'message': 'Poll created successfully!', 'poll': {
        'id': poll.id,
        'question': poll.question,
        'options': [{'id': opt.id, 'text': opt.text, 'votes': opt.votes} for opt in poll.options]
    }})


@app.route('/delete_poll/<int:poll_id>', methods=['POST'])
def delete_poll(poll_id):
    poll = Poll.query.get(poll_id)
    if not poll:
        return jsonify({'message': 'Poll not found'}), 404

    Option.query.filter_by(poll_id=poll_id).delete()
    db.session.delete(poll)
    db.session.commit()

    return jsonify({'message': 'Poll deleted successfully!'})





@socketio.on('vote')
def handle_vote(data):
    option_id = data['option_id']
    option = Option.query.get(option_id)
    option.votes += 1
    db.session.commit()

    poll_id = option.poll_id
    poll = Poll.query.get(poll_id)
    options = [{'id': opt.id, 'votes': opt.votes} for opt in poll.options]
    emit('update_poll', {'poll_id': poll_id, 'options': options}, broadcast=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
