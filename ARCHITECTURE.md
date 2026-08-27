# SIGEM CAL — Arquitetura profissional

## Camadas

- `app/api/` — endpoints JSON e integração HTTP.
- `app/admin/` — telas administrativas organizadas por domínio.
- `app/auth/` — autenticação administrativa.
- `app/core/` — primitives compartilhadas (segurança, arquivos, constantes).
- `app/database/` — extensão SQLAlchemy e migrações.
- `app/middleware/` — autenticação e políticas HTTP.
- `app/models/` — entidades persistidas.
- `app/services/` — regras de negócio e integrações.
- `app/utils/` — funções puras/utilitários.
- `app/templates/` — interface Jinja.
- `scripts/` — operações de manutenção/segurança.
- `excel/` — planilha operacional.
- `uploads/` — dados gerados em execução; não deve ser versionado.
- `instance/` — banco SQLite; não deve ser versionado.

## Segurança

1. Senha administrativa com hash PBKDF2.
2. Segredos de configurações (SMTP/password/token/secret) criptografados com Fernet.
3. Chave de criptografia derivada da `SECRET_KEY`; trocar a `SECRET_KEY` sem migrar os segredos torna os dados criptografados ilegíveis.
4. Cookies HttpOnly + SameSite.
5. CSP, HSTS em HTTPS, X-Frame-Options, Referrer-Policy e Permissions-Policy.
6. `.env`, banco e uploads excluídos do Git.
7. Ambiente de produção rejeita `SECRET_KEY` fraca e ausência de `ADMIN_PASSWORD_HASH`.

## Observação importante

Criptografar código-fonte Python não é uma proteção real contra engenharia reversa quando o programa precisa executá-lo. Para distribuição fechada, use build/empacotamento e controle de acesso ao servidor. O projeto foi protegido principalmente no que realmente importa: credenciais, sessão, segredos persistidos e superfície HTTP.
