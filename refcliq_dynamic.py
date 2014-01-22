#!/usr/bin/env python
# encoding: utf-8
"""
refcliq..py

Created by Neal Caren on June 26, 2013.
neal.caren@gmail.com

Dependencies:
pybtex
networkx
community

Note: community is available from:
http://perso.crans.org/aynaud/communities/

##note: seems to be screwing up where the person has lots of intials.###

JM - 1/20/14 - made the edge size and node weight time-sensitive {weights as dictionaries}. The big changes, basically, are that 1) the citational data elements are always  dictionaries now, not lists 2) the count increments are stored in these dictionaries. Downsides: runs slower, outputs slightly different edge/nodes counts than Caren's original (cannot figure out the cause of that latter point, but I do know that ref_cite was inexplicably processing differently as well and needed to be cleaned). I've also commented out the original's d3js and html outputs. It wouldn't take much to adapt them to the new, time-sensitive cocitational variables.


"""


from pybtex.database.input import bibtex
import itertools
import glob
import networkx as nx
import community
import re
from nltk import stem
from optparse import OptionParser
import time

now = time.time()

    
parser = OptionParser()
parser.add_option("-n", "--node_minimum",
                  action="store", type="int", dest="node_minimum", default=2)
parser.add_option("-e", "--edge_minimum",
                  action="store", type="int", dest="edge_minimum", default=2)
parser.add_option("-d", "--directory_name",
                  action="store", type="string", dest="directory_name",default='clusters')
(options, args) = parser.parse_args()

#Import files
try:
    flist= args
except:
    print 'No input file supplied.'
    exit()

#Stemmer for cleaning abstracts
stemmer = stem.snowball.EnglishStemmer()
def stem_word(word):
    return stemmer.stem(word)

def word_proper(word):
    #Title case, using small word list from that Daring Fireball guy.
    if word.lower() not in ['a','an','and','as','at','but','by','en','for','if','in','of','on','or','the','to']:
        return word[0].upper()+word[1:].lower()
    else:
        return word.lower()

def sentence_proper(text_string):
    #title case a a whole sentence
    proper_string = ' '.join([word_proper(word) for word in text_string.split()])
    try:
        return proper_string[0].upper()+proper_string[1:]
    except:
        return


def r_author(reference):
    #Extra author information from reference. Doesn't work when author isn't straighforward (like Census)
    #Includes last name and  first initital of the author.
    author = reference[0].strip('.')
    author_split = author.split()
    author_last_name = author_split[0]
    author_last_name = word_proper(author_last_name)
    try:
        author_first_initial = author_split[1][0].upper()
    except Exception, e:
        author_first_initial = ''
    if author_last_name == "Granovet.ms":
        author_last_name = "Granovetter"
        author_first_initial = "M"
    return '%s %s' % (author_last_name, author_first_initial)

def r_year(reference):
    #Extra year from references. Returns nothing when year is not an interger, I think.
    for item in reference:
        try:
            year = int(item)
            return year
        except Exception, e:
            pass
        if 'IN PRESS' in item:
            return 'In Press'
    return 'nd'
    #print reference

    return ''
def r_cite(reference):
    #Create a relatively unique name based on author, year and title.
    #Caren's script seems to be capturing a slightly different number of references (eg, I get 21,141 in SiR, he gets 21,249). But I don't really recall changing the script at all up here.
    try:
        author = r_author(reference)
        year = r_year(reference)
        ##JM - for some unholy reason, 'replace' was not removing the occasional '.' from the title string... this is not a problem in caren's original script....
        title = re.sub('\.','',r_title(reference))
        return '%s (%s) %s'.replace('.','') % (author,year,title)
    except Exception, e:
        return ''


def r_doi(reference):
    #extracts DOI from reference. I don't think I do anything with it though.
    if 'DOI ' in reference[-1]:
        return reference[-1].strip('DOI ')
    else:
        return ''

def r_title(reference):
    #cleans up title in reference
    #reliex on the fact that the first year splits author from title
    for order,item in enumerate(reference):
        try:
            year = int(item)
            title = reference[order+1]
            return sentence_proper(title)
        except Exception, e:
            pass
    return sentence_proper(reference[1])
    #return title

def split_references(references):
    #split references, correcting for the fact that '. ' is sometimes found within citations. Bastards.
    references=references.replace('{','').replace('}','').split('. ')
    split_references = [r.split(', ') for r in references]
    cut = False
    new_references = []
    old_reference = []
    for reference in split_references[:]:
        original = reference
        if cut == True:
