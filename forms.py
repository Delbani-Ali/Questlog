"""
=================================================================
FORMS (QuestLog)
=================================================================
This module defines the forms used throughout the QuestLog
application, powered by Flask-WTF. Each class represents a form
and contains fields with associated validation rules.
=================================================================
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, NumberRange

class RegistrationForm(FlaskForm):
    """
    Form for new users to create an account.
    Validates that the username is unique and that the passwords match.
    """
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=4, max=25)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=6)
    ])
    # Ensures that the value of this field matches the 'password' field.
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password')
    ])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    """
    Form for existing users to log in.
    """
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class QuestForm(FlaskForm):
    """
    Form for administrators to create or edit quests.
    """
    name = StringField('Quest Name', validators=[DataRequired(), Length(min=3, max=150)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=500)])
    # Defines the available categories for a quest.
    category = SelectField('Category', choices=[
        ('drawing', 'Drawing'),
        ('writing', 'Writing'),
        ('exercise', 'Exercise'),
        ('reading', 'Reading')
    ], validators=[DataRequired()])
    # Defines the difficulty levels for a quest.
    difficulty = SelectField('Difficulty', choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ], validators=[DataRequired()])
    xp_reward = IntegerField('XP Reward', validators=[
        DataRequired(), 
        NumberRange(min=1, max=1000)
    ])
    submit = SubmitField('Save Quest')

class TrophyForm(FlaskForm):
    """
    Form for administrators to create or edit trophies.
    """
    name = StringField('Trophy Name', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=300)])
    icon = StringField('Icon (Emoji or URL)', default='🏆', validators=[DataRequired()])
    # Defines the types of requirements to unlock a trophy.
    requirement_type = SelectField('Requirement Type', choices=[
        ('quests_completed', 'Quests Completed'), 
        ('level_reached', 'Level Reached'), 
        ('xp_earned', 'XP Earned')
    ], validators=[DataRequired()])
    requirement_value = IntegerField('Requirement Value', validators=[
        DataRequired(), 
        NumberRange(min=1)
    ])
    xp_reward = IntegerField('XP Reward', default=50, validators=[
        DataRequired(), 
        NumberRange(min=0)
    ])
    submit = SubmitField('Save Trophy') 