import datetime
import enum
from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, DateTime, Date, Enum
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()

###############################
# Enums
###############################


class HairColorEnum(str, enum.Enum):
    BLACK = "black"
    BROWN = "brown"
    BLONDE = "blonde"
    RED = "red"
    GREY = "grey"
    WHITE = "white"
    UNKNOWN = "unknown"

    @classmethod
    def get_all(cls):
        return [color.value for color in cls]


class ClimateEnum(str, enum.Enum):
    TROPICAL = "tropical"
    TEMPERATE = "temperate"
    ARID = "arid"
    POLAR = "polar"
    UNKNOWN = "unknown"

    @classmethod
    def get_all(cls):
        return [climate.value for climate in cls]


class TerrainEnum(str, enum.Enum):
    DESERT = "desert"
    GRASSLAND = "grassland"
    MOUNTAIN = "mountain"
    FOREST = "forest"
    SWAMP = "swamp"
    OCEAN = "ocean"
    UNKNOWN = "unknown"

    @classmethod
    def get_all(cls):
        return [terrain.value for terrain in cls]


class WeightUnitEnum(str, enum.Enum):
    KG = "kg"
    LB = "lb"
    OZ = "oz"

    @classmethod
    def get_all(cls):
        return [unit.value for unit in cls]


###############################
# Database Models
###############################


class User(db.Model):
    __tablename__ = "Users"
    Id: Mapped[int] = mapped_column(primary_key=True)
    Email: Mapped[str] = mapped_column(String(50), unique=True)
    Username: Mapped[str] = mapped_column(String(30), unique=True)
    Password: Mapped[str] = mapped_column(String(300))
    IsActive: Mapped[bool] = mapped_column(Boolean())
    CreatedAt: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now)

    Characters_Favorites_Association: Mapped[Optional[list["Character_Favorite"]]] = db.relationship(
        back_populates="User", cascade="all, delete-orphan")
    Planets_Favorites_Association: Mapped[Optional[list["Planet_Favorite"]]] = db.relationship(
        back_populates="User", cascade="all, delete-orphan")

    def __str__(self):
        return self.Username

    def __repr__(self):
        return f"User(Id={self.Id}, Username={self.Username})"

    def serialize(self):
        return {
            "id": self.Id,
            "email": self.Email,
            "username": self.Username,
            "is_active": self.IsActive,
            "created_at": self.CreatedAt,
            "characters_favorites": [{"id": fav.Character.Id, "name": fav.Character.Name} for fav in self.Characters_Favorites_Association],
            "planets_favorites": [{"id": fav.Planet.Id, "name": fav.Planet.Name} for fav in self.Planets_Favorites_Association],
        }


class Character(db.Model):
    __tablename__ = "Characters"
    Id: Mapped[int] = mapped_column(primary_key=True)
    Name: Mapped[str] = mapped_column(String(50), unique=True)
    Height: Mapped[Optional[int]] = mapped_column()
    HairColor: Mapped[enum] = mapped_column(
        Enum(HairColorEnum), default=HairColorEnum.UNKNOWN.value)
    BirthDay: Mapped[Optional[datetime.date]] = mapped_column(Date())
    HomeWorldId: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey("Planets.Id"))

    Weight: Mapped[Optional["Weight"]] = db.relationship(
        back_populates="Character", uselist=False, cascade="all, delete-orphan")
    HomeWorld: Mapped[Optional["Planet"]] = db.relationship(
        back_populates="Characters")

    Users_Favorites_Association: Mapped[Optional[list["Character_Favorite"]]] = db.relationship(
        back_populates="Character", cascade="all, delete-orphan")

    def __str__(self):
        return self.Name

    def __repr__(self):
        return f"Character(Id={self.Id}, Name={self.Name})"

    def serialize(self):
        return {
            "id": self.Id,
            "name": self.Name,
            "height": self.Height,
            "weight": self.Weight.serialize()["weight"] if self.Weight else None,
            "hair_color": self.HairColor.value,
            "birth_day": self.BirthDay,
            "home_world": self.HomeWorld.serialize()["name"] if self.HomeWorld else None,
            "users_favorites": [fav.User.Username for fav in self.Users_Favorites_Association],
        }


