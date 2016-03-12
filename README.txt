Name: cyfi.py
This program accepts the typical flow cytometry data in FCS2 (and maybe other formats)
and interactively displays the 1D histogram or 2D scatter plots in a browser.
Importantly, the program allows users to interactively define gates using the
forward and side scatter plot. The selection is used to filter the events and generate
a histogram of selected cells/beads. The interactive feature is implemented using the mpld3 library. 

The script has been validated using Anaconda-2.2.0 running python 2.7. It generates 
errors in Anaconda2-2.5 and does not run on Anaconda3 (which uses python 3.5).

To run the program:
1. Start MongoDB.
2. python cyfi.py
3. Open 127.0.0.1:5000 in a browser

The versions of various modules installed on my computer at the current time 
(and therefore compatible with this program) are listed in cyfi_requirements.txt. 


