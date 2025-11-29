"""
Gerenciador avançado de requisições com múltiplas estratégias de bypass
para contornar bloqueios do Mercado Livre e CloudFlare.
"""

import requests
import time
import random
import logging
import gzip
import io
from typing import Optional, Dict
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Importar brotli se disponível
try:
    import brotli
    HAS_BROTLI = True
except ImportError:
    HAS_BROTLI = False

logger = logging.getLogger(__name__)

# ========== ESTRATÉGIA 1: cloudscraper (CloudFlare bypass) ==========

try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False
    logger.warning("⚠️ cloudscraper não instalado. Instale com: pip install cloudscraper")

# ========== ESTRATÉGIA 2: Selenium (Headless Browser) ==========

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False
    logger.warning("⚠️ Selenium não instalado. Instale com: pip install selenium")


class RequestHandler:
    """Gerenciador de requisições com retry automático e múltiplas estratégias"""
    
    def __init__(self, config):
        self.config = config
        self.session = self._create_session()
        self.scraper = self._create_cloudscraper() if HAS_CLOUDSCRAPER else None
        self.driver = None
        
    def _create_session(self) -> requests.Session:
        """Cria sessão requests com retry automático"""
        session = requests.Session()
        
        # Configurar retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _create_cloudscraper(self):
        """Cria instância de cloudscraper para bypass CloudFlare"""
        try:
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
            logger.info("✅ CloudScraper inicializado")
            return scraper
        except Exception as e:
            logger.warning(f"⚠️ Erro ao inicializar CloudScraper: {e}")
            return None
    
    def _get_headers(self) -> Dict:
        """Retorna headers realistas variáveis"""
        from .config import USER_AGENTS
        
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
    
    def _get_proxy(self) -> Optional[Dict]:
        """Seleciona proxy aleatório se configurado"""
        from .config import USE_PROXY, PROXY_LIST, SINGLE_PROXY
        
        if not USE_PROXY:
            return None
        
        proxy_url = None
        if SINGLE_PROXY:
            proxy_url = SINGLE_PROXY
        elif PROXY_LIST:
            proxy_url = random.choice(PROXY_LIST)
        
        if not proxy_url:
            return None
        
        # Normalizar URL de proxy
        if not proxy_url.startswith(('http://', 'https://', 'socks5://')):
            proxy_url = f"http://{proxy_url}"
        
        return {
            "http": proxy_url,
            "https": proxy_url
        }
    
    def _decompress_if_needed(self, content: bytes) -> str:
        """Descompacta conteúdo se estiver em gzip ou brotli"""
        try:
            # Testar se é gzip (magic number: 0x1f 0x8b)
            if content[:2] == b'\x1f\x8b':
                logger.debug("Descompactando com gzip...")
                return gzip.decompress(content).decode('utf-8')
        except Exception as e:
            logger.debug(f"Gzip falhou: {e}")
        
        try:
            # Testar se é brotli (magic number: 0xce 0xb2 0xcf 0x81)
            if HAS_BROTLI and content[:2] == b'\xce\xb2':
                logger.debug("Descompactando com brotli...")
                return brotli.decompress(content).decode('utf-8')
        except Exception as e:
            logger.debug(f"Brotli falhou: {e}")
        
        # Tentar decodificar normalmente
        try:
            return content.decode('utf-8')
        except:
            return content.decode('utf-8', errors='ignore')
    
    def _apply_delay(self):
        """Aplica delay aleatório entre requisições"""
        from .config import MIN_DELAY, MAX_DELAY
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        logger.debug(f"⏳ Aguardando {delay:.1f}s antes da requisição...")
        time.sleep(delay)
    
    def fetch(self, url: str, max_retries: Optional[int] = None) -> Optional[str]:
        """
        Busca conteúdo com múltiplas estratégias e retry automático.
        
        Estratégias (nessa ordem):
        1. CloudScraper (se disponível) - contorna CloudFlare
        2. Requests normal com proxy (com retries)
        3. Selenium headless browser (se habilitado)
        
        Args:
            url: URL para buscar
            max_retries: Número máximo de tentativas
        
        Returns:
            HTML do conteúdo ou None se falhar
        """
        from .config import MAX_RETRIES, RETRY_WAIT, USE_CLOUDSCRAPER, USE_HEADLESS_BROWSER
        
        max_retries = max_retries or MAX_RETRIES
        retry_wait = RETRY_WAIT
        html_sem_produtos = False
        
        # ===== ESTRATÉGIA 1: CloudScraper (sem retries) =====
        if USE_CLOUDSCRAPER and self.scraper:
            logger.info(f"[Estratégia 1/3] 🌐 CloudScraper: {url}")
            try:
                self._apply_delay()
                response = self.scraper.get(
                    url,
                    headers=self._get_headers(),
                    timeout=20
                )
                if response.status_code == 200:
                    html = self._decompress_if_needed(response.content)
                    # Verificar se HTML tem produtos (heurística simples)
                    if "ui-search-layout__item" in html or "poly-card" in html:
                        logger.info(f"✅ CloudScraper sucesso: HTTP {response.status_code}")
                        return html
                    else:
                        logger.warning(f"⚠️ CloudScraper: HTTP 200 mas sem produtos (SPA/JavaScript)")
                        html_sem_produtos = True
                elif response.status_code in [403, 429]:
                    logger.warning(f"❌ CloudScraper bloqueado: HTTP {response.status_code}")
                else:
                    logger.warning(f"⚠️ CloudScraper: HTTP {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️ Erro CloudScraper: {str(e)[:100]}")
        
        # ===== ESTRATÉGIA 2: Requests com proxy (COM retries) =====
        logger.info(f"[Estratégia 2/3] 📡 Requests com retry ({max_retries}x)...")
        for tentativa in range(1, max_retries + 1):
            try:
                self._apply_delay()
                
                logger.info(f"  [Tentativa {tentativa}/{max_retries}] 📡 Requests: {url}")
                proxy = self._get_proxy()
                if proxy:
                    logger.debug(f"     Proxy: {proxy.get('http', 'N/A')[:50]}...")
                
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    proxies=proxy,
                    timeout=10,  # Reduzido de 20 para não travar com proxies ruins
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    html = self._decompress_if_needed(response.content)
                    # Verificar se HTML tem produtos (heurística simples)
                    if "ui-search-layout__item" in html or "poly-card" in html:
                        logger.info(f"✅ Requests sucesso: HTTP {response.status_code}")
                        return html
                    else:
                        logger.warning(f"⚠️ Requests: HTTP 200 mas sem produtos (SPA/JavaScript)")
                        html_sem_produtos = True
                        break  # Sair do loop de retries e ir para Selenium
                elif response.status_code in [403, 429]:
                    logger.warning(f"❌ Bloqueado: HTTP {response.status_code}")
                    if tentativa < max_retries:
                        wait_time = retry_wait * (2 ** (tentativa - 1))  # Backoff exponencial
                        logger.warning(f"⏳ Aguardando {wait_time:.0f}s antes de retry {tentativa + 1}/{max_retries}...")
                        time.sleep(wait_time)
                    continue
                else:
                    logger.warning(f"⚠️ HTTP {response.status_code}: {url}")
                    if tentativa < max_retries:
                        wait_time = retry_wait * (2 ** (tentativa - 1))
                        logger.info(f"⏳ Aguardando {wait_time:.0f}s antes de retry {tentativa + 1}/{max_retries}...")
                        time.sleep(wait_time)
                    continue
                    
            except requests.exceptions.ProxyError as e:
                logger.warning(f"❌ Erro de proxy: {str(e)[:60]}")
                logger.warning(f"⚠️ Pulando Requests e indo direto para Selenium...")
                html_sem_produtos = True
                break  # Pula direto para Selenium
                
            except requests.exceptions.Timeout:
                logger.warning(f"⏱️ Timeout na tentativa {tentativa}")
                if tentativa == max_retries:
                    logger.warning(f"⚠️ Proxies muito lentos, pulando para Selenium...")
                    html_sem_produtos = True
                    break
                if tentativa < max_retries:
                    wait_time = retry_wait * (2 ** (tentativa - 1))
                    logger.info(f"⏳ Aguardando {wait_time:.0f}s antes de retry {tentativa + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ Erro na requisição: {str(e)[:80]}")
                if tentativa < max_retries:
                    wait_time = retry_wait * (2 ** (tentativa - 1))
                    logger.info(f"⏳ Aguardando {wait_time:.0f}s antes de retry {tentativa + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.warning(f"❌ Erro inesperado: {str(e)[:80]}")
                if tentativa < max_retries:
                    wait_time = retry_wait * (2 ** (tentativa - 1))
                    logger.info(f"⏳ Aguardando {wait_time:.0f}s antes de retry {tentativa + 1}/{max_retries}...")
                    time.sleep(wait_time)
                if tentativa < max_retries:
                    wait_time = retry_wait * (2 ** (tentativa - 1))
                    logger.info(f"⏳ Aguardando {wait_time:.0f}s antes de retry {tentativa + 1}/{max_retries}...")
                    time.sleep(wait_time)
        
        # ===== ESTRATÉGIA 3: Selenium (se habilitado e HTTP falhou ou sem produtos) =====
        if USE_HEADLESS_BROWSER and HAS_SELENIUM and html_sem_produtos:
            logger.info(f"[Estratégia 3/3] 🤖 Selenium headless browser (renderiza JavaScript)...")
            try:
                return self._fetch_with_selenium(url)
            except Exception as e:
                logger.error(f"❌ Selenium falhou: {e}")
        
        logger.error(f"❌ Todas as estratégias falharam para {url}")
        return None
    
    def _fetch_with_selenium(self, url: str) -> Optional[str]:
        """Busca conteúdo usando Selenium headless browser (último recurso)"""
        import shutil
        import time as time_module
        
        try:
            if not self.driver:
                from .config import SELENIUM_HEADLESS, USE_PROXY, PROXY_LIST, SINGLE_PROXY
                
                options = webdriver.ChromeOptions()
                
                # ===== PROXY =====
                if USE_PROXY:
                    proxy_url = None
                    if SINGLE_PROXY:
                        proxy_url = SINGLE_PROXY
                    elif PROXY_LIST:
                        proxy_url = random.choice(PROXY_LIST)
                    
                    if proxy_url:
                        # Normalizar URL de proxy
                        if not proxy_url.startswith(('http://', 'https://', 'socks5://')):
                            proxy_url = f"http://{proxy_url}"
                        
                        logger.info(f"🌐 Usando proxy: {proxy_url[:50]}...")
                        options.add_argument(f"--proxy-server={proxy_url}")
                
                # ===== ANTI-DETECÇÃO DE BOT =====
                # Desabilitar chromedriver flag
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                
                # Opcional: comentar a linha abaixo pra VER o navegador aberto
                if SELENIUM_HEADLESS:
                    options.add_argument("--headless")
                
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-web-resources")
                options.add_argument("--disable-extensions")
                options.add_argument("--lang=pt-BR")
                options.add_argument(f"user-agent={random.choice(self.config.USER_AGENTS)}")
                
                # Tenta encontrar chromedriver
                chromedriver_path = shutil.which("chromedriver")
                if not chromedriver_path:
                    # Tenta caminhos conhecidos
                    possible_paths = [
                        "/usr/bin/chromedriver",
                        "/usr/local/bin/chromedriver",
                        "/snap/bin/chromium.chromedriver"
                    ]
                    for path in possible_paths:
                        import os
                        if os.path.exists(path):
                            chromedriver_path = path
                            break
                
                if chromedriver_path:
                    logger.debug(f"Usando ChromeDriver: {chromedriver_path}")
                    self.driver = webdriver.Chrome(service=webdriver.chrome.service.Service(chromedriver_path), options=options)
                else:
                    logger.warning("ChromeDriver não encontrado, tentando sem caminho específico...")
                    self.driver = webdriver.Chrome(options=options)
                
                # Configurar timeouts
                from .config import SELENIUM_TIMEOUT, SELENIUM_IMPLICIT_WAIT
                self.driver.set_page_load_timeout(SELENIUM_TIMEOUT)
                self.driver.implicitly_wait(SELENIUM_IMPLICIT_WAIT)
                
                modo = "HEADLESS (sem janela)" if SELENIUM_HEADLESS else "COM JANELA (você pode ver!)"
                proxy_info = f" + {len(PROXY_LIST)} proxies" if USE_PROXY and PROXY_LIST else ""
                logger.info(f"✅ Selenium Chrome iniciado - {modo} (anti-bot ativado{proxy_info})")
            
            logger.info(f"🤖 Carregando com Selenium: {url}")
            
            # Primeiro, visitar a página inicial para pegar cookies/sessão
            logger.debug("🍪 Obtendo cookies de sessão...")
            self.driver.get("https://www.mercadolivre.com.br/")
            time_module.sleep(2)
            
            # Agora carregar a URL com os cookies
            self.driver.get(url)
            
            # Aguardar conteúdo carregar
            logger.debug("⏳ Aguardando body estar presente...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "body"))
            )
            
            # Aguardar e scrollar para carregar itens (scroll infinito)
            logger.debug("📜 Scrollando página para carregar itens...")
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            for i in range(5):  # Tentar scroll 5 vezes
                # Scrollar para o final
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time_module.sleep(2)  # Aguardar carregamento
                
                # Calcular nova altura
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    logger.debug(f"✓ Scroll {i+1}: sem novos itens")
                    break  # Chegou ao final
                logger.debug(f"✓ Scroll {i+1}: carregou mais ({new_height}px)")
                last_height = new_height
            
            # Aguardar itens aparecerem
            logger.debug("⏳ Aguardando produtos aparecerem...")
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "ui-search-layout__item"))
                )
                logger.debug("✓ Produtos encontrados!")
            except:
                logger.debug("⚠️ Timeout aguardando .ui-search-layout__item, continuando mesmo assim...")
            
            # Scrollar de volta para o topo para garantir que tudo está renderizado
            self.driver.execute_script("window.scrollTo(0, 0);")
            time_module.sleep(1)
            
            html = self.driver.page_source
            
            # Debug: contar quantos itens foram encontrados
            try:
                num_items = len(self.driver.find_elements(By.CLASS_NAME, "ui-search-layout__item"))
                logger.info(f"✅ Selenium sucesso ({len(html)} bytes, {num_items} itens encontrados)")
            except:
                logger.info(f"✅ Selenium sucesso ({len(html)} bytes)")
            
            return html
            
        except Exception as e:
            logger.error(f"❌ Selenium error: {type(e).__name__}: {e}")
            raise
    
    def close(self):
        """Fecha conexões e libera recursos"""
        if self.driver:
            self.driver.quit()
            logger.info("✅ Selenium Chrome fechado")
