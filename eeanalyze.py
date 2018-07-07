import mwxml
import argparse
import csv
from dateutil import parser as dateparser
from collections import defaultdict
# Set up command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("file",help="the .csv output file (from eeprocess.py) to read")
parser.add_argument("dump",help="the uncompressed English Wikipedia pages-logging.xml dump to check against")
args=parser.parse_args()
print("Reading " + args.file + "...")
with open(args.file) as fin:
    reader=csv.reader(fin)
    #Do we have a valid CSV?
    head=next(reader)
    if head[0] != "article" or head[1] != "first main" or head[2] != "first talk":
        raise ValueError("invalid .csv file!")
    #valid CSV
    #Create main and talk dicts to store unix times of first main and talk revisions
    main={}
    talk={}
    for row in reader:
        if row[0] in main or row[0] in talk:
            raise ValueError("Duplicate detected in cleaned input!")
        main[row[0]]=dateparser.parse(row[1]).timestamp()
        talk[row[0]]=dateparser.parse(row[2]).timestamp()
print("Read " + str(len(main)) + " main, " + str(len(talk)) + " talk. Checking against " + args.dump + "...")
with open(args.dump) as fin:
    d=mwxml.Dump.from_file(fin)
    #Create reasons, dict mapping article names to reasons why their talk pages appear to have edits before the articles themselves.
    reasons={}
    #Create comments, dict mapping article names to log comments.
    comments={}
    #Create moves, defaultdict storing page moves for later analysis
    moves=defaultdict(dict)
    for i in d.log_items:
        if len(main) == 0:
            break
        try:
            if (i.page.namespace == 0 or i.page.namespace == 1) and i.params in main and i.action.startswith("move"):
                moves[i.params][i.page.namespace]=(i.page.title,i.comment)
            if (i.page.namespace == 0 or i.page.namespace == 1) and i.action == "delete" and i.page.title in main:
                c=str(i.comment).lower()
                if ('copyright' in c or 'copyvio' in c or 'g12' in c or 'a8' in c):
                    reasons[i.page.title]="copyright"
                    comments[i.page.title]=i.comment
                    print("Copyright violation: " + i.page.title + " (" + str(len(reasons)) + " articles auto-analyzed, " + str(len(main)) + " articles to analyze, " + str(len(moves)) + " move candidates)")
            if i.params in moves and i.params in main:
                del main[i.params]
            if i.page.title in reasons and i.page.title in main:
                del main[i.page.title]
        except (AttributeError,TypeError):
            print("Warning: malformed log entry, ignoring.")
            continue
    print(str(len(moves)) + " move candidates, analyzing...")
    for article,movedict in moves.items():
        if 1 in movedict and 0 not in movedict:
            reason="move from " + movedict[1][0]
            comment=movedict[1][1]
            reasons[article]=reason if article not in reasons else reasons[article]+", then " + reason
            comments[article]=comment if article not in comments else comments[article]+", then " + comment
print("Writing move candidate csv...")
with open("eemoves.csv","w") as cam:
    writer=csv.writer(cam)
    writer.writerow(("from","to","namespace","comment"))
    for article,movedict in moves.items():
        for namespace,move in movedict.items():
            writer.writerow((move[0],article,namespace,move[1]))
print(str(len(reasons)) + " pages auto-analyzed, generating CSV...")
with open("eeanalysis.csv","w") as cam:
    writer=csv.writer(cam)
    writer.writerow(("article","reason","comment"))
    for page, reason in reasons.items():
        writer.writerow((page, reason,comments[page]))
print("Done!")