#            reference = [' '.join(old_reference) + '' + reference[0].replace('.','')] + reference[1:]
            reference = [' '.join(old_reference)] + reference[1:]
            #print reference

        if len(reference)<2:
            old_reference = old_reference + reference
            cut = True
        else:
            new_references.append(reference)
            old_reference = []
            cut = False

            if '()' in r_cite(reference):
                print reference
                print r_cite(reference)
                print references
                print '\n'*5


    return new_references

def extract_article_info(b,bp):
        #grabs article info from a bibtex cite and returns some of the fields in a dictionary

        article_title    = sentence_proper(b.get("title",'No title').replace('{','').replace('}',''))
        article_journal  = b.get('series',b.get('journal','') )
        article_journal  = sentence_proper(article_journal.replace('{','').replace('}',''))
        article_year     = b.get('year','').replace('{','').replace('}','')
        article_volume   = b.get('volume','').replace('{','').replace('}','')
        article_number   = b.get('number','1').replace('{','').replace('}','')
        article_pages    = b.get('pages','').replace('{','').replace('}','')
        article_abstract = b.get('abstract','').replace('{','').replace('}','')
        article_doi      = b.get('doi','').replace('{','').replace('}','')
        if ' (C) ' in article_abstract:
            article_abstract = article_abstract.split(' (C) ')[0]

        try:
            references = [r_cite(r) for r in split_references(b["cited-references"])]
        except Exception, e:
            references = []

        try:
            authors_raw = bp["author"]
            article_author = '%s, %s' % ( authors_raw[0].last()[0], authors_raw[0].first()[0] )
            if len(authors_raw)>2:
                for a in authors_raw[1:-1]:
                    article_author = '%s, %s %s' % (article_author,a.first()[0],a.last()[0])
            if len(authors_raw)>1:
                article_author = '%s & %s %s' % (article_author,authors_raw[-1].first()[0],authors_raw[-1].last()[0])
        except Exception, e:
            article_author = "None"
            
        ###JM - added in self citation using same format as given in r_cite()
        self_ref = '%s (%s) %s'.replace('.','') % (article_author,article_year,article_title)

        article_cite = '%s. %s. "%s." %s. %s:%s %s.' % (article_author,
                                       article_year,
                                       article_title,
                                       article_journal,
                                       article_volume,
                                       article_number,
                                       article_pages)
        return {'cite' : article_cite,
                'year': article_year,
                'doi' : article_doi,
                'title' : article_title,
                'journal' : article_journal,
                'volume' : article_volume,
                'pages' : article_pages,
                'references' : references,
                'number' : article_number,
                'abstract' : article_abstract,
                'self_ref' : self_ref}





def import_bibs(filenames):
    #Takes a list of bibtex files and returns entries JSON style.
    parser = bibtex.Parser()
    entered = {}
    #take a list of files in bibtex format and returns a list of articles
    articles = []
    for filename in filenames:
        print 'Importing from %s' % filename
        try:
            bibdata = parser.parse_file(filename)
        except Exception, e:
            print 'Error with the file "%s"' % filename
        else:
            for bib_id in bibdata.entries:
                b = bibdata.entries[bib_id].fields
                bp= bibdata.entries[bib_id].persons
                article=extract_article_info(b,bp)
                if article['cite'] not in entered and len(article['references']) > 2:
                    articles.append(article)
                    entered[article['cite']]=True

    print 'Imported %s articles.' % thous(len(articles))
    return articles

def ref_cite_count(articles):
    #take a list of article and return a dictionary of works cited and their count
    #Later add journal counts
    cited_works = {}
    '''citing_works = {}'''
    for article in articles:
        references = set(article.get('references',[]) )

        article_year = article['year']

        for reference in references:

            try:
        		cited_works[reference]['count']['full_count'] += 1
        		try:
	        		cited_works[reference]['count'][article_year] += 1
	        	except:
	        		cited_works[reference]['count'][article_year] = 1
            except Exception, e:
            	cited_works[reference] = {'count':{'full_count':1, article_year:1} , 'abstract': article['abstract']}
    
    '''return cited_works,citing_works'''
    return cited_works

