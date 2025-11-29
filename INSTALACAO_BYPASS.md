# 🚀 Guia de Instalação - ML Crawler com Bypass Avançado

## ⚡ Quick Start

### 1. Instalar Dependências

```bash
# Instalação básica
pip install -r requirements.txt

# Para suporte a CloudScraper (recomendado para contornar CloudFlare)
pip install cloudscraper

# Para suporte a Selenium (headless browser - último recurso)
pip install selenium

# Opcional: Para suporte a Playwright (alternativa ao Selenium)
pip install playwright
```

---

## 📋 Estratégias de Bypass Implementadas

### Estratégia 1: CloudScraper ⭐ (Recomendado)
- **Descrição**: Contorna proteção CloudFlare automaticamente
- **Status**: Ativado por padrão (`USE_CLOUDSCRAPER=true`)
- **Velocidade**: Rápido (similar a requests normal)
- **Confiabilidade**: Alta

```bash
# No .env
USE_CLOUDSCRAPER=true
```

### Estratégia 2: Requests + Proxy 🌐
- **Descrição**: Rotação de IPs via proxies
- **Status**: Ativado se `USE_PROXY=true`
- **Velocidade**: Médio
- **Confiabilidade**: Depende da qualidade dos proxies

```bash
# No .env
USE_PROXY=true
PROXY_LIST=http://proxy1.com:8080,http://proxy2.com:8080
```

### Estratégia 3: Selenium Headless Browser 🤖 (Último Recurso)
- **Descrição**: Usa navegador real para simular acesso humano
- **Status**: Desativado por padrão (muito lento)
- **Velocidade**: Lento (~5-10s por página)
- **Confiabilidade**: Muito alta (mas processador-intensivo)

```bash
# No .env (apenas se outras estratégias falharem)
USE_HEADLESS_BROWSER=true
HEADLESS_BROWSER=selenium
```

---

## ⚙️ Configuração Recomendada

### Cenário 1: Conexão Normal (Sem Bloqueios)

```env
# .env
USE_CLOUDSCRAPER=true
USE_PROXY=false
MIN_DELAY=1
MAX_DELAY=3
DELAY_BETWEEN_PAGES=2
```

### Cenário 2: Com Bloqueios Ocasionais

```env
# .env
USE_CLOUDSCRAPER=true
USE_PROXY=true
SINGLE_PROXY=http://seu-proxy:8080
MIN_DELAY=3
MAX_DELAY=6
DELAY_BETWEEN_PAGES=4
MAX_RETRIES=4
```

### Cenário 3: Bloqueio Pesado

```env
# .env
USE_CLOUDSCRAPER=true
USE_PROXY=true
PROXY_LIST=http://proxy1:8080,http://proxy2:8080,http://proxy3:8080
MIN_DELAY=5
MAX_DELAY=10
DELAY_BETWEEN_PAGES=8
MAX_RETRIES=5
RETRY_WAIT=15
USE_HEADLESS_BROWSER=false  # Ativar apenas se necessário
```

---

## 🔧 Troubleshooting

### ❌ Problema: "CloudScraper timeout"

**Solução**:
1. Aumentar `MAX_DELAY` no `.env`
2. Ativar proxies: `USE_PROXY=true`
3. Testar proxy: `curl -x http://proxy:8080 https://www.google.com`

### ❌ Problema: "HTTP 429 (Too Many Requests)"

**Significa**: Você está fazendo requisições muito rápido.

**Solução**:
```env
# Aumentar delays
MIN_DELAY=5
MAX_DELAY=15
DELAY_BETWEEN_PAGES=10

# Aumentar retry wait
RETRY_WAIT=30
```

### ❌ Problema: "HTTP 403 (Forbidden)"

**Significa**: Mercado Livre bloqueou seu IP/User-Agent.

**Solução**:
```env
# Ativar proxy rotativo
USE_PROXY=true
PROXY_LIST=http://proxy1:8080,http://proxy2:8080,http://proxy3:8080

# Aumentar delays agressivamente
MIN_DELAY=10
MAX_DELAY=20
DELAY_BETWEEN_PAGES=15
```

