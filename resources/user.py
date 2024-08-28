
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, get_jwt

from blocklist import BLOCKLIST
import models
from db import db
from sqlalchemy.exc import SQLAlchemyError
from schemas import UserSchema


blp = Blueprint("Users", "users", description="Operations on users")

@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        if models.UserModel.query.filter(models.UserModel.username == user_data["username"]).first():
            abort(409, message = "A user exists")
        
        user = models.UserModel(
            username = user_data["username"],
            password = pbkdf2_sha256.hash(user_data["password"])
        )
        db.session.add(user)
        db.session.commit()

        return {
            "message": "User Createddd"
        }, 201


@blp.route("/user/<int:user_id>")
class User(MethodView):
    @blp.response(200, UserSchema)
    def get(self, user_id):        
        user = models.UserModel.query.get_or_404(user_id)
        return user

    def delete(self, user_id):
        user = models.UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": "User Deleted"}, 200
        

@blp.route("/login")
class LoginUser(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = models.UserModel.query.filter(
            models.UserModel.username == user_data["username"]
        ).first()

        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(identity=user.id)
            return {
                "access token": access_token,
                "refresh token": refresh_token
            }
        
        abort(401, message="Invalid Creds.")

@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
       current_user = get_jwt_identity()
       access_token = create_access_token(identity=current_user, fresh=False)
       jti = get_jwt()["jti"]
       BLOCKLIST.add(jti)
       return {
            "access token": access_token,                
        }
        
       

@blp.route("/logout")
class LogoutUser(MethodView):
    @jwt_required()
    def post(self):
       jti = get_jwt()['jti']
       BLOCKLIST.add(jti)
       return {
        "message": "Logged out"
       }, 201

