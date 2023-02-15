from selenium import webdriver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options 

from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os

from time import sleep

from cerebro.brain import inteligenciaIA
import datetime


# exemplo
# key_api = "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__ERWQSA"
print("Enter your Key:")
key_api = input()

def converter(texto):
    if ':' in texto:
        return texto.replace(':', '.')
    return None

def check_text(text):
    
    return text.lstrip().split()[0].upper()
    print(len(text.split()[0]))
    print(text.lstrip()[len(text.split()[0]):].lstrip())


class whatsapps:
    def __init__(self) -> None:

        chrome_options = Options()
        dir_path = os.getcwd()
        profile = os.path.join(dir_path, "profile", "bet365")

        chrome_options.add_argument(r"user-data-dir={}".format(profile))

        d = DesiredCapabilities.CHROME
        d['loggingPrefs'] = { 'browser':'ALL' }

        self.driver = webdriver.Chrome(f'{os.path.dirname(__file__)}\\driver\\chromedriver.exe', chrome_options=chrome_options, desired_capabilities=d)

        self.dicionario = {}


    def site(self, url='https://web.whatsapp.com/'):
        self.driver.get(url)


    def conversas(self):
        
        self.site()
        while True:
            msg = ""
            try:
                conversas = self.driver.find_element(By.CSS_SELECTOR, "div[aria-label='Lista de conversas']")
                break
            except:
                pass

        while True:
            conteiner = conversas.find_elements(By.CSS_SELECTOR,"div[class='g0rxnol2']")

            for text in conteiner:
                try:
                    try:
                        grupo = text.find_element(By.CSS_SELECTOR, "div[class='_21S-L']").find_element(By.CSS_SELECTOR, "span[dir='auto']").get_attribute('innerHTML')
                    except:
                        grupo = None

                    try:
                        time_ = text.find_element(By.CSS_SELECTOR, "div[aria-colindex='2']").find_element(By.CSS_SELECTOR, "div[class='Dvjym']").get_attribute('innerHTML')
                    except:
                        time_ = None

                    try:
                        nome = text.find_element(By.CSS_SELECTOR, "div[class='vQ0w7']").find_element(By.CSS_SELECTOR, "span[dir='auto']").get_attribute('innerHTML')
                    except:
                        nome = None
                        pass

                    try:
                        texto = text.find_element(By.CSS_SELECTOR, "div[class='vQ0w7']").find_element(By.CSS_SELECTOR, "span[dir='ltr']").get_attribute('innerHTML')
                    except:
                        texto = None


                    if texto[len(check_text(texto)):] != "":
                        current_time = datetime.datetime.now().strftime("%H.%M")
                        t__ = converter(time_)
                        if str(check_text(texto)) == '/BOT'.upper()  and t__ != None:
                            
                            if  float(current_time) <= float(t__)  :

                                print()
                                print('grupo-',grupo)            
                                print('time-',time_)            
                                print('nome-',nome)
                                print('texto-', texto[len(check_text(texto)):])
                                
                                sleep(1)
                                text.click()
                                sleep(1)
                                msg_box = self.driver.find_element(By.XPATH, '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div/p')


                                msg = inteligenciaIA(texto[len(check_text(texto)):], key_api )
                                msg_box.send_keys(msg)
                                sleep(1)
                                msg_box = self.driver.find_element(By.XPATH, '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[1]').send_keys(Keys.ENTER)


                            print('Resposta-',msg.lstrip())

                except KeyboardInterrupt:
                    self.driver.close()
                    break

                except:
                    pass

if __name__ == "__main__":
    w = whatsapps()
    w.conversas()


