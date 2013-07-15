RefCliq
====
This is a Python program that uses a network clustering algorthym to anlayze
 Web of Knowledge records in BibTeX format. The results are helpful for constructing
 literature reviews.
 
Requires Python 2.7 and the following dependencies:
* [NLTK](http://nltk.org)
* [Pybtex](http://pybtex.sourceforge.net)
* [NetworkX](http://networkx.github.io)
* [Community](http://perso.crans.org/aynaud/communities/)

Note: This should work with Python 2.6 if you have [Counter class](http://code.activestate.com/recipes/576611-counter-class/). 

Sample Usage:
This program works exlusively with articles downloaded from Web of Knowledge that include the "Full Record" including "Cited References".
    $ python refcliq.py moby.bib -d moby