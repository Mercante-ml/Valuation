# apps/users/models.py
import re
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError

# --- Validador de CNPJ (Simples) ---
# Em produção, use uma biblioteca como "validate-docbr"
def validate_cnpj(cnpj):
    """Validador simples de formato de CNPJ (apenas dígitos)."""
    cnpj = re.sub(r'[^0-9]', '', cnpj) # Remove pontuação
    if len(cnpj) != 14:
        raise ValidationError("CNPJ deve conter 14 dígitos.")
    if cnpj.isdigit() == False:
        raise ValidationError("CNPJ deve conter apenas dígitos.")
    return cnpj

# --- Manager Customizado ---
class CustomUserManager(BaseUserManager):
    """
    Manager para nosso modelo de usuário customizado.
    Define como criar usuários e superusuários.
    """
    def create_user(self, cnpj, email, razao_social, password=None, **extra_fields):
        """Cria e salva um usuário comum."""
        if not cnpj:
            raise ValueError('O CNPJ é obrigatório')
        if not email:
            raise ValueError('O Email é obrigatório')

        # Normaliza e valida os dados
        email = self.normalize_email(email)
        cnpj = validate_cnpj(cnpj)
        
        # Cria o objeto usuário
        user = self.model(
            cnpj=cnpj,
            email=email,
            razao_social=razao_social,
            **extra_fields
        )
        
        user.set_password(password) # Criptografa a senha
        user.save(using=self._db)
        return user

    def create_superuser(self, cnpj, email, razao_social, password=None, **extra_fields):
        """Cria e salva um superusuário."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True) # Superusuário já nasce ativo

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(cnpj, email, razao_social, password, **extra_fields)

# --- Modelo de Usuário Customizado ---
class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuário customizado que usa CNPJ como login.
    """
    cnpj = models.CharField(
        max_length=14, 
        unique=True, 
        validators=[validate_cnpj],
        help_text="CNPJ (apenas números)"
    )
    email = models.EmailField(unique=True)
    razao_social = models.CharField(max_length=255)
    
    # --- NOVOS CAMPOS ADICIONADOS ---
    ddd = models.CharField(
        max_length=2, 
        blank=True, # Opcional
        null=True,
        verbose_name="DDD"
    )
    telefone = models.CharField(
        max_length=10, # Para 9 dígitos (ex: 912345678) ou 8 dígitos
        blank=True, # Opcional
        null=True,
        verbose_name="Telefone (apenas números)"
    )
    # --- FIM DOS NOVOS CAMPOS ---
    
    # Campo para limitar o uso (como você pediu)
    usage_count = models.PositiveIntegerField(
        default=0, 
        help_text="Contador de quantas vezes o usuário usou o simulador."
    )
    
    # Campos de status do Django
    is_active = models.BooleanField(
        default=True,
        help_text="Define se o usuário pode logar. Desmarque para 'banir' o usuário."
        # Você pode usar isso para confirmação de e-mail,
        # setando default=False e ativando via link de email.
    )
    is_staff = models.BooleanField(
        default=False, 
        help_text="Define se o usuário pode acessar o site de Admin."
    )
    date_joined = models.DateTimeField(auto_now_add=True)

    # --- Configuração ---
    
    # Define o "Manager" que acabamos de criar
    objects = CustomUserManager()

    # Define qual campo será usado para login
    USERNAME_FIELD = 'cnpj'
    
    # Campos obrigatórios ao criar um usuário (ex: createsuperuser)
    REQUIRED_FIELDS = ['email', 'razao_social']

    def __str__(self):
        return f"{self.razao_social} ({self.cnpj})"