import json
from headers import *
from requests_html import HTMLSession
import firebase_admin
from firebase_admin import db

cred = firebase_admin.credentials.Certificate('serviceAccountKey.json')
firebase_admin = firebase_admin.initialize_app(cred, {'databaseURL': 'https://python-web-scraping-419e5-default-rtdb.asia-southeast1.firebasedatabase.app/'})

ref = db.reference("/Products")

class Scraper():
    
    def __init__(self, page_limit = 0):
        self.s = HTMLSession()
        self.product_urls = []
        self.proxies = {
            'http://113.176.81.31:55443',
        }
        self.url = 'https://bellarose.pl/sklep/'
        self.next_url = ''
        self.scraped_data = {}
        self.page_limit = page_limit
        self.loop_counter = 1 #exclude page 1
        self.current_page = 1
    
    def scrape_data(self):
        print('-----Start Checking If Connective is Alive-----')
        request = self._check_request_w_headers_and_cookies(self.url)
        request.html.render()
    
        if request != False:
            raw_urls = request.html.absolute_links  
            self.next_url = self.url + 'page/' + str(self.loop_counter + 1)
            self._filter_product_url(raw_urls, '/product/')
        
        print('-----Loop Scraping on Elements-----')
        for x, product_url in enumerate(self.product_urls):
            r = self._check_request_w_headers_and_cookies(product_url)
            if r != False:
                # Render html when elements and text are loaded by javascsript
                r.html.render(timeout = 20)

                title = r.html.find('div.summary.entry-summary.col-md-6 > h2.product_title.entry-title')[0].text.strip()
                image_element = r.html.find('div.img-thumbnail > div.inner > img')
                image_url = image_element[0].attrs['src']
                description = r.html.find('div.description.woocommerce-product-details__short-description')[0].text.strip()
                price = r.html.find('p.price')[0].text.strip()
                availability = r.html.find('div.product_meta > span.product-stock')[0].text.strip()

                delivery_time = ''
                
                # Add to dictionary
                self.scraped_data['Product' + str(x+1)] = {'product_url': product_url, 'title': title, 'description': description, 'price': price, 'availability': availability, 'image_url': image_url}
                print('-----Done Adding into Dictionary-----')
    
            else:
                print(r)

        if self.page_limit != 0:
            self.loop_counter += 1
            while self.loop_counter <= self.page_limit:
                print('-----Start scraping to page-----' + str(self.loop_counter))
                self.url = self.next_url
                self.scrape_data()
                self.current_page += 1
            
        return self.scraped_data

    def _check_proxy(self, url):
        # Iterate the proxies and check if it is working
        for proxy in self.proxies:
            try:
                request = self.s.get(url, proxies = {'http': proxy, 'https': proxy})
                # if proxy is alive do scrape
                if request.status_code == 200:
                    return proxy
                    break
            except OSError as e:
                print(e)
                return False
    
    def _check_request_w_headers_and_cookies(self, url):
        # Get a proxy IP
        # proxy = self._check_proxy(url)
        # if proxy != False:
        try:
            request = self.s.get(url, headers = headers)
            # if proxy is alive do scrape
            if request.status_code == 200:
                return request
        except OSError as e:
            print(e)
            return False

    def _filter_product_url(self, urls, condition):
        for url in urls:
            if condition in url:
                self.product_urls.append(url)

    def save_as_json_file(self, records):
        # save as json file for backup
        with open("products.json", "w") as fp:
            json.dump(records, fp, indent = 4) 

    def store_to_firebase(self):
        #Save to to firebase
        print('-----Storing to Firebase-----')
        with open("products.json", "r") as f:
            file_contents = json.load(f)
        ref.set(file_contents)

def main():
    scraper = Scraper(1)
    records = scraper.scrape_data()
    scraper.save_as_json_file(records)
    scraper.store_to_firebase()

main()

        



