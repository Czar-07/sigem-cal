# SIGEM CAL — versão profissional

## Inicialização

### 1. Ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Criar configuração segura

```powershell
Copy-Item .env.example .env
python scripts/security.py
```

Copie os valores gerados para `.env`.

### 3. Banco e execução

```powershell
python create_db.py
python app.py
```

Em produção, não use o servidor de desenvolvimento do Flask. Utilize um servidor WSGI como Gunicorn (Linux) ou Waitress (Windows).

## Estrutura

O projeto foi organizado por responsabilidade e mantém os dados operacionais dentro da própria pasta do projeto:

```text
SIGEM_CAL/
├── app.py
├── config.py
├── app/
│   ├── admin/
│   ├── api/
│   ├── auth/
│   ├── core/
│   ├── database/
│   ├── middleware/
│   ├── models/
│   ├── public/
│   ├── services/
│   ├── templates/
│   └── utils/
├── excel/
├── uploads/
├── instance/
├── scripts/
├── requirements.txt
├── .env.example
└── ARCHITECTURE.md
```

## Segurança de credenciais

Nunca distribua o `.env`. O repositório contém apenas `.env.example`.

A senha administrativa é armazenada como hash. Senhas SMTP e outros segredos de configuração são criptografados no banco.

## Dados grandes

`Certificados.zip` e `uploads/` são dados operacionais, não código. Eles ficam separados da camada de aplicação para que o código possa ser versionado e atualizado sem duplicar centenas de megabytes.
