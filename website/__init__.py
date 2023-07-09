from flask import Flask

def create_app():
    app = Flask(__name__,static_url_path='/website/static')
    app.config["SECRET_KEY"]='AYA'
    from .views import views
    app.register_blueprint(views, url_prefix='/')
    return app