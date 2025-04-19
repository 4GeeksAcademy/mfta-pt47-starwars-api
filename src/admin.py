import os
from flask_admin import Admin
from models import db, User, Planet, Character, Weight, Character_Favorite, Planet_Favorite
from flask_admin.contrib.sqla import ModelView

# Crear vistas personalizadas para cada modelo
class UserView(ModelView):
    column_list=('Id', 'Email', 'Username', 'Password', 'IsActive', 'CreatedAt', 'Characters_Favorites_Association', 'Planets_Favorites_Association')

class CharacterView(ModelView):
    column_list=('Id', 'Name', 'Height', 'HairColor', 'BirthDay', 'HomeWorldId', 'Weight', 'HomeWorld', 'Users_Favorites_Association')

class PlanetView(ModelView):
    column_list=('Id', 'Name', 'Climate', 'Terrain', 'Characters', 'Users_Favorites_Association')

class WeightView(ModelView):
    column_list=('CharacterId', 'Weight', 'WeightUnit', 'Character')

class Character_FavoriteView(ModelView):
    column_list=('UserId', 'CharacterId', 'User', 'Character')

class Planet_FavoriteView(ModelView):
    column_list=('UserId', 'PlanetId', 'User', 'Planet')

def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    admin = Admin(app, name='4Geeks Admin', template_mode='bootstrap3')

    
    # Add your models here, for example this is how we add a the User model to the admin
    admin.add_view(UserView(User, db.session))
    admin.add_view(CharacterView(Character, db.session))
    admin.add_view(WeightView(Weight, db.session))
    admin.add_view(PlanetView(Planet, db.session))
    admin.add_view(Character_FavoriteView(Character_Favorite, db.session))
    admin.add_view(Planet_FavoriteView(Planet_Favorite, db.session))

    # You can duplicate that line to add mew models
    # admin.add_view(ModelView(YourModelName, db.session))