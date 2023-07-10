from selenium import webdriver
from bs4 import BeautifulSoup
import time
import numpy as np
import pandas as pd
import re
from tqdm import tqdm_notebook as tqdmn
from datetime import datetime
from time import strftime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

start_time = time.time()


def opening_web(web,path,wait_time):
    """ Open a webpage using selenium ChromeDriver

    We'll be using this function to open webpages that we want to collect data from

    Args:
        web (str): An url adress. This is the web page will be opening
        path (str): The path to the chromedriver used to open the webpage
        wait_time (int): The amount of time to wait after opening the webpage.
                        This is used to let enough time to load the webpage
    
    Returns :
        driver : A webpage open with selenium
    """
    #options = webdriver.ChromeOptions()
    #options.add_argument('--ignore-certificate-errors')
    #options.add_argument('--incognito')
    #options.add_argument('--headless')

    driver = webdriver.Chrome(executable_path = path) #, options=options)
    driver.get(web)
    time.sleep(wait_time+2)
    return(driver)

def scroll_to_load_more_ad(driver,scroll_pause_time):
    """ Scroll through a webpage

    We'll be using this function to scroll down a webpage and load more data.
    This will stop once the size of the scroll height will be different from what it was when starting
    scrolling, meaning that more data has been loaded.

    Args:
        driver : a driver object, return from webdriver.Chrome
        scroll_pause_time (int): The amount of time to wait after scrolling the page
    """
    screen_height = driver.execute_script("return window.screen.height;")
    i = 1
    init_scroll_height = driver.execute_script("return document.body.scrollHeight;")
    while True:
        # scroll one screen height each time
        driver.execute_script("window.scrollTo(0, {screen_height}*{i});".format(screen_height=screen_height, i=i))  
        i += 1
        time.sleep(scroll_pause_time)
        # update scroll height each time after scrolled, as the scroll height can change after we scrolled the page
        new_scroll_height = driver.execute_script("return document.body.scrollHeight;")  
        # Break the loop when the height we need to scroll to is larger than the total scroll height
        if ((screen_height) * i > new_scroll_height) | (init_scroll_height != new_scroll_height):
            break


def get_all_ads(listing_balise,ads_balise,driver):
    """ Find all ads in the webpage

    We'll be using this function to find all ads available on the webpage in order to click on each
    one of them.

    Args:
        listing_balise (str) : html balise used to find the "block" of ads we are looking to collect
                               a "block" correspond to the last block of ads loaded while itering through
                               the webpage
        ads_balise (str) : html balise used to find each ads links inside the "block"
        driver : a driver object, return from webdriver.Chrome
    
    Return:
        all_ads (list) : a list of link to open all ads available
    """
    # find the last listing loaded
    listing = driver.find_elements_by_css_selector(listing_balise)
    
    # Get all ads from the last listing available
    
    all_ads = listing[-1].find_elements_by_css_selector(ads_balise)
    time.sleep(1)
    
    return(all_ads)

def extract_number(list_of_text,keyword,item_to_grab):
    """ Extract a specific pattern from a string

    We'll be using this function to extract number from list of string

    Examples:
        extract_number("9 pièces";"[0-9 ]* pièce(s)";0)
        returns : "9"

    Args:
        list_of_text (str) : a list that only contains string
        keyword (str) : Regex expression
        item_to_grab : Which item to return from the match pattern when split
    
    Return:
        list_init (list) : a list that return extracted pattern for each element

    Exceptions:
        if an element in the list is empty we do not try to match pattern and simply append
        a missing value
    """
    list_init = []
    for text in list_of_text:
        try:
            if re.search(keyword,text):
                list_init.append(re.search(keyword,text).group().split()[item_to_grab])
            else:
                list_init.append(np.nan)
        except:
            list_init.append(np.nan)
    return(list_init)


