# SIGEM CAL 1.7 — Professional Edition

Sistema web Flask para gestão de instrumentos, calibrações, certificados, relatórios e sincronização com Excel.

## Excel fora da pasta do projeto

Sim. O SIGEM CAL agora aceita `EXCEL_PATH` como caminho relativo ou absoluto.

Exemplo Windows:
```env
EXCEL_PATH=C:/Dados/Calibracao/Controle Calibração de Dispositivos 2026 REV1.xlsx
```

Exemplo de pasta de rede:
```env
EXCEL_PATH=//servidor/qualidade/Calibracao/Controle Calibração de Dispositivos 2026 REV1.xlsx
```

O caminho é lido pelo **servidor Flask**, não pelo navegador. Portanto, o computador/servidor onde o SIGEM CAL estiver rodando precisa ter acesso ao arquivo e permissão de leitura.

## Sincronização

- `python import_excel.py` faz uma importação manual.
- `python scripts/watch_excel.py` faz a sincronização inicial e monitora alterações no arquivo.
- O botão **Sincronizar** no painel chama `POST /api/sync/run` e atualiza os dados sob demanda.

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python create_db.py
python import_excel.py
python app.py
```

Para produção, altere `SECRET_KEY` e as credenciais administrativas e mantenha `.env` fora do controle de versão.

## Principais melhorias desta edição

- Interface visual profissional, responsiva e consistente.
- Sidebar escura com navegação ativa e hierarquia visual.
- Navbar com pesquisa global, perfil e sincronização.
- Feedback visual por toast para sincronização.
- Login administrativo redesenhado.
- Suporte a Excel externo por caminho absoluto/UNC.
- API de sincronização manual.
- Watcher do Excel baseado na configuração do `.env`.
- Validação de existência e extensão do arquivo Excel.


## SIGEM CAL — atualização profissional

A versão atual inclui:

- **Importação manual do Excel** pelo botão `Importar Excel` disponível no painel.
- Validação da planilha antes da substituição do arquivo ativo.
- Backup automático do Excel anterior em `excel/backups/`.
- Registro persistente da **última sincronização**, origem e versão.
- Dashboard executivo com indicadores de vencidos, vencendo e sem data.
- Gráficos de status, clientes, condições, certificados e calendário de calibrações.
- Central de notificações com histórico, status e deduplicação por dispositivo/vencimento.
- Motor de alertas para calibrações próximas do vencimento e atrasadas.
- Envio de e-mail em HTML via SMTP.
- Configuração profissional de SMTP em **Configurações → E-mail**.
- E-mail de teste para validar a integração.
- Monitor automático de notificações quando o sistema é executado por `python app.py`.
- Banco de dados inicializado automaticamente para as novas tabelas.

### SMTP

É possível configurar o SMTP pela interface ou por variáveis de ambiente. Para produção, prefira manter a senha fora do banco:

```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=usuario@empresa.com
SMTP_PASSWORD=senha-ou-segredo
SMTP_SENDER=sigem@empresa.com
```

Depois, em **Configurações → E-mail**, informe os destinatários e ative o envio automático.

### Excel

O importador utiliza a primeira linha de cabeçalho real da planilha (`header=1`) e normaliza espaços/quebras de linha. O arquivo de referência da pasta `excel/` foi atualizado com a planilha fornecida para esta versão.

## Sincronização automática de certificados

A aba **Certificados** agora possui um sincronizador idempotente. Ele:

- lê `Certificados.zip` ou uma pasta configurada em `CERTIFICATES_FOLDER`;
- identifica certificados pelo nome `... NNN-AAAA (DC-XXXX).pdf/xlsx`;
- identifica relatórios de terceiros quando o caminho contém `DC_XXXX...`;
- vincula o DC diretamente ao `Device.numero`;
- prioriza PDF quando existe PDF e XLSX do mesmo certificado;
- copia o arquivo para `uploads/certificates/AAAA/`;
- registra a origem e uma assinatura do arquivo para detectar novos/alterados;
- mantém certificados inalterados sem reprocessamento;
- informa DCs que não existem na base de dispositivos.

Por padrão, o sistema procura `Certificados.zip` na pasta imediatamente acima do projeto. Para outra localização, defina `CERTIFICATES_FOLDER` no `.env`.

A sincronização é acionada automaticamente ao abrir a aba (no máximo uma vez a cada 5 minutos por sessão) e também pode ser executada manualmente pelo botão **Sincronizar certificados**.
