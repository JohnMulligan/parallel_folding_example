from math import cos, sin, sqrt, floor, pi
import sys
import os
import networkx as nx
import make_graph
from itertools import product,islice
import numpy as np
import time
import re
import json
from transforms import folder,rotate

def get_euclidean_distance(a,b):
	ax,ay,az=a
	bx,by,bz=b
	ed=sqrt((ax-bx)**2+(ay-by)**2+(az-bz)**2)
	return ed
	
def evaluate_folding(G,closeness_threshold):
	nodelist={n:0 for n in G.nodes()}
	outernodes = {x:y['index'] for x,y in G.nodes(data=True) if y['set']=='outer'}
	outernodes_sorted={k: v for k, v in sorted(outernodes.items(), key=lambda item: item[1])}
	outernode_labels_sorted=list(outernodes_sorted.keys())
	first_outernode_label=outernode_labels_sorted[0]
	last_outernode_label=outernode_labels_sorted[-1]
	terminal_outernodes=[first_outernode_label,last_outernode_label]
	close_neighborings={}
	all_close_distances=[]
	all_distances=[]
	for n_id_a in nodelist:
		for n_id_b in nodelist:
			if n_id_a!=n_id_b:
				ed=get_euclidean_distance(
					G.nodes[n_id_a]['pos'],
					G.nodes[n_id_b]['pos']
				)
				all_distances.append(ed)
				if ed < closeness_threshold:
					all_close_distances.append(ed)
					neighboring_id="__".join([n_id_a,n_id_b])
					if neighboring_id not in close_neighborings:
						close_neighborings[neighboring_id]=ed
					else:
						if ed < closeness_threshold:
							close_neighborings[neighboring_id]=ed
	if len(all_close_distances)>0:
		mean_close_neighborings=sum(all_close_distances)/len(all_close_distances)
	else:
		mean_close_neighborings=None
	return close_neighborings,mean_close_neighborings


def main(N,r=1000):
	
	basepath="outputs/%d/" %N
	
	matchesfiles=[f for f in os.listdir(basepath) if re.match("[0-9]+\.txt")]
	
	if len(matchesfiles)==0:
		print("no file like 0.txt in folder outputs/%d" %N)
	
	matches=[]
	
	for matchesfile in matchesfiles:	
		thismatchesfile=os.path.join(basepath,matchesfile)
		if os.path.exists(thismatchesfile):
			thismatchesfile=thismatchesfile
		else:
			print("file does not exist:",thismatchesfile)
			exit()
		d=open(thismatchesfile)
		t=d.read()
		d.close()
		lines=[l.strip() for l in t.split('\n') if l.strip()!='']
		
		for line in lines:
			linejson=json.loads(line)
			matches.append(linejson)
		
	c=1
	for m in matches:
		print("rendering match %d of %d" %(c,len(matches)))
		G=make_graph.main(N,r)
		folding_angle=m['angle']
		this_folding=m['this_folding']
		
		G=folder(
			G=G,
			this_folding=this_folding,
			angle=folding_angle
		)
		close_neighbors,mean_close_neighborings=evaluate_folding(G,r*.0005)
		
		neighborings=[]
		for neighboring in close_neighbors:
			abpair=neighboring.split("__")
			abpair.sort()
			if abpair not in neighborings:
				neighborings.append(abpair)
		
		intersectionstring=";".join([','.join(abpair) for abpair in neighborings])
		
		title="%d-sided figure, folded at %s radians, in the following pattern: %s. Intersections at %s" %(N,str(folding_angle),str(this_folding),intersectionstring)		
		
		make_graph.draw_graph(G,title=title)
		c+=1

if __name__=="__main__":
	N=int(sys.argv[1])
	print(sys.argv)
	main(N)