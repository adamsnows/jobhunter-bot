"""
LinkedIn Job Scraper
Busca automática de vagas no LinkedIn usando Selenium
"""

import time
import random
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc

from .base_scraper import BaseScraper
from ..models.job import Job

logger = logging.getLogger(__name__)

class LinkedInScraper(BaseScraper):
    """Scraper específico para LinkedIn"""

    def __init__(self, email: str, password: str, headless: bool = True):
        super().__init__()
        self.email = email
        self.password = password
        self.headless = headless
        self.driver = None
        self.is_logged_in = False
        self.base_url = "https://www.linkedin.com"

        # Configurações de busca
        self.max_jobs_per_search = 100
        self.delay_between_requests = (2, 5)  # segundos

    def setup_driver(self) -> None:
        """Configura o driver do Chrome com opções otimizadas"""
        try:
            options = uc.ChromeOptions()

            if self.headless:
                options.add_argument('--headless')

            # Opções para evitar detecção
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--disable-extensions")
            options.add_argument("--profile-directory=Default")
            options.add_argument("--incognito")
            options.add_argument("--disable-plugins-discovery")
            options.add_argument("--start-maximized")

            # User agent personalizado
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

            self.driver = uc.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logger.info("✅ Chrome driver configurado com sucesso")

        except Exception as e:
            logger.error(f"❌ Erro ao configurar driver: {str(e)}")
            raise

    def login(self) -> bool:
        """Faz login no LinkedIn"""
        try:
            if not self.driver:
                self.setup_driver()

            logger.info("🔐 Fazendo login no LinkedIn...")

            # Vai para página de login
            self.driver.get(f"{self.base_url}/login")
            time.sleep(random.uniform(2, 4))

            # Preenche email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.clear()
            self._type_like_human(email_field, self.email)

            # Preenche senha
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            self._type_like_human(password_field, self.password)

            # Clica no botão de login
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()

            time.sleep(random.uniform(3, 6))

            # Verifica se o login foi bem-sucedido
            if "/feed" in self.driver.current_url or "/in/" in self.driver.current_url:
                self.is_logged_in = True
                logger.info("✅ Login realizado com sucesso!")
                return True
            else:
                logger.error("❌ Falha no login - verificar credenciais")
                return False

        except Exception as e:
            logger.error(f"❌ Erro durante login: {str(e)}")
            return False

    def search_jobs(self, keywords: List[str], location: str = "",
                   experience_level: str = "", job_type: str = "") -> List[Job]:
        """
        Busca vagas no LinkedIn

        Args:
            keywords: Lista de palavras-chave para busca
            location: Localização (ex: "São Paulo, Brazil")
            experience_level: Nível de experiência (entry, associate, mid, senior, executive)
            job_type: Tipo de vaga (full-time, part-time, contract, etc.)
        """
        if not self.is_logged_in:
            if not self.login():
                return []

        all_jobs = []

        for keyword in keywords:
            logger.info(f"🔍 Buscando vagas para: {keyword}")

            try:
                jobs = self._search_keyword(keyword, location, experience_level, job_type)
                all_jobs.extend(jobs)

                # Delay entre buscas
                time.sleep(random.uniform(*self.delay_between_requests))

            except Exception as e:
                logger.error(f"❌ Erro na busca por '{keyword}': {str(e)}")
                continue

        # Remove duplicatas baseado na URL
        unique_jobs = []
        seen_urls = set()

        for job in all_jobs:
            if job.url not in seen_urls:
                unique_jobs.append(job)
                seen_urls.add(job.url)

        logger.info(f"✅ Total de {len(unique_jobs)} vagas únicas encontradas")
        return unique_jobs

    def _search_keyword(self, keyword: str, location: str,
                       experience_level: str, job_type: str) -> List[Job]:
        """Busca vagas para uma palavra-chave específica"""
        try:
            # Constrói URL de busca
            search_url = self._build_search_url(keyword, location, experience_level, job_type)

            self.driver.get(search_url)
            time.sleep(random.uniform(3, 5))

            jobs = []
            page = 1

            while len(jobs) < self.max_jobs_per_search and page <= 10:
                logger.info(f"📄 Processando página {page} para '{keyword}'")

                # Espera carregar a lista de vagas
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search__results-list"))
                    )
                except TimeoutException:
                    logger.warning("⚠️ Timeout aguardando lista de vagas")
                    break

                # Extrai vagas da página atual
                page_jobs = self._extract_jobs_from_page()
                jobs.extend(page_jobs)

                # Tenta ir para próxima página
                if not self._go_to_next_page():
                    break

                page += 1
                time.sleep(random.uniform(2, 4))

            return jobs[:self.max_jobs_per_search]

        except Exception as e:
            logger.error(f"❌ Erro na busca por palavra-chave '{keyword}': {str(e)}")
            return []

    def _build_search_url(self, keyword: str, location: str,
                         experience_level: str, job_type: str) -> str:
        """Constrói URL de busca do LinkedIn"""
        base_jobs_url = f"{self.base_url}/jobs/search/"

        params = []
        params.append(f"keywords={keyword.replace(' ', '%20')}")

        if location:
            params.append(f"location={location.replace(' ', '%20')}")

        # Filtros adicionais
        filters = []

        if experience_level:
            level_mapping = {
                'entry': '1',
                'associate': '2',
                'mid': '3',
                'senior': '4',
                'executive': '5'
            }
            if experience_level in level_mapping:
                filters.append(f"f_E={level_mapping[experience_level]}")

        if job_type:
            type_mapping = {
                'full-time': 'F',
                'part-time': 'P',
                'contract': 'C',
                'temporary': 'T',
                'internship': 'I'
            }
            if job_type in type_mapping:
                filters.append(f"f_JT={type_mapping[job_type]}")

        # Adiciona filtro para vagas recentes (última semana)
        filters.append("f_TPR=r604800")

        if filters:
            params.extend(filters)

        return f"{base_jobs_url}?{'&'.join(params)}"

    def _extract_jobs_from_page(self) -> List[Job]:
        """Extrai informações das vagas da página atual"""
        jobs = []

        try:
            # Encontra todos os cards de vaga
            job_cards = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".jobs-search__results-list .result-card"
            )

            if not job_cards:
                # Tenta seletor alternativo
                job_cards = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".jobs-search__results-list .job-result-card"
                )

            logger.info(f"📋 Encontrados {len(job_cards)} cards de vaga na página")

            for card in job_cards:
                try:
                    job = self._extract_job_from_card(card)
                    if job:
                        jobs.append(job)

                except Exception as e:
                    logger.warning(f"⚠️ Erro ao extrair vaga: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"❌ Erro ao extrair vagas da página: {str(e)}")

        return jobs

    def _extract_job_from_card(self, card) -> Optional[Job]:
        """Extrai informações de uma vaga específica"""
        try:
            # Título da vaga
            title_element = card.find_element(By.CSS_SELECTOR, "h3 a")
            title = title_element.text.strip()
            url = title_element.get_attribute("href")

            # Empresa
            try:
                company_element = card.find_element(By.CSS_SELECTOR, ".result-card__subtitle a")
                company = company_element.text.strip()
            except NoSuchElementException:
                company_element = card.find_element(By.CSS_SELECTOR, ".result-card__subtitle")
                company = company_element.text.strip()

            # Localização
            try:
                location_element = card.find_element(By.CSS_SELECTOR, ".job-result-card__location")
                location = location_element.text.strip()
            except NoSuchElementException:
                location = "Não especificado"

            # Data de postagem
            try:
                date_element = card.find_element(By.CSS_SELECTOR, ".result-card__listdate")
                posted_date = date_element.text.strip()
            except NoSuchElementException:
                posted_date = "Recente"

            # Limpa a URL (remove parâmetros de tracking)
            clean_url = url.split('?')[0] if '?' in url else url

            # Cria objeto Job
            job = Job(
                title=title,
                company=company,
                location=location,
                url=clean_url,
                source="LinkedIn",
                posted_date=posted_date,
                created_at=datetime.now()
            )

            return job

        except Exception as e:
            logger.warning(f"⚠️ Erro ao extrair informações da vaga: {str(e)}")
            return None

    def _go_to_next_page(self) -> bool:
        """Tenta navegar para a próxima página"""
        try:
            # Procura botão "Próxima"
            next_buttons = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button[aria-label*='próxima'], button[aria-label*='next']"
            )

            if not next_buttons:
                # Tenta seletor alternativo
                next_buttons = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".artdeco-pagination__button--next"
                )

            for button in next_buttons:
                if button.is_enabled():
                    self.driver.execute_script("arguments[0].click();", button)
                    time.sleep(random.uniform(2, 4))
                    return True

            return False

        except Exception as e:
            logger.warning(f"⚠️ Erro ao navegar para próxima página: {str(e)}")
            return False

    def _type_like_human(self, element, text: str) -> None:
        """Digita texto simulando comportamento humano"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

    def get_job_details(self, job_url: str) -> Dict:
        """Obtém detalhes completos de uma vaga específica"""
        try:
            self.driver.get(job_url)
            time.sleep(random.uniform(3, 5))

            details = {}

            # Descrição da vaga
            try:
                description_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".description__text"))
                )
                details['description'] = description_element.text.strip()
            except TimeoutException:
                details['description'] = "Descrição não disponível"

            # Critérios/requisitos
            try:
                criteria_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".job-criteria__list .job-criteria__item"
                )
                criteria = {}
                for element in criteria_elements:
                    key = element.find_element(By.CSS_SELECTOR, ".job-criteria__subheader").text.strip()
                    value = element.find_element(By.CSS_SELECTOR, ".job-criteria__text").text.strip()
                    criteria[key] = value
                details['criteria'] = criteria
            except NoSuchElementException:
                details['criteria'] = {}

            # Salário (se disponível)
            try:
                salary_element = self.driver.find_element(
                    By.CSS_SELECTOR,
                    ".salary, .compensation__salary"
                )
                details['salary'] = salary_element.text.strip()
            except NoSuchElementException:
                details['salary'] = None

            return details

        except Exception as e:
            logger.error(f"❌ Erro ao obter detalhes da vaga: {str(e)}")
            return {}

    def close(self) -> None:
        """Fecha o driver"""
        if self.driver:
            self.driver.quit()
            logger.info("🔒 Driver fechado")

    def __del__(self):
        """Destructor para garantir que o driver seja fechado"""
        self.close()
