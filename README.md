# RedGifDownloader
Repository of RedGif Downloader, there isn't much to explain

## Usage

1. Create a text file (.txt) and paste the urls, one per line
2. Inside the program select a directory to save (it is saved so you don't have to assign a folder every time you open the software)
3. Make any additional changes to the configuration after opening the application once (after changes are made, you will have to close the RedGifDownloader window and open it again)
4. Select the text file with the urls
5. Press the download button
____________________________________________________________

In case you are using the source instead of the binaries (which will be posted when compiled hopepefully) you'll these libraries:

- **os** (included in python)
- **Tkinter** (included in python)
- **ConfigParser** (included in python)
- **Pygubu** (https://github.com/alejandroautalan/pygubu / https://pypi.org/project/pygubu/)
- **Requests** (https://pypi.org/project/requests/ / https://github.com/psf/requests)

also it was built using Python 3.8.7 and Pygubu Designer (https://github.com/alejandroautalan/pygubu-designer / https://pypi.org/project/pygubu-designer/)

______________________________________________________________

Some explanations about the functionality and some things I'll try to implement.
At the moment its a very basic download software, the basic functionality is complete but some links may not work because of the way the page saves them.

Also some functions I'll try to implement or create
 - Pause and Continue a download
 - Option to insert links directly instead of using a text file.
 - A more optimized command line app without GUI (the original code was accidentally deleted 7 hours after creating it)
