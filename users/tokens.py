# users/tokens.py
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six # pip install six (se não estiver instalado)

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # Garante que o hash mude se o status de ativação do usuário mudar
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_active)
        )

account_activation_token = AccountActivationTokenGenerator()