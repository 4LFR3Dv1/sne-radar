# 🚀 SNE Radar - Deploy no Render

## Sobre o Sistema

O SNE (Sistema Neural Estratégico) é um radar de trading automatizado que monitora o mercado de criptomoedas em tempo real, detecta rupturas e envia alertas via Telegram.

## Funcionalidades

- ✅ **Monitoramento em Tempo Real**: BTCUSDT a cada minuto
- ✅ **Detecção de Rupturas**: Algoritmo personalizado baseado em densidade
- ✅ **Alertas Telegram**: Notificações automáticas de eventos
- ✅ **Interface Web**: Dashboard para controle e monitoramento
- ✅ **Análise Técnica**: EMA8, EMA21, SMA200, Volume
- ✅ **Módulos Estratégicos**: Mente fluida, catálogo magnético, backtest

## Deploy no Render

### 1. Preparação

1. Faça fork deste repositório
2. Conecte sua conta do GitHub ao Render
3. Configure as variáveis de ambiente (opcional)

### 2. Deploy Automático

1. Acesse [render.com](https://render.com)
2. Clique em "New +" → "Web Service"
3. Conecte seu repositório GitHub
4. Configure:
   - **Name**: `sne-radar`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Plan**: Free

### 3. Configuração do Telegram (Opcional)

Para receber alertas no Telegram, edite o arquivo `xenos_bot.py`:

```python
TELEGRAM_TOKEN = "SEU_TOKEN_AQUI"
CHAT_ID = "SEU_CHAT_ID_AQUI"
```

## Uso da Interface Web

### Endpoints Disponíveis

- **`/`** - Dashboard principal com controles
- **`/status`** - Status atual do sistema (JSON)
- **`/dados`** - Dados atuais do mercado (JSON)
- **`/rupturas`** - Histórico de rupturas detectadas (JSON)
- **`/iniciar`** - Inicia o radar (POST)
- **`/parar`** - Para o radar (POST)
- **`/health`** - Health check

### Controles

1. **Iniciar Radar**: Clique no botão "Iniciar Radar"
2. **Parar Radar**: Clique no botão "Parar Radar"
3. **Monitoramento**: O status atualiza automaticamente a cada 30 segundos

## Estrutura do Projeto

```
SNEv1/
├── app.py                 # Aplicação Flask principal
├── main.py               # Versão desktop original
├── requirements.txt      # Dependências Python
├── render.yaml          # Configuração Render
├── xenos_bot.py         # Integração Telegram
├── backtest.py          # Módulo de backtest
├── mente_fluida.py      # Análise de ressonância
├── catalogo_magnetico.py # Mapeamento de zonas
└── logs/                # Logs do sistema
```

## Monitoramento

### Logs
- Acesse os logs no painel do Render
- Logs são salvos em `logs/rupturas_criticas.log`

### Métricas
- Preço atual do BTC
- Volume de negociação
- Indicadores técnicos
- Rupturas detectadas
- Alertas enviados

## Troubleshooting

### Problemas Comuns

1. **Erro de Importação**: Verifique se todas as dependências estão no `requirements.txt`
2. **Timeout**: O Render pode ter timeout em requisições longas
3. **Memória**: O plano gratuito tem limitações de memória

### Soluções

1. **Reiniciar Serviço**: Use o painel do Render
2. **Verificar Logs**: Acesse os logs para debug
3. **Health Check**: Use `/health` para verificar status

## Limitações do Plano Gratuito

- ⚠️ **Sleep após 15 min**: O serviço "dorme" após inatividade
- ⚠️ **Limite de CPU**: Processamento limitado
- ⚠️ **Timeout**: Requisições podem timeout
- ⚠️ **Memória**: 512MB RAM disponível

## Próximos Passos

1. **Upgrade para Plano Pago**: Para uso 24/7
2. **Banco de Dados**: Adicionar PostgreSQL para persistência
3. **WebSocket**: Implementar conexão real-time
4. **Múltiplos Ativos**: Expandir para outras criptomoedas

## Suporte

Para dúvidas ou problemas:
1. Verifique os logs no Render
2. Teste os endpoints da API
3. Verifique a configuração do Telegram