def top_cites(cited_works, threshold = 2):
    #returns sorted list of the top cites. Would probably be better if handled ties in a more sophisticated way.
    #most_cited = [r[0] for r in sorted(cited_works.items(), key=lambda (k,v): v['count'], reverse=True)[:n] ]
    #threshold = cited_works[most_cited[-1]]['count']
    #if threshold < 2:

    
    
    cocite_most_cited = {r:cited_works[r] for r in cited_works.keys() if cited_works[r]['count']['full_count'] >= threshold}
    
    '''citing_not_in_cited = [r for r in citing_works if r not in cocite_most_cited]
    
    cite_most_cited = cocite_most_cited + citing_not_in_cited    
    print 'Cite graph: Minimum node weight: %s' % threshold
    print 'Nodes: %s' % thous(len(cite_most_cited))'''
    
    print 'Cocite graph: Minimum node weight: %s' % threshold
    print 'Nodes: %s' % thous(len(cocite_most_cited))
    
    
    '''return cocite_most_cited,cite_most_cited'''
    return cocite_most_cited

def cite_keywords(cite, stopword_list, articles, n = 5):
    words_ab= [article.get('abstract') for article in articles if cite in article['references']]
    words_title= [article.get('title') for article in articles if cite in article['references'] and len(article.get('abstract'))<5 ]
    words = words_title + words_ab
    
    stopwords= ['do','and', 'among', 'findings', 'is', 'in', 'results', 'an', 'as', 'are', 'only', 'number',
              'have', 'using', 'research', 'find', 'from', 'for', 'to', 'with', 'than', 'since','most',
             'also', 'which', 'between', 'has', 'more', 'be', 'we', 'that', 'but', 'it', 'how',
             'they', 'not', 'article', 'on', 'data', 'by', 'a', 'both', 'this', 'of', 'study', 'analysis',
             'their', 'these', 'social', 'the', 'or','may', 'whether', 'them'', only',
             'implication','our','less','who','all','based','less','was',
           'its','new','one','use','these','focus','result','test',
           'finding','relationship','different','their','more','between',
           'article','study','paper','research','sample','effect','case','argue','three',
           'affect','extent','when','implications','been','data','even','examine','toward',
           'effects','analysis','into','support','show','within','what','were',
           'associated','suggest','those','over','however','while','indicate','about',
           'such','other','because','can','both','n','find','using','have','not',
           'some','likely','findings','but','results','among','has','how','which',
           'they','be','i','two','than','how','which','be','across','also','it','through','at']
    stopword_list = stopword_list + stopwords
    cite_words = keywords(words,stopword_list,n=n)
    return cite_words
    
def make_journal_list(cited_works):
    #Is it a journal or a book?
    #A journal is somethign with more than three years of publication
    #Returns a dictionary that just lists the journals
    cited_journals = {}
    for item in cited_works:
        title = item.split(') ')[-1]
        year = item.split(' (')[1].split(')')[0]
        try:
            if year not in cited_journals[title]:
                cited_journals[title].append(year)
        except:
            cited_journals[title] = [year]
    cited_journals = {j:True for j in cited_journals if len(set(cited_journals[j])) > 3 or 'J ' in j}
    return cited_journals

def make_filename(string):
    punctuation = '''!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~'''

    for item in punctuation:
        string = string.replace(item,'')
    string = string.replace(' ','_')
    string = string.lower()
    return string

def make_reverse_directory(articles):
    #creates reverse directory for all articles that cite a specific article:
    reverse_directory = {}
    for article in articles:
        cite = article['cite']
        for reference in article['references']:
            try:
                reverse_directory[reference].append(article)
            except Exception, e:
                 reverse_directory[reference] = [article]
    return reverse_directory


def write_reverse_directory(cite,cited_bys,output_directory,stopword_list, articles):
    html_preface = '''<html><head><meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
		<style type="text/css">
		body {
			background-color:#D9D9D9;
			text-rendering:optimizeLegibility;
			color:#222;
			margin-left:10%;
			font-family: Verdana, sans-serif;
                       font-size:12px;
			text-align:left;
                       width:600px;
			}
		h1 {
			font-weight:normal;
			font-size:18px;
			margin-left:0px;
			}
                h2 {
			font-weight: normal;
			font-size: 18px;
			margin-left: 0px;
			}
		p {
			font-weight:normal;
			font-size:12px;
			line-height:1.5;
			}
                 table {
    font-size:12px;
}
		</style> <body>'''
    html_suffix = r'''<p>Powered by <href='https://github.com/nealcaren/RefCliq' rarget="_blank">Refcliq<.</body></html>'''
    filename = make_filename(cite)
    output = open('%s/refs/%s.html' % (output_directory,filename), 'w')
    output.write(html_preface)
    output.write('<h1>Contemporary articles citing %s</h1>' % cite)
    output.write('<h2>%s</h2>' % ', '.join(cite_keywords(cite, stopword_list, articles, n = 10)) )
    output.write('<dl>')
    for item in cited_bys:
        output.write('<dt>%s \n' % item['cite'])
        if len(item.get('doi','')) > 2:
            link = 'http://dx.doi.org/%s' % item.get('doi','')
            output.write('''<a href='%s' target="_blank">Link</a>''' % link)
        #output.write('\n\n')
        output.write('<dd>%s\n' % item.get('abstract',''))
        output.write('<p>\t</p>\n')
    output.write(html_suffix)
    output.close()


