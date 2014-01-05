RefCliq
====
This is a Python program that uses a network clustering algorthym to anlayze
 Web of Knowledge records in BibTeX format. The results are helpful for constructing
 literature reviews.
 
Requires Python 2.7 with the following dependencies:
* [NLTK](http://nltk.org)
* [Pybtex](http://pybtex.sourceforge.net)
* [NetworkX](http://networkx.github.io)
* [Community](http://perso.crans.org/aynaud/communities/)

You can install `NLTK`, `Pybtex` and `NetworkX` through `easy_install` or `pip`. To use `community`, download it and store it the same directory as `RefCliq` or somewhere else in your path.

Note: This should work with Python 2.6 if you have [Counter class](http://code.activestate.com/recipes/576611-counter-class/). 

Sample Usage:
--------
This program works exclusively with articles downloaded from Web of Knowledge that include the "Full Record" including "Cited References". Using a 
community detection algorithm, this program identifies clusters of citations and reports the most central works in each clusters. For each cluster,
it all list the most commonly occurring  words in abstracts (or titles when abstracts are not available) of articles that heavily cite works from the cluster
and the journals where that frequently cite these works. 

For each of the most central references in the cluster, the report includes the within cluster betweeness centrality, total count of the times the work was
cited and the words used most frequently  in articles/titles that cite that work. Selecting on a reference opens a new page that shows the contemporary works that cite that reference.

Here is a [sample](http://sociologicalresearch.org/clusters/us_sociology/) output based on articles published in US sociological journals in 2011 and 2012. 

If you had all the articles from the journal Mobilization stored as `moby.bib` 
and you wanted the analysis to be stored in a folder called `moby`:

    $ python refcliq.py moby.bib -d moby

The contents of the output directory include:
* `index.html` which is the cluster report.
* `refs` folder which contains information about listed references.
* `cites.json` which stores the resulting reference network for mapping in a format that d3js reads.
* `cites.gexf` ... Gephi format.
    
To run a standard analysis of the files, `us_2012_a.bib`, `us_2012_b.bib`, and , `us_2012_c.bib` and save the results in a folder called `us_sociology`.

    $ python refcliq.py us_2012.bib -d us_sociology

Using the same files and destination, but include all references with at least
two citations.

    $ python refcliq.py us_2012*.bib -d us_sociology -n 2

Using the same files and destination, but include all edges with at least two 
occurrences.

    $ python refcliq.py us_2012*.bib -d us_sociology -e 2
    



    