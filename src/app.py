"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
import datetime
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Character, Planet, Character_Favorite, Planet_Favorite, Weight, ClimateEnum, TerrainEnum, WeightUnitEnum, HairColorEnum
# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
# Agregado por mi, para que no cambie el orden de las llaves en el json
app.json.sort_keys = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints


@app.route('/')
def sitemap():
    return generate_sitemap(app)

##########################################################
# USERS 
##########################################################
@app.route('/users', methods=['GET']) #-------------------------------------Get Users
def get_users():
    """
    Get all users
    """
    users = User.query.all()

    if not users:
        return jsonify({"message": "No users found"}), 404

    return jsonify([user.serialize() for user in users]), 200


@app.route('/users/<int:user_id>', methods=['GET']) #------------------------Get User by ID
def get_user(user_id):
    """
    Get a user by id
    """
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify(user.serialize()), 200


@app.route('/users', methods=['POST']) #-----------------------------------------------Create User
def create_user():
    """
    Create a new user
    Example:
    {
        "username": "new_username",
        "email": "new_email",
        "password": "new_password",
        "is_active": true
    }
    """
    body = request.get_json()

    if not body:
        return jsonify({"message": "No input data provided"}), 400

    if 'username' not in body:
        return jsonify({"message": "Username is required"}), 400

    if 'email' not in body:
        return jsonify({"message": "Email is required"}), 400
    
    if 'password' not in body:
        return jsonify({"message": "Password is required"}), 400
    
    # Check if the username already exists
    if User.query.filter_by(Username=body['username']).first():
        return jsonify({"message": "Username already exists"}), 400
    
    # Check if the email already exists
    if User.query.filter_by(Email=body['email']).first():
        return jsonify({"message": "Email already exists"}), 400
    
    # Check if the password is strong enough
    if len(body['password']) < 8:
        return jsonify({"message": "Password must be at least 8 characters long"}), 400


    new_user = User(
        Username=body['username'],
        Email=body['email'],
        Password=body['password'],
        IsActive=body.get('is_active', False)
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.serialize()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating user", "error": str(e)}), 500
    finally:
        db.session.close()


@app.route('/users/<int:user_id>', methods=['PUT']) #-------------------------------------Update User
def update_user(user_id):
    """
    Update a user by id
    Example:
    {
        "username": "new_username",
        "email": "new_email",
        "current_password": "current_password",
        "password": "new_password",
        "is_active": true
    }
    """
    body = request.get_json()

    if not body:
        return jsonify({"message": "No input data provided"}), 400
    
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404
    
    if 'username' in body:
        # Check if the username is different from the current one
        if body['username'] != user.Username:
            # Check if the username already exists
            if User.query.filter_by(Username=body['username']).first():
                return jsonify({"message": "Username already exists"}), 400
            
    if 'email' in body:
        # Check if the email is different from the current one
        if body['email'] != user.Email:
            # Check if the email already exists
            if User.query.filter_by(Email=body['email']).first():
                return jsonify({"message": "Email already exists"}), 400
            
    # To update the password, the user must provide the current password
    if 'password' in body:
        if 'current_password' not in body:
            return jsonify({"message": "Current password is required to update the password"}), 400
        if body['current_password'] != user.Password:
            return jsonify({"message": "Current password is incorrect"}), 400
        if len(body['password']) < 8:
            return jsonify({"message": "Password must be at least 8 characters long"}), 400
        user.Password = body['password']

    if 'is_active' in body:
        user.IsActive = body['is_active']

    user.Username = body.get('username', user.Username)
    user.Email = body.get('email', user.Email)
    user.Password = body.get('password', user.Password)
    user.IsActive = body.get('is_active', user.IsActive)
    
    try:
        db.session.commit()
        return jsonify(user.serialize()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error updating user", "error": str(e)}), 500
    finally:
        db.session.close()
    

@app.route('/users/<int:user_id>', methods=['DELETE']) #--------------------------------Delete User
def delete_user(user_id):
    """
    Delete a user by id
    """
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error deleting user", "error": str(e)}), 500
    finally:
        db.session.close()


@app.route('/users/<int:user_id>/favorites/characters', methods=['POST']) #----------------Add Character to Favorites
def add_character_to_favorites(user_id):
    """
    Add a character to the user's favorites
    Example:
    {
        "character_id": 1
    }
    """
    body = request.get_json()

    if not body:
        return jsonify({"message": "No input data provided"}), 400

    if 'character_id' not in body:
        return jsonify({"message": "Character ID is required"}), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    character = Character.query.get(body['character_id'])

    if not character:
        return jsonify({"message": "Character not found"}), 404
    
    # Check if the character is already in the user's favorites
    if Character_Favorite.query.filter_by(UserId=user.Id, CharacterId=character.Id).first():
        return jsonify({"message": "Character already in favorites"}), 400

    favorite = Character_Favorite(
        UserId=user.Id,
        CharacterId=character.Id
    )

    try:
        db.session.add(favorite)
        db.session.commit()
        return jsonify(user.serialize()["characters_favorites"]), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error adding character to favorites", "error": str(e)}), 500
    finally:
        db.session.close()


@app.route('/users/<int:user_id>/favorites/characters/<int:character_id>', methods=['DELETE']) #----------------Remove Character from Favorites
def remove_character_from_favorites(user_id, character_id):
    """
    Remove a character from the user's favorites
    """
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    character = Character.query.get(character_id)

    if not character:
        return jsonify({"message": "Character not found"}), 404

    favorite = Character_Favorite.query.filter_by(
        UserId=user.Id, CharacterId=character.Id).first()

    if not favorite:
        return jsonify({"message": "Favorite not found"}), 404

    try:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify(user.serialize()["characters_favorites"]), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error removing character from favorites", "error": str(e)}), 500
    finally:
        db.session.close()


@app.route('/users/<int:user_id>/favorites/planets', methods=['POST']) #----------------Add Planet to Favorites
def add_planet_to_favorites(user_id):
    """
    Add a planet to the user's favorites
    Example:
    {
        "planet_id": 1
    }
    """
    body = request.get_json()

    if not body:
        return jsonify({"message": "No input data provided"}), 400

    if 'planet_id' not in body:
        return jsonify({"message": "Planet ID is required"}), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    planet = Planet.query.get(body['planet_id'])

    if not planet:
        return jsonify({"message": "Planet not found"}), 404
    
    # Check if the planet is already in the user's favorites
    if Planet_Favorite.query.filter_by(UserId=user.Id, PlanetId=planet.Id).first():
        return jsonify({"message": "Planet already in favorites"}), 400

    favorite = Planet_Favorite(
        UserId=user.Id,
        PlanetId=planet.Id
    )

    try:
        db.session.add(favorite)
        db.session.commit()
        return jsonify(user.serialize()["planets_favorites"]), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error adding planet to favorites", "error": str(e)}), 500
    finally:
        db.session.close()


@app.route('/users/<int:user_id>/favorites/planets/<int:planet_id>', methods=['DELETE']) #----------------Remove Planet from Favorites
def remove_planet_from_favorites(user_id, planet_id):
    """
    Remove a planet from the user's favorites
    """
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    planet = Planet.query.get(planet_id)

    if not planet:
        return jsonify({"message": "Planet not found"}), 404

    favorite = Planet_Favorite.query.filter_by(
        UserId=user.Id, PlanetId=planet.Id).first()

    if not favorite:
        return jsonify({"message": "Favorite not found"}), 404

    try:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify(user.serialize()["planets_favorites"]), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error removing planet from favorites", "error": str(e)}), 500
    finally:
        db.session.close()



############################################################
# CHARACTERS
############################################################
@app.route('/characters', methods=['GET']) #-----------------------------------Get Characters
def get_characters():
    """
    Get all characters
    """
    characters = Character.query.all()

    if not characters:
        return jsonify({"message": "No characters found"}), 404

    return jsonify([character.serialize() for character in characters]), 200


@app.route('/characters/<int:character_id>', methods=['GET']) #----------------Get Character by ID
def get_character(character_id):
    """
    Get a character by id
    """
    character = Character.query.get(character_id)

    if not character:
        return jsonify({"message": "Character not found"}), 404

    return jsonify(character.serialize()), 200


@app.route('/characters', methods=['POST']) #----------------------------------Create Character
def create_character():
    """
    Create a new character
    """
    body = request.get_json()

    if not body:
        return jsonify({"message": "No input data provided"}), 400

    if 'name' not in body:
        return jsonify({"message": "Name is required"}), 400
    
    # Check if the name already exists
    if Character.query.filter_by(Name=body['name']).first():
        return jsonify({"message": "Name already exists"}), 400

    # Check if the hair color is valid
    if 'hair_color' in body:
        if body['hair_color'] not in HairColorEnum.get_all():
            return jsonify({"message": "Invalid hair color"}), 400
    
    # Check if the height is a valid integer
    if 'height' in body:
        try:
            body['height'] = int(body['height'])
        except ValueError:
            return jsonify({"message": "Height must be an integer"}), 400
    
    # Check if the birth day is a valid date
    if 'birth_day' in body:
        try:
            body['birth_day'] = datetime.datetime.strptime(body['birth_day'], '%d-%m-%Y').date()
        except ValueError:
            return jsonify({"message": "Birth day must be in DD-MM-YYYY format"}), 400
    
    # Check if the home world id is a valid integer
    if 'home_world_id' in body:
        try:
            body['home_world_id'] = int(body['home_world_id'])
        except ValueError:
            return jsonify({"message": "Home world id must be an integer"}), 400
    # Check if the home world id exists
    if 'home_world_id' in body:
        home_world = Planet.query.get(body['home_world_id'])
        if not home_world:
            return jsonify({"message": "Home world not found"}), 404
    
    new_character = Character(
        Name=body['name'],
        Height=body.get('height', None),
        HairColor=body['hair_color'],
        BirthDay=body['birth_day'],
        HomeWorldId=body['home_world_id']
    )

    if 'weight' in body:
        # Check if the weight is a valid float
        try:
            body['weight'] = float(body['weight'])
        except ValueError:
            return jsonify({"message": "Weight must be a float"}), 400
        
        # Check if the weight unit is valid
        if 'weight_unit' in body:
            if body['weight_unit'] not in WeightUnitEnum.get_all():
                return jsonify({"message": "Invalid weight unit"}), 400
        else:
            body['weight_unit'] = WeightUnitEnum.KG.value
        
        # Create a new weight object
        new_weight = Weight(
            Weight=body['weight'],
            WeightUnit=body['weight_unit']
        )
        new_character.Weight = new_weight

    try:
        db.session.add(new_character)
        db.session.commit()
        return jsonify(new_character.serialize()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating character", "error": str(e)}), 500
    finally:
        db.session.close()


@app.route('/characters/<int:character_id>', methods=['PUT']) #--------------------Update Character
def update_character(character_id):
    """
    Update a character by id
    """
    body = request.get_json()

    if not body:
        return jsonify({"message": "No input data provided"}), 400
    
    character = Character.query.get(character_id)

    if not character:
        return jsonify({"message": "Character not found"}), 404
    
    if 'name' in body:
        # Check if the name is different from the current one
        if body['name'] != character.Name:
            # Check if the name already exists
            if Character.query.filter_by(Name=body['name']).first():
                return jsonify({"message": "Name already exists"}), 400
            
    if 'hair_color' in body:
        # Check if the hair color is different from the current one
        if body['hair_color'] != character.HairColor:
            # Check if the hair color is valid
            if body['hair_color'] not in HairColorEnum.get_all():
                return jsonify({"message": "Invalid hair color"}), 400
    
    # Check if the height is a valid integer
    if 'height' in body:
        try:
            body['height'] = int(body['height'])
        except ValueError:
            return jsonify({"message": "Height must be an integer"}), 400
    
    # Check if the birth day is a valid date
    if 'birth_day' in body:
        try:
            body['birth_day'] = datetime.datetime.strptime(body['birth_day'], '%d-%m-%Y').date()
        except ValueError:
            return jsonify({"message": "Birth day must be in DD-MM-YYYY format"}), 400
    
    # Check if the home world id is a valid integer
    if 'home_world_id' in body:
        try:
            body['home_world_id'] = int(body['home_world_id'])
        except ValueError:
            return jsonify({"message": "Home world id must be an integer"}), 400
        # Check if the home world id exists
        home_world = Planet.query.get(body['home_world_id'])
        if not home_world:
            return jsonify({"message": "Home world not found"}), 404

    # Check if the weight is a valid float
    if 'weight' in body:
        try:
            body['weight'] = float(body['weight'])
        except ValueError:
            return jsonify({"message": "Weight must be a float"}), 400
        
        # Check if the weight unit is valid
        if 'weight_unit' in body:
            if body['weight_unit'] not in WeightUnitEnum.get_all():
                return jsonify({"message": "Invalid weight unit"}), 400
        else:
            body['weight_unit'] = WeightUnitEnum.KG.value
        
        # Update the weight object
        if character.Weight:
            character.Weight.Weight = body['weight']
            character.Weight.WeightUnit = body['weight_unit']
        else:
            new_weight = Weight(
                Weight=body['weight'],
                WeightUnit=body['weight_unit']
            )
            character.Weight = new_weight

    # Update the character object
    character.Name = body.get('name', character.Name)
    character.Height = body.get('height', character.Height)
    character.HairColor = body.get('hair_color', character.HairColor)
    character.BirthDay = body.get('birth_day', character.BirthDay)
    character.HomeWorldId = body.get('home_world_id', character.HomeWorldId)

    try:
        db.session.commit()
        return jsonify(character.serialize()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error updating character", "error": str(e)}), 500
    finally:
        db.session.close()


@app.route('/characters/<int:character_id>', methods=['DELETE']) #--------------Delete Character
def delete_character(character_id):
    """
    Delete a character by id
    """
    character = Character.query.get(character_id)

    if not character:
        return jsonify({"message": "Character not found"}), 404

    try:
        db.session.delete(character)
        db.session.commit()
        return jsonify({"message": "Character deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error deleting character", "error": str(e)}), 500
    finally:
        db.session.close()



############################################################
# PLANETS
############################################################
@app.route('/planets', methods=['GET']) #----------------------------------------Get Planets
def get_planets():
    """
    Get all planets
    """
    planets = Planet.query.all()

    if not planets:
        return jsonify({"message": "No planets found"}), 404

    return jsonify([planet.serialize() for planet in planets]), 200


@app.route('/planets/<int:planet_id>', methods=['GET']) #------------------------Get Planet by ID
def get_planet(planet_id):
    """
    Get a planet by id
    """
    planet = Planet.query.get(planet_id)

    if not planet:
        return jsonify({"message": "Planet not found"}), 404

    return jsonify(planet.serialize()), 200


@app.route('/planets', methods=['POST']) #---------------------------------------Create Planet
def create_planet():
    """
    Create a new planet
    """
    body = request.get_json()

    if not body:
        return jsonify({"message": "No input data provided"}), 400

    if 'name' not in body:
        return jsonify({"message": "Name is required"}), 400
    
    # Check if the name already exists
    if Planet.query.filter_by(Name=body['name']).first():
        return jsonify({"message": "Name already exists"}), 400
    
    # Check if the climate is valid
    if 'climate' in body:
        if body['climate'] not in ClimateEnum.get_all():
            return jsonify({"message": "Invalid climate"}), 400
        
    # Check if the terrain is valid
    if 'terrain' in body:
        if body['terrain'] not in TerrainEnum.get_all():
            return jsonify({"message": "Invalid terrain"}), 400

    new_planet = Planet(
        Name=body['name'],
        Climate=body.get('climate', ClimateEnum.UNKNOWN.value),
        Terrain=body.get('terrain', TerrainEnum.UNKNOWN.value)
    )

    try:
        db.session.add(new_planet)
        db.session.commit()
        return jsonify(new_planet.serialize()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating planet", "error": str(e)}), 500
    finally:
        db.session.close()


@app.route('/planets/<int:planet_id>', methods=['PUT']) #---------------------------Update Planet
def update_planet(planet_id):
    """
    Update a planet by id
    """
    body = request.get_json()

    if not body:
        return jsonify({"message": "No input data provided"}), 400
    
    planet = Planet.query.get(planet_id)

    if not planet:
        return jsonify({"message": "Planet not found"}), 404
    
    if 'name' in body:
        # Check if the name is different from the current one
        if body['name'] != planet.Name:
            # Check if the name already exists
            if Planet.query.filter_by(Name=body['name']).first():
                return jsonify({"message": "Name already exists"}), 400
            
    if 'climate' in body:
        # Check if the climate is different from the current one
        if body['climate'] != planet.Climate.value:
            # Check if the climate is valid
            if body['climate'] not in ClimateEnum.get_all():
                return jsonify({"message": "Invalid climate"}), 400
    
    if 'terrain' in body:
        # Check if the terrain is different from the current one
        if body['terrain'] != planet.Terrain.value:
            # Check if the terrain is valid
            if body['terrain'] not in TerrainEnum.get_all():
                return jsonify({"message": "Invalid terrain"}), 400

    # Update the planet object
    planet.Name = body.get('name', planet.Name)
    planet.Climate = body.get('climate', planet.Climate.value)
    planet.Terrain = body.get('terrain', planet.Terrain.value)

    try:
        db.session.commit()
        return jsonify(planet.serialize()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error updating planet", "error": str(e)}), 500
    finally:
        db.session.close()


@app.route('/planets/<int:planet_id>', methods=['DELETE']) #------------------------------Delete Planet
def delete_planet(planet_id):
    """
    Delete a planet by id
    """
    planet = Planet.query.get(planet_id)

    if not planet:
        return jsonify({"message": "Planet not found"}), 404

    try:
        db.session.delete(planet)
        db.session.commit()
        return jsonify({"message": "Planet deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error deleting planet", "error": str(e)}), 500
    finally:
        db.session.close()






# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