def create_edge_list(articles, cocite_most_cited):
    #What things get cited together?
    cocite_pairs = {}
    '''cite_pairs = {}'''
    
    for article in articles:
        references = article.get('references',[])
        '''article_self_ref = article.get('self_ref')'''
        
        article_year = article.get('year')
        
        cocite_references = list(set([r for r in references if r in cocite_most_cited.keys()]))
        cocite_refs = itertools.combinations(cocite_references,2)

        '''cite_refs = list(set([r for r in references if r in cite_most_cited]))'''

        
        for cocite_pair in cocite_refs:
        	cocite_pair = sorted(cocite_pair)
        	cocite_pair = (cocite_pair[0],cocite_pair[1])
        	try:
        		cocite_pairs[cocite_pair]['full_count'] += 1
        		try:
        			cocite_pairs[cocite_pair][article_year] += 1
        		except:
        			cocite_pairs[cocite_pair][article_year] = 1
        	except:
        		cocite_pairs[cocite_pair] = dict()
        		cocite_pairs[cocite_pair][article_year] = 1
        		cocite_pairs[cocite_pair]['full_count'] = 1    
    
    return cocite_pairs

def top_edges(cocite_pairs, threshold = 2):
    # note that it doesn't just return top edges, but actually returns all the edges that have
    # an edge weight equal to or greater than the nth edge
    #most_paired = sorted(pairs, key=pairs.get, reverse=True)[:n]
    #threshold =  pairs[most_paired[-1]]
    
    
    cocite_most_paired = {p:cocite_pairs[p] for p in cocite_pairs.keys() if cocite_pairs[p]['full_count'] >= threshold}

    print 'Cocite graph: Minimum edge weight: %s' % threshold
    print 'Edges: %s' % thous(len(cocite_most_paired))

    return cocite_most_paired

'''def d3_export(most_cited, most_paired, cliques, suffix, output_directory=options.directory_name):
    #Exports network data in a JSON file format that d3js likes.
    #includes nodes with frequences and cliques; and edges with frequencies.
    import json
    import os    
    try:
        os.stat(output_directory)
    except:
        os.mkdir(output_directory)

    suffix = suffix + '.json'
    outfile_name = os.path.join('%s' % output_directory, suffix)

    node_key ={node:counter for counter,node in enumerate(sorted(most_cited))}
    nodes = [{'group': cliques[node]  ,
              'name' : node ,
              'nodeSize': int(cited_works[node]['count']) } for node in sorted(most_cited)]
    links  = [{'source': node_key[p[0]],
              'target' : node_key[p[1]],
              'value': int(p[2]['weight']) } for p in most_paired]
    d3_data = {'nodes': nodes, 'links' : links}
    json.dump(d3_data,open(outfile_name,'wb'))'''

