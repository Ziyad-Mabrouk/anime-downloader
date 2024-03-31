from flask import Flask, render_template, request, jsonify
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

class WebDriverContextManager:
    def __enter__(self):
        # Path to the Brave executable
        brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

        # Path to the downloaded Chrome WebDriver
        webdriver_path = './chromedriver.exe'

        # Set up download preferences
        prefs = {
            "download.default_directory": r"C:\Users\Ziyad Mabrouk\Videos\Anime\Black Clover",
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }

        # Set up Brave options
        options = webdriver.ChromeOptions()
        options.binary_location = brave_path
        options.add_experimental_option("prefs", prefs)
        options.add_argument('--headless')  # Run in headless mode

        # Set up the Chrome service
        service = Service(webdriver_path)

        # Return a new WebDriver instance
        return webdriver.Chrome(service=service, options=options)

    def __exit__(self, exc_type, exc_value, traceback):
        pass


def is_episode_downloaded(expected_filename):
    download_directory = r"C:\Users\Ziyad Mabrouk\Videos\Anime\Black Clover"
    return os.path.exists(os.path.join(download_directory, expected_filename))

def get_first_letter(anime_name): return anime_name[0]

def download_episode(anime_name, episode_number, quality):
    print(get_first_letter(anime_name))
    try:
      with WebDriverContextManager() as driver:
        driver.get('https://animepahe.ru/anime')

        # Wait for 'B' link and click it
        element_xpath = f"//a[@class='nav-link' and contains(text(), '{get_first_letter(anime_name)}')]"
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, element_xpath))
        )
        element.click()

        # Wait for anime name link and click it
        element_xpath = f"//a[contains(text(), '{anime_name}')]"
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, element_xpath))
        )
        element.click()

        # Click the first episode
        element_xpath = "//a[@class='play' and contains(text(), 'Watch  - 1 Online')]"
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, element_xpath))
        )
        element.click()

        # Click the desired episode number
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'episodeMenu'))
        )
        button.click()

        if (episode_number != 1):
            element_xpath = f"//a[@class='dropdown-item' and contains(text(), 'Episode {episode_number}')]"
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, element_xpath))
            )
            element.click()

        # Click the download button
        element_xpath = "//a[@id='downloadMenu']"
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, element_xpath))
        )
        element.click()

        # Click the desired download quality
        download_xpath = f"//a[@class='dropdown-item' and contains(text(), '{quality}')]"
        download_element = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, download_xpath))
        )
        href_value = download_element.get_attribute("href")

        # Download the episode
        driver.get(href_value)

        # Click the download button
        element_xpath = "//a[@class='btn btn-secondary btn-block redirect' and contains(text(), 'Continue')]"
        element = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, element_xpath))
        )
        
        driver.get(element.get_attribute("href"))

        # Find the element containing the filename
        filename_element_xpath = "//h1[@class='title']"
        filename_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, filename_element_xpath))
        )
        expected_name = filename_element.text.strip()

        # Locate the element containing form data
        form_element_xpath = "//form"
        form_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, form_element_xpath))
        )
        form_html = form_element.get_attribute("outerHTML")

        # Parse form data using BeautifulSoup
        soup = BeautifulSoup(form_html, 'html.parser')
        form_action = soup.find('form').get('action')
        form_method = soup.find('form').get('method')
        token_value = soup.find('input', {'name': '_token'}).get('value')

        # Execute the POST request
        js_script = f'''
            var form = document.createElement('form');
            form.method = '{form_method}';
            form.action = '{form_action}';

            var token = document.createElement('input');
            token.setAttribute('type', 'hidden');
            token.setAttribute('name', '_token');
            token.setAttribute('value', '{token_value}');
            form.appendChild(token);

            document.body.appendChild(form);
            form.submit();
        '''
        driver.execute_script(js_script)
        #print(f"Downloading episode {episode_number}...")

        # Wait if the download is complete
        while not is_episode_downloaded(expected_name):
            time.sleep(1)  # Wait for 1 second before checking again

        #print(f"\nEpisode {episode_number} fully downloaded\n")
        driver.quit()  # Close the browser instance


    except Exception as e:
        print(f"Exception occurred: {str(e)}")

    pass 


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    anime_name = request.form.get('anime-name')
    quality = request.form.get('quality')
    start_episode = int(request.form.get('start-episode'))
    end_episode = int(request.form.get('end-episode'))
    try:
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit each download task to the thread pool
            futures = [executor.submit(download_episode, anime_name, episode_number, quality) for episode_number in range(start_episode, end_episode + 1)]

        response_data = {'success': True, 'message': 'Working on it...'}
        return jsonify(response_data)

    except Exception as e:
        response_data = {'success': False, 'message': f'Download failed. Error: {str(e)}'}
        return jsonify(response_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)