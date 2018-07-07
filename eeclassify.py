import csv
import argparse
from dateutil import parser as dateparser
from collections import Counter,defaultdict
# Requires unidecode from PyPI
import unidecode
parser = argparse.ArgumentParser()
parser.add_argument("eeprocessed",help="the .csv output file (from eeprocess.py) to read")
parser.add_argument("eeanalysis",help="the .csv output file (from eeanalyze.py) to read")
args=parser.parse_args()
# Declare main and talk dicts, mapping article names to timestamps of their first main and talk edits respectively
main={}
talk={}
# Declare reasons and comments dicts, mapping article names to reasons and comments (from eeanalyze)
reasons={}
comments={}
# Read in CSVs
with open(args.eeprocessed) as fin:
    reader=csv.reader(fin)
    #Skip the header
    next(reader)
    #read in main and talk dicts
    for row in reader:
        main[row[0]]=row[1]
        talk[row[0]]=row[2]
with open(args.eeanalysis) as fin:
    reader=csv.reader(fin)
    #Skip the header
    next(reader)
    #Read in reasons, filtering out revision deletion based on the comment field (I'm sure there's a better way, but the log_deleted field in the db which determines if a deletion is page or revision doesn't properly exist for all deletes or mwxml doesn't see it in all cases)
    for row in reader:
        if "rd1" not in row[2].lower():
            reasons[row[0]]=row[1]
            comments[row[0]]=row[2]
print("Read " + str(len(main)) + " main, " + str(len(talk)) + " talk, and " + str(len(reasons)) + " articles that were automatically analyzed (not counting revision deletions; they are false positives for my purposes).")
# Fix misclassified copyvios
for article,reason in reasons.items():
    c=comments[article].lower()
    if "copyright" not in reason and ("copyright" in c or "copyvio" in c or "g12" in c or "a8" in c):
        reasons[article]="copyright (" + reasons[article] + ")"
# Classify articles affected by the Great Oops (15:52, 25 February 2002 UTC) and UseMod keep pages
reasons.update({a:"great oops" for a,ts in main.items() if dateparser.parse(ts).timestamp() <= 1014652320 and dateparser.parse(talk[a]).timestamp() <= 1014652320})
comments.update({a:"" for a,r in reasons.items() if r == "great oops"})
# find split histories (pages with identical names except caps and diacritics)
acounter=Counter([unidecode.unidecode(a).lower() for a in main])
splitkeys=[k for k,v in acounter.items() if v>1]
splithist=defaultdict(dict)
for a,ts in main.items():
    k=unidecode.unidecode(a).lower()
    if k in splitkeys:
        splithist[k][dateparser.parse(ts).timestamp()]=a
for a,m in splithist.items():
    t=sorted(m.keys())
    reasons[m[t[0]]]="split from " + m[t[1]]
    comments[m[t[0]]]=""
# Add unknowns
reasons.update({a:"unknown" for a in main if a not in reasons})
comments.update({a:"" for a,r in reasons.items() if r == "unknown"})
# Write eefinal.csv
print("Writing eefinal.csv...")
with open("eefinal.csv","w") as cam:
    writer=csv.writer(cam)
    writer.writerow(("article","first main","first talk","reason","comment"))
    for a in sorted(reasons.keys()):
        if reasons[a]=="unknown" and unidecode.unidecode(a).lower() in splitkeys:
            continue
        writer.writerow((a,main[a],talk[a],reasons[a],comments[a]))
print("CSV written. Generating stats...")
copyvios=0
copymoves=0
talkmoves=0
histsplits=0
oopses=0
unknowns=0
for a,r in reasons.items():
    if r == "copyright":
        copyvios+=1
    elif r.startswith("copyright ("):
        copymoves+=1
    elif r.startswith("move from"):
        talkmoves+=1
    elif r.startswith("split from"):
        histsplits+=1
    elif r == "great oops":
        oopses+=1
    elif r == "unknown":
        unknowns+=1
print(str(copyvios) + " articles were copyright violations.")
print(str(copymoves) + " articles were copyright violations, but a new page was moved over the violating material.")
print(str(talkmoves) + " articles were likely moved by cut and paste, while their talk pages were moved properly.")
print(str(histsplits) + " articles have split history, with differences in capitalization or diacritics in the title.")
print(str(oopses) + " articles were affected by the Great Oops or UseMod keep pages.")
print(str(unknowns-histsplits) + " articles could not be automatically analyzed.")
print("Done!")