def gexf_export(most_cited, most_paired, works_list, cliques, suffix, output_directory=options.directory_name):
	#Exports network data in .gexf format (readable by Gephi)
	#John Mulligan -- not the prettiest, but it gets the job done and translates all the information exported in the d3_export module.
    
    from xml.etree import ElementTree as et
    from xml.etree.ElementTree import Element, SubElement, tostring
    import os    
    
    try:
        os.stat(output_directory)
    except:
        os.mkdir(output_directory)
    suffix = suffix + '.gexf'
    outfile_name = os.path.join('%s' % output_directory, suffix)
    node_key ={node:counter for counter,node in enumerate(sorted(most_cited))}

    ##Create the tree
    et.register_namespace('',"http://www.gexf.net/1.2draft")
    et.register_namespace('viz','http://www.gexf.net/1.2draft/viz')
    tree = et.ElementTree()
    gexf = et.Element("gexf",{"xmlns":"http://www.gexf.net/1.2draft","version":"1.2"})
    tree._setroot(gexf)
        
    graph = SubElement(gexf,"graph",{'defaultedgetype':'undirected', 'mode':'dynamic', 'timeformat':'double'})
    #more (graph) header information
    graph_nodes_attributes = SubElement(graph,"attributes",{'class':'node','mode':'dynamic'})
    graph_nodes_mod_att = SubElement(graph_nodes_attributes,"attribute",{'id':'modularity_class','title':'Modularity Class','type':'integer'})
    graph_nodes_mod_att_content = SubElement(graph_nodes_mod_att,'default')
    graph_nodes_mod_att_content.text = "0"
    graph_nodes_score_att = SubElement(graph_nodes_attributes, "attribute", {'id':'score', 'title':'score', 'type':'integer'})
    graph_nodes_score_att.text = ' '
    
    graph_edges_attributes = SubElement(graph, "attributes", {'class':'edge', 'mode':'dynamic'})
    graph_edges_mod_att = SubElement(graph_edges_attributes,"attribute",{'id':'weight', 'title':'Weight', 'type':'float'})
    graph_edges_mod_att.text = ' '
        
    nodes = SubElement(graph,"nodes")
    edges = SubElement(graph,"edges")

    
    #write nodes
    for n in sorted(most_cited.keys()):
    	#create node in xml tree
    	
    	node_dates = sorted([int(a) for a in most_cited[n]['count'].keys() if a != 'full_count'])
    	node_date_sizes = works_list[n]['count']
    	node_start_date = str(min(node_dates)) + ".0"
    	
    	node = SubElement(nodes, "node")
    	node.attrib["start"] = node_start_date
    	node.attrib["end"] = '2016.0'
    	node.attrib["id"] = str(node_key[n])
    	node.attrib["label"] = n
    	#add attributes: clique, name
    	attributes_wrapper = SubElement(node, "attvalues")
    	clique_id = str(cliques[n])
    	clique = SubElement(attributes_wrapper, "attvalue", {"for":"modularity_class", "value":clique_id})
    	clique.text = ' '
    	#add attribute: visualization size
    	
    	last = 0
    	
    	##Each node's "count" attribute is set to a dictionary whose keys are the years it attained new references, and whose values are the number of new references it attained that year.
    	##The way this is configured right now, nodes only grow (no "decay" variable). size_ratchet keeps track of these size values
    	size_ratchet = 0
    	for nd in node_dates:
    		
    		size_ratchet += node_date_sizes[str(nd)]
    		##set the start date as the year of the node's changing size...
    		this_size_start_date = str(nd) + ".0"
    		##and the end date as one year prior to the next change...
    		if node_dates.index(nd) + 1 == len(node_dates):
    			this_size_end_date = "2016.0"
    		else:
    			this_size_end_date = str(int(node_dates[node_dates.index(nd)+1])-1) + ".0"
    		
    		this_size = str(size_ratchet)
    		
    		size_atty = SubElement(attributes_wrapper, "attvalue", {"for":"score","value":this_size, "start":this_size_start_date, "end":this_size_end_date})
    		size_atty.text = ' '
    #write edges
    c = 0
    
    for p in most_paired.keys():
    	id = str(c)
    	source = str(node_key[p[0]])
    	target = str(node_key[p[1]])
    	edge = SubElement(edges,"edge",{'source':source,'target':target,'id':id})
    	attributes_wrapper = SubElement(edge, "attvalues")
    	
    	edge_dates = sorted([int(a) for a in most_paired[p].keys() if (a != 'full_count')])
    	edge_dates = [str(a) for a in edge_dates]
    	##see "size ratchet" above in gexf_export()
    	weight_ratchet = 0
    	for ed in edge_dates:
			start_time = ed + ".0"
			if weight_ratchet == 0:
				clear_time_atty = SubElement(attributes_wrapper, "attvalue", {"for":"weight", "value":"0.0", "start":"1974.0", "end":start_time})
				clear_time_atty.text = ' '			
			pair = most_paired[p]
			weight_ratchet += pair[ed]

			try:
				end_time = str(int(edge_dates[edge_dates.index(ed)+1]-1)) + ".0"
			except:
				end_time = "2016.0"
			time_atty = SubElement(attributes_wrapper, "attvalue", {"for":"weight", "value":str(weight_ratchet), "start":start_time, "end":end_time})
			time_atty.text = ' '
    	c+=1

    	
    	##experiment to remove any edges from before 1975 (gephi is doing some weird-ass shit and displaying, apparently at random, edges between no-date items across the whole timeline   
    
    tree.write(outfile_name, xml_declaration = True, encoding = 'utf-8', method = 'xml')
	
	
