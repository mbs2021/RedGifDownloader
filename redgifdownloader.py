import os
import pygubu
import configparser
import wordninja
import requests
from configparser import ConfigParser
from tkinter import messagebox
from tkinter import filedialog


PROJECT_PATH = os.path.dirname(__file__)
PROJECT_UI = os.path.join(PROJECT_PATH, "windows.ui")
wordninja.DEFAULT_LANGUAGE_MODEL = wordninja.LanguageModel(PROJECT_PATH+'\wordninja_words.txt.gz')
folder = 0
data = 0

def configLoader():
    global folder
    config_object = ConfigParser()
    config_object.read('cfg.ini')
    route = config_object['ROUTE']
    folder = route["save_directory"]

def configCreator():
    config_object = ConfigParser()
    config_object["ROUTE"] = {"save_directory":folder}
    with open(PROJECT_PATH+'/cfg.ini', 'w') as config:
        config_object.write(config);

def configRewrite(folder):
    config_object = ConfigParser()
    config_object.read("cfg.ini")
    route = config_object["ROUTE"]
    route["save_directory"] = folder
    with open(PROJECT_PATH+'/cfg.ini', 'w') as config:
        config_object.write(config);

def convertSize(size):
    return str(round((size/1024000),2))+' MB'

def populateTable(data, tree, window):
    count = 0
    tree.delete(*tree.get_children())
    tree['columns'] = ('id','name', 'size', 'status')
    tree.column('id', width='35')
    tree.heading('id', text='#', anchor='center')
    tree.column('name', width='300' , anchor='center')
    tree.heading('name', text='Name')
    tree.column('size', width='120' , anchor='center')
    tree.heading('size', text='File size')
    tree.column('status', width='140' , anchor='center')
    tree.heading('status', text='Status')
    for x in data:
        if x.find('redgifs.com/') != -1:
            if x.find('/watch/') != -1:
                file = x.split('/watch/')
                file = "".join([file[index] for index in [1]])
            else:
                file = x.split('.com/')
                file = "".join([file[index] for index in [1]])
            if x.find('.webm') != -1 or x.find('.mp4') != -1:
                file = file.split('.')
                file = "".join([file[index] for index in [0]])
        else:
            file = x
        if file:
            count+=1
            words = wordninja.split(file)
            try: 
                if words.index("mobile") != 1:
                    index = words.index("mobile")
                    words[index] = "-mobile"
            except ValueError:
                print("")
            for x in range(3):
                words[x] = words[x].capitalize()
            file="".join(words)
            url = 'https://thumbs2.redgifs.com/'+file+'.mp4'
            r = requests.get(url, stream=True)
            total_length = int(r.headers.get('content-length'))
            tree.insert('', 'end', iid=count, values=(count,file,convertSize(total_length),'Pending'))
            tree.yview(count-2)
            window.update()
            
            

class RedGifsDownloader:
    
    def __init__(self):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        self.mainwindow = builder.get_object('toplevel')
        builder.connect_callbacks(self)
        if os.path.isfile(PROJECT_PATH+'/cfg.ini'):
            configLoader()
            text = builder.get_variable('lbl_foldervar')
            text.set('Current folder: ' + folder)
        else:
            configCreator()
        
    def getDirectory(self):
        folder = filedialog.askdirectory()
        if folder != "":
            text = self.builder.get_variable('lbl_foldervar')
            text.set('Current file: ' + folder)
            configRewrite(folder)

    def openFile(self):
        global data, data2
        filename = filedialog.askopenfilename(filetypes=[("Text files","*.txt")])
        if filename != "":
            text = self.builder.get_variable('lbl_filevar')
            text.set('Current file: ' + filename)
            with open (filename, "r") as myfile:
                data=myfile.read().split('\n')
            data2 = data
            populateTable(data, self.builder.get_object('tv_files'), self.builder.get_object('toplevel'))

    def downloadFiles(self):
        global data, data2
        count = 0
        window = self.builder.get_object('toplevel')
        tree = self.builder.get_object('tv_files')
        if data != 0 and folder != 0:
            bar = self.builder.get_object('pb_download')
            for x in data:
                if x.find('redgifs.com/') != -1:
                    if x.find('/watch/') != -1:
                        file = x.split('/watch/')
                        file = "".join([file[index] for index in [1]])
                    else:
                        file = x.split('.com/')
                        file = "".join([file[index] for index in [1]])
                    if x.find('.webm') != -1 or x.find('.mp4') != -1:
                        file = file.split('.')
                        file = "".join([file[index] for index in [0]])
                else:
                    file = x
                total_length = 0
                bar['value'] = 0
                count+=1
                if file:
                    words = wordninja.split(file)
                    try: 
                        if words.index("mobile") != 1:
                            index = words.index("mobile")
                            words[index] = "-mobile"
                    except ValueError:
                        print("")
                    for x in range(3):
                        words[x] = words[x].capitalize()
                    file="".join(words)
                    url = 'https://thumbs2.redgifs.com/'+file+'.mp4'
                    r = requests.get(url, stream=True)
                    total_length = int(r.headers.get('content-length'))
                    tree.item(count, values=(count,file,convertSize(total_length),'Downloading'))
                    tree.yview(count-1)
                    with open(folder +'/'+ file+'.mp4', 'wb') as f:
                        bar["maximum"] = total_length
                        for chunk in r.iter_content(chunk_size=1024):
                            if chunk:
                                bar.step(1024)
                                window.update()
                                f.write(chunk)
                                f.flush()
                else:
                    print("");
                tree.item(count, values=(count,file,convertSize(total_length),'Completed'))
            bar['maximum'] = 100
            bar['value'] = 100
            messagebox.showinfo('RedGifs Downloader',"Finished");
            data = data2
        else:
            if data == 0 and folder != 0:
                messagebox.showinfo('RedGifs Downloader',"Please select a file with the names")
            elif data != 0 and folder == 0:
                messagebox.showinfo('RedGifs Downloader',"Please select a folder")
            else:
                messagebox.showinfo('RedGifs Downloader',"Please select a file with the names and a folder")

    def run(self):
        self.mainwindow.mainloop()

if __name__ == '__main__':
    app = RedGifsDownloader()
    app.run()

