"""
Formularios de autenticación
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from sqlalchemy import or_
from app.models.user import User

class LoginForm(FlaskForm):
    """Formulario de inicio de sesión"""
    correo = StringField('Email o Usuario',
                        validators=[
                            DataRequired(message='Este campo es obligatorio'),
                            Length(min=3, max=120, message='Debe tener entre 3 y 120 caracteres')
                        ],
                        render_kw={'placeholder': 'Email o usuario'})
        
    password = PasswordField('Contraseña',
                            validators=[DataRequired(message='Este campo es obligatorio')],
                            render_kw={'placeholder': 'Contraseña'})
        
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')

class RegisterForm(FlaskForm):
    """Formulario de registro de usuario"""
    full_name = StringField('Nombre completo',
                           validators=[DataRequired(), Length(min=2, max=120)],
                           render_kw={'placeholder': 'Nombre completo'})
        
    username = StringField('Usuario',
                          validators=[
                              DataRequired(message='Este campo es obligatorio'),
                              Length(min=3, max=80, message='Debe tener entre 3 y 80 caracteres')
                          ],
                          render_kw={'placeholder': 'Nombre de usuario único'})
        
    email = StringField('Correo electrónico',
                       validators=[DataRequired(), Email()],
                       render_kw={'placeholder': 'tu@email.com'})
        
    password = PasswordField('Contraseña',
                            validators=[DataRequired(), Length(min=6)],
                            render_kw={'placeholder': 'Mínimo 6 caracteres'})
        
    password_confirm = PasswordField('Confirmar contraseña',
                                   validators=[
                                       DataRequired(),
                                       EqualTo('password', message='Las contraseñas deben coincidir')
                                   ],
                                   render_kw={'placeholder': 'Repetir contraseña'})
        
    role = SelectField('Rol',
                      choices=[
                          ('student', 'Estudiante'),
                          ('teacher', 'Docente'),
                          ('parent', 'Padre/Acudiente'),
                          ('admin', 'Administrador Institucional')
                      ],
                      validators=[DataRequired()],
                      default='student')
        
    submit = SubmitField('Registrarse')
        
    def validate_email(self, field):
        """Validar que el email no esté registrado"""
        usuario = User.query.filter_by(email=field.data.lower()).first()
        if usuario:
            raise ValidationError('Este correo ya está registrado.')
    
    def validate_username(self, field):
        """Validar que el username no esté registrado"""
        usuario = User.query.filter_by(username=field.data.lower()).first()
        if usuario:
            raise ValidationError('Este nombre de usuario ya está en uso.')

class ChangePasswordForm(FlaskForm):
    """Formulario para cambiar contraseña"""
    password_actual = PasswordField('Contraseña actual',
                                   validators=[DataRequired()],
                                   render_kw={'placeholder': 'Contraseña actual'})
        
    password_nueva = PasswordField('Nueva contraseña',
                                  validators=[DataRequired(), Length(min=6)],
                                  render_kw={'placeholder': 'Nueva contraseña'})
        
    password_confirm = PasswordField('Confirmar nueva contraseña',
                                   validators=[
                                       DataRequired(),
                                       EqualTo('password_nueva', message='Las contraseñas deben coincidir')
                                   ],
                                   render_kw={'placeholder': 'Repetir nueva contraseña'})
        
    submit = SubmitField('Cambiar Contraseña')

class ForgotPasswordForm(FlaskForm):
    """Formulario para solicitar recuperación de contraseña"""
    email_or_username = StringField('Email o Usuario',
                                   validators=[
                                       DataRequired(message='Este campo es obligatorio'),
                                       Length(min=3, max=120)
                                   ],
                                   render_kw={'placeholder': 'Tu email o nombre de usuario'})
    submit = SubmitField('Enviar enlace de recuperación')
    
    def validate_email_or_username(self, field):
        """Validar que el email o username exista"""
        input_value = field.data.lower().strip()
        usuario = User.query.filter(
            or_(
                User.email == input_value,
                User.username == input_value
            )
        ).first()
        if not usuario:
            raise ValidationError('No se encontró ningún usuario con este email o nombre de usuario.')

class ResetPasswordForm(FlaskForm):
    """Formulario para restablecer contraseña"""
    password = PasswordField('Nueva contraseña',
                            validators=[DataRequired(), Length(min=6)],
                            render_kw={'placeholder': 'Nueva contraseña'})
        
    password_confirm = PasswordField('Confirmar contraseña',
                                   validators=[
                                       DataRequired(),
                                       EqualTo('password', message='Las contraseñas deben coincidir')
                                   ],
                                   render_kw={'placeholder': 'Repetir contraseña'})
        
    submit = SubmitField('Restablecer Contraseña')