def make_partition(G,min=5):
    #clustering but removes small clusters.
    partition = community.best_partition(G)
    cliques = {}
    for node in partition:
        clique = partition[node]
        cliques[clique] = cliques.get(clique,0) + 1

    revised_partition = {}
    for node in partition:
        clique = partition[node]
        if cliques[clique]>=min:
            revised_partition[node] = str(partition[node])
        else:
            revised_partition[node] = '-1'
    return revised_partition

'''#suite for making an html table
def html_table_row(row):
    row = [str(item) for item in row]
    return '<tr> <td>' + '</td> <td>'.join(row) + '</td> <tr>'

def html_table(list_of_rows):
    table_preface = r'<table>'
    table_body = '\n'.join( [html_table_row(row) for row in list_of_rows] )
    table_suffix = r'</table>'
    return table_preface + table_body + table_suffix

def clean_abstract(abstract):
    #takes a string and returns a list of unique words minus punctation.
    #Stemming should probably be an option, not a requirement
    from string import punctuation
    words = list(set([ stem_word(word.strip(punctuation)) for word in abstract.lower().split()]))
    words = [w for w in words if len(w)>0]
    return words'''

def article_clique(article, cliques, min=2):
    #Look up the clique of each of the reference
    #Note that most reference won't be found.
    clique_list = {}
    for ref in article['references']:
        if cliques.get(ref,'-1') != '-1':
            clique_list[cliques[ref]] = clique_list.get(cliques[ref],0) + 1

    #Assign the clique to the most
    try:
        top_clique = sorted(clique_list, key=clique_list.get, reverse=True)[0]
    except Exception, e:
        top_clique = '-1'

    #Set minimum threshold for number of cites to define clique membership
    if clique_list.get(top_clique,0) < min :
        top_clique = '-1'
    return top_clique

def split_and_clean(sentence):
    #turn string into a list of unique, lower-cased words
    punctuation = '''!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~'''
    words = [str(w.strip(punctuation).lower()) for w in sentence.split()]
    return list(set(words))

def make_word_freq(list_of_texts):
    from collections import Counter
    #returns the % of documents containing each word
    document_count =float(len(list_of_texts))
    #Split and clean each of the texts.
    list_of_texts = [split_and_clean(text) for text in list_of_texts]
    #flatten list
    words = [word for text in list_of_texts for word in text if len(word)>1 ]
    # % of docuemnts that have each word.

    #I've resisted using collections.Counter but it is really fast.
    word_counts = Counter(words)
    word_freq = {word : (word_counts[word]/document_count) for word in word_counts}
    return word_freq
    #for text in list_of texts:

def stopwords(articles, minfreq =.2):
    #list of commonly occuring words. You need to set the threshold low for most small texts.
    abstracts = [article['abstract'] for article in articles if len(article['abstract']) > 0 ]
    word_freq = make_word_freq(abstracts)
    stop_words = list(set(word for word in word_freq if word_freq[word] > minfreq ))
    return stop_words

def keywords(abstracts,stopword_list,n=10):
    #abstracts = [article['abstract'] for article in articles if len(article['abstract']) > 0 ]
    word_freq = make_word_freq(abstracts)
    word_freq = {w : word_freq[w] for w in word_freq if w not in stopword_list}
    top_words = sorted(word_freq, key=word_freq.get, reverse=True)[:n]
    return top_words

def journal_cliques(articles, cliques):
    #finds the journals that commonly cite a reference clique.
    from collections import Counter
    journals = [article['journal'] for article in articles]
    journal_counts = Counter(journals)
    clique_journals = {}
    for article in articles:
        journal = article['journal']
        ac = article_clique(article, cliques)
        if ac in clique_journals:
            clique_journals[ac][journal] = clique_journals[ac].get(journal,0) + (1 / float(journal_counts[journal]) )
        else:
            clique_journals[ac]={article['journal'] : (1 / float(journal_counts[journal]) )}
    clique_best_journal = { c: sorted(clique_journals[c], key=clique_journals[c].get, reverse=True)[:4] for c in clique_journals }
    return clique_best_journal



