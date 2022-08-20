from setuptools import Command
from app import app


@Command
def run_server():
    app.run(host="0.0.0.0", port=49876, use_reloader=True)

if __name__ == '__main__':    
    app.run(host="0.0.0.0", port=49876, use_reloader=True)
    #main()