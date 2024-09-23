from flask import Flask
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import BooleanField, SubmitField, StringField, SelectField, RadioField, DateField, PasswordField, IntegerField, EmailField, FileField
from wtforms.validators import InputRequired, NumberRange, EqualTo, Email, DataRequired

class RegistrationForm(FlaskForm):
    user_name = StringField("Username:", validators=[DataRequired("Username required")])
    password = PasswordField("Password:", validators=[DataRequired("Password required")])
    password2 = PasswordField("Confirm Password:", validators=[DataRequired("Please confirm password"), EqualTo("password", message="Passwords Must be Equal")])
    email = EmailField("Email:", validators=[DataRequired("Email required"),Email()])
    age = IntegerField("Age:", validators=[DataRequired("Age required"), NumberRange(0,1000000000000, message="Please choose valid numbers")])
    gender = SelectField("Gender:", choices=["Male","Female","Other"])
    level = SelectField("Level:", choices=[] )
    submit = SubmitField("submit")

class LoginForm(FlaskForm):
    user_name = StringField("Username:", validators=[DataRequired("Username required")])
    password = PasswordField("Password:", validators=[DataRequired("Password required")])
    submit = SubmitField("submit")

class ForgotPasswordForm(FlaskForm):
    email = EmailField("Enter Email: ",validators=[Email()])
    submit = SubmitField("Submit")

class ApplicationForm(FlaskForm):
    clear = SubmitField("Clear all")

class AcceptApplicantForm(FlaskForm):
    rank = SelectField("Assign Member Rank:", choices=["Outer Member","Inner Member","Core Member"])
    residence = SelectField("Assign Member Residence:", choices=[])
    submit = SubmitField("Confirm")

class MembersForm(FlaskForm):
    name = SelectField("Name: ", choices=[], default="Any")
    status = SelectField("Status: ", choices=["Active","Deceased","Any"], default="Any")
    rank = SelectField("Rank: ", choices=[], default="Any")
    gender = SelectField("Gender: ", choices=["Female","Male","Other","Any"], default="Any")
    residence = SelectField("Residence: ", choices=[], default="Any")
    order = SelectField("Order By: ", choices=["Age","Gender","Joined","Member ID","Level","Name","Rank","Recent Login","Residence","Status"], default="Name")
    submit = SubmitField("Search")

class ModifyMemberDetailsForm(FlaskForm):
    status = SelectField("Status", choices=["Active","Deceased"])
    rank = SelectField("Rank:", choices=[])
    age = IntegerField("Age:", validators=[DataRequired("Enter an age"),NumberRange(0,1000000000000, message="Please enter a valid age")])
    level = SelectField("Level:", choices=[])
    residence = SelectField("Residence:", choices=[])
    submit = SubmitField("Confirm")

class BaseStorageForm(FlaskForm):
    base = SelectField("Base: ", choices=[], default="Any")
    item = SelectField("Item: ", choices=[], default="Any")
    rarity = SelectField("Rarity: ", choices=[], default="Any")
    submit = SubmitField("Search")

class BaseStorageMovement(FlaskForm):
    item_name3 = SelectField("Item Name: ", choices=[])
    moveTo = SelectField("Move To: ", choices=[])
    quantity = IntegerField("Quantity: ")
    submit = SubmitField("Confirm")

class ItemArchiveForm(FlaskForm):
    item_name = SelectField("Select Item:", choices=[], default="Any")
    item_rarity = SelectField("Select Rarity:", choices=[], default="Any")
    submit = SubmitField("Confirm")

class AddToItemArchiveForm(FlaskForm):
    item_name = StringField("Item Name: ", validators=[DataRequired("Enter Item Name")])
    item_rarity = SelectField("Rarity: ", choices=[])
    item_description = StringField("Item Description: ", validators=[DataRequired("Enter Item Description")])
    submit = SubmitField("Confirm")

class AddNewBaseForm(FlaskForm):
    base_name = StringField("Base Name: ", validators=[DataRequired("Enter Base Name")])
    base_location = StringField("Base Location:", validators=[DataRequired("Enter Base Location")])
    submit = SubmitField("Confirm")

class AddItemsToBase(FlaskForm):
    item_name1 = SelectField("Item Name:", choices=[])
    quantity1 = IntegerField("Quantity:")
    submit1 = SubmitField("Confirm")

class DeleteItemsFromBase(FlaskForm):
    item_name2 = SelectField("Item Name:", choices=[])
    quantity2 = IntegerField("Quantity:")
    submit2 = SubmitField("Confirm")

class AddMissionForm(FlaskForm):
    mission_name = StringField("Mission Name: ", validators=[DataRequired("Enter Mission Name")])
    mission_level = SelectField("Mission Level:", choices=["S","A","B","C","D","E","F"])
    mission_reward = IntegerField("Mission Reward:", validators=[DataRequired("Enter Mission Reward"), NumberRange(0, message="Use Positive Numbers")])
    rank_requirement = SelectField("Required Rank: ", choices=["Outer Member", "Inner Member", "Core Member", "Any"], default="Any")
    mission_description = StringField("Mission Description: ", validators=[DataRequired("Enter Mission Description")])
    mission_party_limit = IntegerField("Party Limit: ", validators=[DataRequired("Enter Party Limit"), NumberRange(0, message="Use Positive Numbers")])
    submit = SubmitField("Confirm")

class AcceptMissionForm(FlaskForm):
    submit = SubmitField("Accept")

class MissionSearchingForm(FlaskForm):
    mission_id = SelectField("Mission ID:", choices=[], default="Any")
    mission_status = SelectField("Mission Status:", choices=["Any","Closed","Incomplete"], default="Any")
    difficulty = SelectField("Difficulty: ", choices=["S","A","B","C","D","E","F","Any",], default="Any")
    rank_requirement = SelectField("Rank Requirement: ", choices=["Core Member","Inner Member","Outer Member","Any"], default="Any")
    submit = SubmitField("Confirm")

class PermissionForm(FlaskForm):
    new_permission_rank = SelectField("Rank:", choices=[])
    submit = SubmitField("Confirm")

class PfpForm(FlaskForm):
    file = FileField("File", validators=[InputRequired("Upload an image"), FileAllowed(["png","jpg","jfif"], "File not allowed")])
    submit = SubmitField("Confirm")


    