def get_clique_words(articles,cliques,stopword_list=[]):
    #This extracts the most common words in a clique based on articles that cite references in the clique.
    #Note that this is the most frequent, not the distinquishing words (i.e. not uniquely occuring in the clique.)
    stopwords= ['do','and', 'among', 'findings', 'is', 'in', 'results', 'an', 'as', 'are', 'only', 'number',
              'have', 'using', 'research', 'find', 'from', 'for', 'to', 'with', 'than', 'since','most',
             'also', 'which', 'between', 'has', 'more', 'be', 'we', 'that', 'but', 'it', 'how',
             'they', 'not', 'article', 'on', 'data', 'by', 'a', 'both', 'this', 'of', 'study', 'analysis',
             'their', 'these', 'social', 'the', 'or','may', 'whether', 'them'', only',
             'implication','our','less','who','all','based','less','was',
           'its','new','one','use','these','focus','result','test',
           'finding','relationship','different','their','more','between',
           'article','study','paper','research','sample','effect','case','argue','three',
           'affect','extent','when','implications','been','data','even','examine','toward',
           'effects','analysis','into','support','show','within','what','were',
           'associated','suggest','those','over','however','while','indicate','about',
           'such','other','because','can','both','n','find','using','have','not',
           'some','likely','findings','but','results','among','has','how','which',
           'they','be','i','two','than','how','which','be','across','also','it','through','at']
    stopword_list = stopword_list + stopwords
    
    clique_abstracts = {}
    for article in articles:
        ac = article_clique(article, cliques)
        if len(article['abstract'])>2:
            words = article['abstract']
        else:
            words = article['title']
        try:
            clique_abstracts[ac].append(words)
        except Exception:
            clique_abstracts[ac] = [words]
            
    clique_words = {clique: keywords(clique_abstracts[clique],stopword_list) for clique in clique_abstracts}
    return clique_words

def journal_report(articles):
    #Could I have a string with all the journals and how many items from each?
    from collections import Counter
    journals = Counter([article['journal'] for article in articles if article['journal'] is not None])

    try:
        journals = ['%s (%s)' % (j.replace('\\&','&'), journals[j]) for j in sorted(journals,key=journals.get, reverse=True) if journals[j] >= 10 ]
    except:
        journals = []
    return ', '.join(journals)

def thous(x, sep=',', dot='.'):
    #make numbers pretty
    num, _, frac = str(x).partition(dot)
    num = re.sub(r'(\d{3})(?=\d)', r'\1'+sep, num[::-1])[::-1]
    if frac:
        num += dot + frac
    return num

