from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    # Flask-SocketIO সার্ভার চালু করা হচ্ছে
    socketio.run(app, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)