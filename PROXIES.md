# 🔧 Guia de Uso de Proxies no ML Crawler

## Problema
O Mercado Livre pode bloquear requisições repetidas do mesmo IP, retornando erro 429 (Too Many Requests) ou 403 (Forbidden).

## Solução
Use proxies para rotacionar seu IP e evitar bloqueios.

---

## ⚙️ Configuração

### Opção 1: Usar um Único Proxy

Adicione no arquivo `.env`:

```env
USE_PROXY=true
SINGLE_PROXY=http://185.123.456.789:8080
```

### Opção 2: Usar Múltiplos Proxies (Recomendado)

Adicione no arquivo `.env`:

```env
USE_PROXY=true
PROXY_LIST=http://proxy1.com:8080,http://proxy2.com:8080,http://proxy3.com:8080
```

O sistema automaticamente vai rotacionar entre os proxies a cada requisição.

### Opção 3: Proxy SOCKS5

Para proxies SOCKS5:

```env
USE_PROXY=true
SINGLE_PROXY=socks5://185.123.456.789:1080
```

---

## 🔗 Onde Encontrar Proxies

### Proxies Gratuitos (Qualidade Variável)
- [Proxy List Download](https://www.proxy-list.download/)
- [Free Proxies Nets](https://www.freeproxylists.net/)
- [SSL Proxies](https://www.sslproxies.org/)

⚠️ **Aviso**: Proxies gratuitos costumam ser lentos e pouco confiáveis.

### Serviços Pagos (Recomendado para Produção)
- **Bright Data** (antes Luminati): ~$15-100/mês
- **Oxylabs**: Proxies de qualidade superior
- **Smartproxy**: Bom custo-benefício
- **ScraperAPI**: Já incluem tratamento de proxies automático

---

## 📊 Como Funciona

### Com USE_PROXY=true:

1. **User-Agent Rotativo**: Cada requisição usa um user-agent diferente
2. **Proxy Rotativo**: Se usar PROXY_LIST, cada requisição rotaciona entre os proxies
3. **Fallback**: Se o proxy falhar, tenta fazer a requisição sem proxy
4. **Timeout**: Requisições têm timeout de 15 segundos

### Logs:
```
[PROXY] Usando proxy único: http://185.123.456.789:8080
[PROXY] Usando proxy rotativo: http://proxy2.com:8080
[HTTP] 200 - https://lista.mercadolivre.com.br/...
```

---

## 🚀 Testando Proxies

Para verificar se seus proxies funcionam:

```bash
# Terminal
curl -x http://proxy.com:8080 https://httpbin.org/ip

# Python
import requests

proxies = {"http": "http://proxy.com:8080", "https": "http://proxy.com:8080"}
r = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=5)
print(r.json())
```

---

## ⚠️ Dicas Importantes

1. **Valide proxies regularmente**: Alguns podem ficar offline
2. **Use proxies brasileiros**: Melhor para acessar Mercado Livre
3. **Rate limiting**: Adicione delays entre requisições para não sobrecarregar
4. **Monitorar**: Verifique logs regularmente para detectar bloqueios
5. **Alternativas**: Considere usar ScraperAPI que já gerencia proxies automaticamente

---

## 🔍 Verificar Bloqueios

Se vir muitas requisições retornando 403/429:

1. Verifique se os proxies estão ativos
2. Tente trocar de proxy ou adicionar novos
3. Aumente o intervalo entre requisições
4. Considere usar um serviço premium

---

## 📝 Exemplo Completo de .env

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ml_crawler
DB_USER=postgres
DB_PASSWORD=postgres

# Proxies
USE_PROXY=true
PROXY_LIST=http://proxy1.com:8080,http://proxy2.com:8080,http://proxy3.com:8080

# Ou use um único proxy
# SINGLE_PROXY=http://meu-proxy.com:8080
```

---

## 💡 Próximos Passos

1. Configure seus proxies no `.env`
2. Reinicie o scraper
3. Monitore os logs para confirmar que os proxies estão sendo usados
4. Se ainda tiver bloqueios, considere:
   - Reduzir frequência de requisições
   - Usar serviço proxy premium
   - Implementar delays maiores entre páginas

Boa sorte! 🎯