class Weight(db.Model):
    __tablename__ = "Weights"
    CharacterId: Mapped[int] = mapped_column(
        db.ForeignKey("Characters.Id"), primary_key=True)
    Weight: Mapped[float] = mapped_column()
    WeightUnit: Mapped[enum] = mapped_column(
        Enum(WeightUnitEnum), default=WeightUnitEnum.KG.value)

    Character: Mapped["Character"] = db.relationship(back_populates="Weight")

    def __str__(self):
        return f"{self.Weight} {self.WeightUnit.value}"

    def __repr__(self):
        return f"Weight(Id={self.CharacterId}, Weight={self.Weight}, Unit={self.WeightUnit.value})"

    def serialize(self):
        return {
            "character_id": self.CharacterId,
            "weight": f"{self.Weight} {self.WeightUnit.value}",
        }


class Planet(db.Model):
    __tablename__ = "Planets"
    Id: Mapped[int] = mapped_column(primary_key=True)
    Name: Mapped[str] = mapped_column(String(50), unique=True)
    Climate: Mapped[enum] = mapped_column(
        Enum(ClimateEnum), default=ClimateEnum.UNKNOWN.value)
    Terrain: Mapped[enum] = mapped_column(
        Enum(TerrainEnum), default=TerrainEnum.UNKNOWN.value)

    Characters: Mapped[Optional[list["Character"]]] = db.relationship(
        back_populates="HomeWorld")

    Users_Favorites_Association: Mapped[Optional[list["Planet_Favorite"]]] = db.relationship(
        back_populates="Planet", cascade="all, delete-orphan")

    def __str__(self):
        return self.Name

    def __repr__(self):
        return f"Planet(Id={self.Id}, Name={self.Name})"

    def serialize(self):
        return {
            "id": self.Id,
            "name": self.Name,
            "climate": self.Climate.value,
            "terrain": self.Terrain.value,
            "characters": [character.Name for character in self.Characters],
            "users_favorites": [fav.User.Username for fav in self.Users_Favorites_Association],
        }


class Character_Favorite(db.Model):
    __tablename__ = "Characters_Favorites"
    UserId: Mapped[int] = mapped_column(
        db.ForeignKey("Users.Id"), primary_key=True)
    CharacterId: Mapped[int] = mapped_column(
        db.ForeignKey("Characters.Id"), primary_key=True)

    User: Mapped["User"] = db.relationship(
        back_populates="Characters_Favorites_Association", uselist=False)
    Character: Mapped["Character"] = db.relationship(
        back_populates="Users_Favorites_Association", uselist=False)

    def __str__(self):
        return f"{self.User.Username} likes {self.Character.Name}"

    def __repr__(self):
        return f"Character_Favorite(UserId={self.UserId}, CharacterId={self.CharacterId})"


class Planet_Favorite(db.Model):
    __tablename__ = "Planets_Favorites"
    UserId: Mapped[int] = mapped_column(
        db.ForeignKey("Users.Id"), primary_key=True)
    PlanetId: Mapped[int] = mapped_column(
        db.ForeignKey("Planets.Id"), primary_key=True)

    User: Mapped["User"] = db.relationship(
        back_populates="Planets_Favorites_Association", uselist=False)
    Planet: Mapped["Planet"] = db.relationship(
        back_populates="Users_Favorites_Association", uselist=False)

    def __str__(self):
        return f"{self.User.Username} likes {self.Planet.Name}"

    def __repr__(self):
        return f"Planet_Favorite(UserId={self.UserId}, PlanetId={self.PlanetId})"
