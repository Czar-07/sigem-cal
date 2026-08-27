# SIGEM — Pacote compacto

Este pacote **não contém o `Certificados.zip`** nem cópias extraídas dos certificados.

## Estrutura recomendada

Coloque o arquivo de certificados ao lado da pasta do SIGEM:

```text
Dados/
├── Certificados.zip
└── sigem-main/
    ├── app.py
    ├── app/
    ├── instance/
    ├── excel/
    └── ...
```

O SIGEM procura automaticamente `Certificados.zip` na pasta do projeto e também na pasta pai. Portanto, não é necessário editar código.

Também é possível definir um caminho explícito no `.env`:

```env
CERTIFICATES_FOLDER=../Certificados.zip
```

## Por que ficou menor?

Foram removidos do pacote:

- `Certificados.zip` (fonte original, para ser mantida separadamente);
- PDFs duplicados em `uploads/certificates/`;
- pasta `fix/`, que era uma cópia do projeto;
- backups antigos do Excel;
- arquivos de teste e documentação interna desnecessários para execução;
- caches e `__pycache__`.

Os certificados continuam acessíveis pela aplicação porque o serviço de certificados lê o arquivo original diretamente quando necessário.
