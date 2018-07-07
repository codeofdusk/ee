# Imports
import argparse
from dateutil import parser as dateparser
# Set up command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("file",help="the tab-separated output file to read")
parser.add_argument("-w","--window",type=int,help="the time window to scan (the minimum amount of time between the creation of the talk page and the article required for inclusion in the output list), default is 86,400 seconds (one day)",default=86400)
args=parser.parse_args()
# Declare dictionaries
main={} #map of pages in namespace 0 (articles) to the timestamps of their first revision
talk={} #map of pages in namespace 1 (article talk pages) to the timestamps of their first revision
# Declare the chunk counter (count of number of times the header row appears)
chunk=0
# Read in file
with open(args.file) as fin:
    for line in fin:
        #Split fields
        t=line.strip().split("\t")
        # Check line length
        if len(t) != 3:
            print("Warning: The following line is malformed!:")
            print(line)
            continue
        if t[0] == "page_title" and t[1] == "rev_timestamp" and t[2] == "page_namespace":
            #New chunk
            chunk+=1
            print("Reading chunk " + str(chunk) + "...")
            continue
        #Is the page already in the dictionary?
        if t[0] in main and t[2]=="0":
            if int(t[1])<int(main[t[0]]):
                main[t[0]]=t[1]
            else:
                continue
        if t[0] in talk and t[2]=="1":
            if int(t[1])<int(talk[t[0]]):
                talk[t[0]]=t[1]
            else:
                continue
        # If not, add it.
        if t[2] == '0':
            main[t[0]]=t[1]
        elif t[2] == '1':
            talk[t[0]]=t[1]
print("Data collected, analyzing...")
matches=[]
for title,timestamp in main.items():
    if title not in talk:
        #No talk page, probably a redirect.
        continue
    elif dateparser.parse(main[title]).timestamp()-dateparser.parse(talk[title]).timestamp()>=args.window:
        matches.append(title)
print("Analysis complete!")
print("The following " + str(len(matches)) + " articles have visible edits to their talk pages earlier than the articles themselves:")
for match in matches:
    print(match.replace("_"," "))
print("Generating CSV report...")
import csv
with open("eeprocessed.csv","w") as cam:
    writer=csv.writer(cam)
    writer.writerow(("article","first main","first talk"))
    for match in matches:
        writer.writerow((match.replace("_"," "),main[match],talk[match]))
print("Done!")