def web_scrapper(driver,nb_of_scroll=range(0,20)):

    # Initialize empty list to fill with the scraped data
    title = []
    price = []
    localisation = []
    item = []
    #ref=[]
    descriptif = []
    #contact = []
    ad_url = []

    # Close the cookies pop-up

    try:
        driver.find_element_by_css_selector('.sd-cmp-16t61.sd-cmp-2JYyd.sd-cmp-3cRQ2').click()
    except:
        None

    # This loop is based on the number of "scroll" we want to perform in order to load more data
    for nb_scroll in nb_of_scroll:
        all_ads = get_all_ads(listing_balise = '.row.row-large-gutters.page-item',ads_balise = '.item-body [href]',driver=driver)
        j = 0
        all_ads_it = all_ads
        # This loop goes through each ad to click on it and collect the data
        for ad in all_ads:
            driver.get(all_ads_it[j].get_attribute('href'))
            try:
                driver.find_element_by_css_selector('.sd-cmp-16t61.sd-cmp-2JYyd.sd-cmp-3cRQ2').click()
            except:
                None
            page_source = driver.page_source
            soup = BeautifulSoup(page_source,'lxml')
        
            # This is where we try to collect data from the ad
        
            try:
                title.append(soup.find('h1', class_='item-title').get_text().replace('\n','').replace('\t','').replace('\xa0','').replace('.',''))
            except:
                title.append(np.nan)
        
            try:
                price.append(soup.find('span',class_='item-price').get_text().replace('\xa0','').replace('.',''))
            except:
                price.append(np.nan)
        
            #try:
             #   ref.append(soup.find('p', class_='item-date').get_text())
            #except:
             #   ref.append(np.nan)
        
            try:
                localisation.append(soup.find('h2',class_='margin-bottom-8').get_text())
            except:
                localisation.append(np.nan)
        
            try:
                item.append(' '.join(soup.find('ul',class_="item-tags margin-bottom-20").get_text().replace('\n',' ').strip().split()))
            except:
                item.append(np.nan)
        
            try:
                descriptif.append(' '.join(soup.find('div',class_="margin-bottom-30").get_text().replace('\n',' ').replace('\xa0','').strip().split()))
            except:
                descriptif.append(np.nan)
        
            #try:
             #   contact.append(soup.find('span',class_="txt-indigo").get_text())
            #except:
             #   contact.append(np.nan)
            
            ad_url.append(driver.current_url)

            # After collecting data, we wait a bit and hit the "return" button to go back
            # to the page with all the ads on it

            time.sleep(1)
            driver.execute_script("window.history.back();")
            time.sleep(2)
            all_ads_it = get_all_ads(listing_balise = '.row.row-large-gutters.page-item',ads_balise = '.item-body [href]',driver=driver)
            j = j +1

        # We scroll here until more data are loaded 

        scroll_to_load_more_ad(driver = driver,scroll_pause_time = 2)

    # We close the webpage after the amount of scroll has been reached    
    driver.quit()

    # We then clean a bit our data

    room = extract_number(item,"[0-9 ]* pièce(s)",0)
    bedroom = extract_number(item,"[0-9 ]* chambre(s)",0)
    surface = extract_number(item,"[0-9 ]* m²",0)
    terrain = extract_number(item,"Terrain [0-9 ]* m²",1)

    # We put all the list collected into a dataframe and return it
    data = pd.DataFrame(list(zip(title,price,localisation,item,room,bedroom,surface,terrain,descriptif)),#ref,contact
               columns =["Title","Price","Localisation","Items","Room","Bedroom","Area","Field_Area","Description"])
    data['source'] = "PAP"
    data['date_of_extraction'] = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    return(data)

# Adding a cleaning step

def clean_data(data,city):
    #data = data.dropna(subset = ['Contact'])
    if (city!=[]):
        data = data[data['Localisation'].isin(city)]
    data = data.drop_duplicates()
    return(data)



def send_mail(sender,password,receiver,host_add,host_port,file_to_attached):

    """ Send an e-mail

    We'll be using this function to automaticaly send an e-mail with a file attached.

    Args:
        sender : The mail address to connect to
        password : the password to connect to the sender email
        receiver : The mail address to send the email to
        host_add : Outgoing mail server name
        host_port : The port number your incoming mail server uses
        file_to_attached : the file to attached to the message
    """

    # Connection with the server
    server = smtplib.SMTP(host=host_add, port = host_port)
    server.starttls()
    server.login(sender,password)

    # Creation of the MIMEMultipart Object
    message = MIMEMultipart()   

    # Setup of MIMEMultipart Object Header
    message['From'] = sender
    message['To'] = receiver
    message['Subject'] = "Automated Email"

    # Creation of a MIMEText Part
    textPart = MIMEText("Hello, \n\nYou'll find attached the data. \n\nBest Regards, \n\nSteven","plain")

    # Creation of a MIMEApplication Part
    filename = file_to_attached
    filePart = MIMEApplication(open(filename,"rb").read(),Name = filename)
    filePart["Content-Disposition"] = 'attachment; filename="%s"' %filename

    # Part attachment   
    message.attach(textPart)
    message.attach(filePart)
   
    # Send Email and close connection
    server.send_message(message)
    server.quit()