### ❌ Problema: "0 itens encontrados"

**Possíveis causas**:
1. Seletor CSS mudou no Mercado Livre
2. Página bloqueou (CloudFlare)
3. HTML não foi carregado corretamente

**Solução**:
```bash
# Verificar logs
tail -f logs/ml_crawler.log

# Testar URL diretamente com curl
curl -A "Mozilla/5.0..." "https://lista.mercadolivre.com.br/celular?_Paging=1" | head -100

# Se CloudFlare está bloqueando:
# Ativar CloudScraper ou Selenium
USE_CLOUDSCRAPER=true
USE_HEADLESS_BROWSER=true
```

---

## 🧪 Testando a Configuração

### Teste 1: Verificar Dependências

```bash
python3 << 'EOF'
print("Testando dependências...")

try:
    import cloudscraper
    print("✅ CloudScraper OK")
except:
    print("⚠️ CloudScraper não instalado")

try:
    import selenium
    print("✅ Selenium OK")
except:
    print("⚠️ Selenium não instalado")

try:
    import requests
    print("✅ Requests OK")
except:
    print("❌ Requests não instalado")
EOF
```

### Teste 2: Verificar Requisição

```bash
# Testar sem proxy
python3 -c "from src.scraper import fetch_html; html = fetch_html('https://lista.mercadolivre.com.br/celular?_Paging=1'); print(f'HTML recebido: {len(html)} bytes')"

# Ver logs completos
grep -i "erro\|warning\|cloudflare" logs/ml_crawler.log
```

### Teste 3: Executar Coleta Teste

```bash
# Coletar apenas 1 página de 1 categoria
python3 << 'EOF'
from src.scraper import scrape_all_pages
resultado = scrape_all_pages(
    base_url="https://lista.mercadolivre.com.br/celular",
    categoria="celular",
    max_pages=1,
    max_products=10
)
print(f"Resultado: {resultado}")
EOF
```

---

## 📊 Monitoramento

### Ver Logs em Tempo Real

```bash
# Todos os logs
tail -f logs/ml_crawler.log

# Apenas erros
tail -f logs/ml_crawler.log | grep -i "erro\|warning"

# Apenas sucesso
tail -f logs/ml_crawler.log | grep "✅"
```

### Verificar Status do Banco

```bash
# Contar produtos por categoria
psql -h localhost -U postgres -d ml_crawler -c "
SELECT categoria, COUNT(*) as total FROM produtos GROUP BY categoria;
"

# Ver últimas coletas
psql -h localhost -U postgres -d ml_crawler -c "
SELECT categoria, data_inicio, status, total_produtos FROM coletas ORDER BY data_inicio DESC LIMIT 10;
"
```

---

## 🚀 Performance

### Otimizando para Velocidade (Sem Bloqueios)

```env
USE_CLOUDSCRAPER=true
USE_PROXY=false
MIN_DELAY=0.5
MAX_DELAY=1
DELAY_BETWEEN_PAGES=1
```

### Otimizando para Confiabilidade (Com Bloqueios)

```env
USE_CLOUDSCRAPER=true
USE_PROXY=true
PROXY_LIST=http://proxy1:8080,http://proxy2:8080,...
MIN_DELAY=8
MAX_DELAY=15
DELAY_BETWEEN_PAGES=10
MAX_RETRIES=5
```

---

## 📚 Recursos Externos

- [CloudScraper GitHub](https://github.com/VeNoMouS/cloudscraper)
- [ML Crawler Logs](./logs/)
- [Proxies Gratuitos](https://www.proxy-list.download/)
- [Bright Data (Premium)](https://brightdata.com/)

---

## 💡 Próximas Melhorias Sugeridas

1. **Cache de HTML**: Não fazer re-scraping do mesmo conteúdo
2. **Detecção Automática**: Detectar quando está bloqueado e mudar estratégia
3. **Distribuído**: Usar múltiplos workers em paralelo
4. **API Alternative**: Considerar usar API oficial do Mercado Livre

---

**Última atualização**: 28/11/2025