'''def clique_report(G, articles, cliques, suffix, no_of_cites=20, output_directory=options.directory_name):
    
    import os
    #This functions does too much.
    node_count = len(G.nodes())
    #gather node, clique and edge information
    nodes = list(G.nodes_iter(data=True))
    node_dict = {node[0]:{'freq':node[1]['freq'], 'clique':node[1]['group'], 'abstract':node[1]['abstract']} for node in nodes}
    node_min = sorted([node_dict[node]['freq'] for node in node_dict])[0]
    #Build a dictionary of cliques listing articles with frequencies
    clique_references = {}
    for node in node_dict:
        clique = node_dict[node]['clique']
        freq = node_dict[node]['freq']
        try:
            clique_references[clique][node] = freq
        except Exception, e:
            clique_references[clique] = {node : freq }
    clique_journals = journal_cliques(articles, cliques)

    #set up HTML
    html_preface = '''<html><head><meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
		<style type="text/css">
		body {
			background-color:#D9D9D9;
			text-rendering:optimizeLegibility;
			color:#222;
			margin-left:10%;
			font-family: Verdana, sans-serif;
                       font-size:12px;
			text-align:left;
                       width:800px;
			}
		h1 {
			font-weight:normal;
			font-size:18px;
			margin-left:0px;
			}
                h2 {
			font-weight: normal;
			font-size: 14px;
			margin-left: 0px;
			}
		p {
			font-size:12px;
			font-weight:normal;
			line-height:1.5;
			}
                 table {
    font-size:12px;
}
		</style> <body>'''
    html_suffix = r'''<p>Powered by <href='https://github.com/nealcaren/RefCliq' rarget="_blank">Refcliq<.</body></html>'''
    table_header = [['<b>Name</b>','','<b>Centrality</b>','<b>Count</b>','<b>Keywords</b>']]


    reference_location = os.path.join(output_directory,'refs')
    for dir_name in [output_directory,reference_location]:
        try:
            os.stat(dir_name)
        except:
            os.mkdir(dir_name)

    years = sorted([article['year'] for article in articles])
    suffix = suffix + 'index.html'
    outfile_name = os.path.join('%s' % output_directory, suffix)
    outfile = open(outfile_name,'wb')
    outfile.write (html_preface)
    journals = journal_report(articles)
    outfile.write('<h1>Cluster analysis of %s articles ' % thous(len(articles)) )
    outfile.write('based on %s references cited at least %s times.' % (thous(len(G.nodes())) , node_min ) )
    outfile.write('<h1>Major Journals: %s\n ' % journals)
    outfile.write('<h1>Years: %s-%s\n ' % (years[0],years[-1]))
    outfile.write('<h1>Clusters:' )
    stopword_list = stopwords(articles)
        
    
    clique_words = get_clique_words(articles,cliques ,stopword_list)


    reverse_directory = make_reverse_directory(articles)

    #Quick hack to figure out which are the biggest cliques and print in reverse order
    clique_size = {}
    for clique in clique_references:
        for ref in clique_references[clique]:
            clique_size[clique] = clique_size.get(clique,0) + clique_references[clique][ref]
    
    #Hack to put unsorted hack last:
    clique_size['-1'] = 0
        
    clique_counter = 0
    for clique in sorted(clique_size, key=clique_size.get, reverse=True):
        clique_members= [node for node in node_dict if node_dict[node]['clique']==clique]
        c=G.subgraph(clique_members)
        bc = nx.betweenness_centrality(c, normalized=True, weight='freq')
        vocab = ', '.join(clique_words.get(clique,''))
        table_text = []
        try:
            journals = ', '.join(clique_journals[clique])
        except Exception, e:
            journals = 'None'

        if int(clique) >= -2:
            
            if int(clique) == -1:
                vocab = "Cites that didn't cluster well."

            clique_counter = clique_counter +1

            outfile.write('<h2> %s   \n\n' % vocab)
            outfile.write('<br><b>Journals:</b> %s \n </h2>' % journals.replace(r'\&','&') )

            sorted_clique = sorted(clique_references[clique], key=clique_references[clique].get, reverse=True)
            if int(clique)> - 1:
                sorted_clique = sorted(bc, key=bc.get, reverse=True)

            output_cites = [cite for cite in sorted_clique[:no_of_cites] if node_dict[cite]['freq'] > 4]
            output_cites.sort()
            
            for cite in sorted(output_cites):
                write_reverse_directory(cite,reverse_directory[cite],output_directory,stopword_list,articles)

            table_text = table_header + [[str(cite_link(cite)+' '*40)[:130],'','%.2f' % bc[cite], node_dict[cite]['freq'],', '.join(cite_keywords(cite, stopword_list, articles, n = 5))] for cite in sorted_clique[:no_of_cites]]
            table_text= html_table(table_text)
            outfile.write(table_text)
            outfile.write('<p>')
    print 'Report printed on %s nodes, %s edges and %s cliques to %s.' % (thous(len(G.nodes())), thous(len(G.edges())), clique_counter, output_directory)
    outfile.write (html_suffix)

def cite_link(cite):
    import os
    link_name = 'refs/%s' % make_filename(cite)
    link = '''<a href='%s.html' target="_blank">%s</a>''' % (link_name,cite)
    return link'''

if __name__ == '__main__':
    filenames = flist
    articles = import_bibs(filenames)

    #This journals seems to follow me whererver I go
    articles = [a for a in articles if a['journal']!='Sociologicky Casopis-czech Sociological Review']
    
    cited_works = ref_cite_count(articles)
    
    print 'Cocite graph: Seems like you have about %s different references.' % thous(str(len(cited_works)))
    

    if options.node_minimum == 0:
        node_minimum = int(2 + len(articles)/1000)
    else:
        node_minimum = options.node_minimum
    
    cocite_most_cited = top_cites(cited_works, threshold = node_minimum)
        
    cocite_pairs = create_edge_list(articles, cocite_most_cited)
        
    cocite_most_paired = top_edges(cocite_pairs, threshold = options.edge_minimum)
	
    cocite_G=nx.Graph()

    cocite_G.add_edges_from(cocite_most_paired)

    
    for node in cocite_most_cited:
        cocite_G.add_node(node,freq= cited_works[node]['count']['full_count'])

    cocite_cliques = make_partition(cocite_G, min=10)
    
    for node in cocite_most_cited:
        cocite_G.add_node(node,freq= cited_works[node]['count']['full_count'], group = cocite_cliques[node], abstract = cited_works[node]['abstract'])
    
    '''d3_export(cocite_most_cited, cocite_most_paired, cocite_cliques, 'cocite', output_directory=options.directory_name)'''
    gexf_export(cocite_most_cited, cocite_most_paired, cited_works, cocite_cliques, 'cocite', output_directory=options.directory_name)
    '''clique_report(cocite_G, articles, cocite_cliques, 'cocite', no_of_cites=25)'''

#print time.time() - now
