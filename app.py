import requests
import pandas as pd
import os
from flask import Flask, render_template, request
from lxml import html



# define global paths for Image and csv folders

CSV_FOLDER = os.path.join('static', 'CSVs')

app = Flask(__name__)
# config environment variables

app.config['CSV_FOLDER'] = CSV_FOLDER

class DataCollection:
    def __init__(self):
            # dictionary to gather data
        self.data = {
        "Series": list(), 
        "UserName": list(),
        "Rating": list(), 
        "Comment": list()}
            
    def get_final_data(self,seriesName=None,username=None,rating=None,comment=None):
        '''
        this will append data gathered from comment box into data dictionary
        '''
        # append product name
        self.data["Series"].append(seriesName)
        try:
           self.data["UserName"].append(username) 
        except:
           self.data["UserName"].append('No Name') 
           
        try:
           self.data["Rating"].append(rating) 
        except:
           self.data["Rating"].append('No Rating')   
           
        try:
           self.data["Comment"].append(comment) 
        except:
           self.data["Comment"].append('No Comment')           
        

        

        
    def get_main_HTML(self, base_URL=None, search_string=None):
        search_url = f"{base_URL}/find?q={search_string}"
        request_url=requests.get(search_url)
        page=html.fromstring(request_url.content)
        return(page)

    def get_series_name_links(self,bigBoxes=[]):
        all_links=[]


        for box in bigBoxes:

                linktext='https://imdb.com'+box
                all_links.append(linktext)


        return all_links    

    def get_series_HTML(self, seriesLinks=None):
        series_page = requests.get(seriesLinks)
        series_HTML =html.fromstring(series_page.content) 
        return series_HTML

    def get_data_dict(self):
        '''
        returns collected data in dictionary
        '''

        return self.data
    
    def save_as_dataframe(self, dataframe, fileName=None):
        '''
        it saves the dictionary dataframe as csv by given filename inside
        the CSVs folder and returns the final path of saved csv
        '''
        # save the CSV file to CSVs folder
        csv_path = os.path.join(app.config['CSV_FOLDER'], fileName)
        fileExtension = '.csv'
        final_path = f"{csv_path}{fileExtension}"
        # clean previous files -
        CleanCache(directory=app.config['CSV_FOLDER'])
        # save new csv to the csv folder
        dataframe.to_csv(final_path, index=None)
        print("File saved successfully!!")
        return final_path
class CleanCache:
    '''
    this class is responsible to clear any residual csv and image files
    present due to the past searches made.
    '''
    def __init__(self, directory=None):
        self.clean_path = directory
        # only proceed if directory is not empty
        if os.listdir(self.clean_path) != list():
            # iterate over the files and remove each file
            files = os.listdir(self.clean_path)
            for fileName in files:
                print(fileName)
                os.remove(os.path.join(self.clean_path,fileName))
        print("cleaned!")
        
# route to display the home page
@app.route('/',methods=['GET'])  
def homePage():
    return render_template("index.html")

# route to display the review page
@app.route('/review', methods=("POST", "GET"))
    
def index():
    if request.method == 'POST':

            base_URL = 'https://www.imdb.com'
            
            # enter a product name eg "xiaomi"
            # search_string = input("enter a brandname or a product name: ")
            search_string = request.form['content']
            #search_string = search_string.replace(" ", "")
            get_data = DataCollection()

            imdb_HTML = get_data.get_main_HTML(base_URL, search_string)
            

            # store all the boxes containing products
            bigBoxes = imdb_HTML.xpath('//div[@class="article"]/div[2]/table/tr/td[@class="result_text"]/a/@href')
            print(bigBoxes)

            # store extracted product name links
            series_name_Links = get_data.get_series_name_links( bigBoxes)
            print(series_name_Links)


            # iterate over series HTML
            for seriesLinks in series_name_Links:
                print(seriesLinks)

                for series_HTML_page in get_data.get_series_HTML(seriesLinks):
                    comments=series_HTML_page.xpath("//div[@class='comment-meta']/following-sibling::div/p")[0].text
                    username=series_HTML_page.xpath("//div[@class='comment-meta']/a/span")[0].text
                    rating=series_HTML_page.xpath("//div[@class='ratingValue']/strong/span")[0].text
                    date=series_HTML_page.xpath('//a[@title="See more release dates"]')[0].text
                    date=date.rstrip("\n")
                    series=series_HTML_page.xpath("//div[@class='title_wrapper']/h1")[0].text
                    series_name=series+date
                    get_data.get_final_data(series_name,username, rating, comments)
                    break
       
            # save the data as gathered in dataframe
            df = pd.DataFrame(get_data.get_data_dict())
            # save dataframe as a csv which will be availble to download
            download_path = get_data.save_as_dataframe(df, fileName=search_string.replace("+", "_"))            
            return render_template('review.html', 
            tables=[df.to_html(classes='data')], # pass the df as html 
            titles=df.columns.values, # pass headers of each cols
            search_string = search_string, # pass the search string
            download_csv=download_path # pass the download path for csv
            )      
            



    else:
        # return index page if home is pressed or for the first run
        return render_template("index.html")
    
if __name__ == '__main__':
    app.run(debug=True)
    