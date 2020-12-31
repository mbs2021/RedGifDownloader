# RedGifDownloader
Repository of RedGif Downloader, there isn't much to explain<br/>
Usage:<br/>
Create a text file (.txt) and paste the urls or video code, one by line.<br/>
Inside the program select a directory to save (it is saved so you don't have to assign a folder every time you open the software)<br/>
Select the text file with the urls.<br/>
Press the download button.
____________________________________________________________

In case you are using the source instead of the binaries (which will be posted when compiled hopepefully)
you'll these libraries:

os<br/>
(included in python)<br /><br />
Tkinter<br />
(included in python)<br /><br />
ConfigParser<br />
(included in python)<br /><br />
Pygubu<br />
(https://github.com/alejandroautalan/pygubu / https://pypi.org/project/pygubu/)<br /><br />
Wordninja<br /> 
(https://pypi.org/project/wordninja/ / https://github.com/keredson/wordninja)<br /><br />
Requests<br />
(https://pypi.org/project/requests/ / https://github.com/psf/requests)<br /><br />


also it was built using Python 3.8.7 and Pygubu Designer (https://github.com/alejandroautalan/pygubu-designer / https://pypi.org/project/pygubu-designer/)

______________________________________________________________

Some explanations about the functionality and some things i'll try to implement.<br/>
At the moment its a very basic download software, the basic functionality is complete but some links may not work because of the way the page saves them, in that case, just edit the file inside wordninja.txt.gz and add that word, or contact me to upload it.<br/>

Also some functions i'll try to implement or create:<br/>
*Pause and Continue a download.<br/>
*Option to insert links directly instead of using a text file.<br/>
*A more optimized command line app without GUI (the original code was accidentally deleted 7 hours after creating it)<br/>
