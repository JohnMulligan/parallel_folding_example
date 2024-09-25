from math import cos, sin, sqrt, floor, pi
import sys
import os
import networkx as nx
import make_graph
from itertools import product,islice
import numpy as np
import time
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

def main(N,r=1000,graphit=True):
	
	#R is the radius of the circle we draw to make our polygon
	G=make_graph.main(N,r)
	
	#threshold defines the euclidean distance at which we count two points as being close enough to one another to count them
	threshold=5
	
	#this is a bit of a cheat for the purposes of the workshop
	#a different process already gave us each N-gon's "good" folding angles
	thisngonknownanglesfile="outputs/%d/known_angles.txt" %N
	if os.path.exists(thisngonknownanglesfile):
		knownanglesfile=thisngonknownanglesfile
	else:
		knownanglesfile="known_angles.txt"
	d=open(knownanglesfile)
	t=d.read()
	d.close()
	lines=[l.strip() for l in t.split('\n') if l.strip()!='']
	known_angles=[]
	for l in lines:
		try:
			known_angles.append(float(l))
		except:
			print("error with line in angles file:",l)
	
	#Now we run through our spokes and
	##create a dictionary of the nodes that are "downstream" of each
	##so that when we "fold" on that spoke, we know which nodes are affected by it
	spokes={e:G.edges[e] for e in G.edges if G.edges[e]['set']=='spokes'}
	spokes_by_index={spokes[e]['index']:e for e in spokes}
	fold_spoke_indices=[spokes[s_id]['index'] for s_id in spokes][1:-1]
	
	#Here we get all the possible folds we'll be testing
	#And, creatively, we do this without actually generating them as a massive list
	#Why? Because the list grows exponentially
	possible_folds=product([i for i in [-1,1]],repeat=len(fold_spoke_indices))
	number_of_possible_folds=2**(N-1)
	
	#What are we testing again?
	##Every possible folding pattern
	##On every known angle
	total_work_list_length=number_of_possible_folds * len(known_angles)
	print("this job requires %d total iterations" %total_work_list_length)
	
	st=time.time()
	
	iter_step=0
	for this_folding in possible_folds:
		print("+++this folding:",this_folding)
		folds_completed=0
		for folding_angle in known_angles:
			loop_st=time.time()
			##You have to generate the graph anew every time because of how networkx uses memory
			print("this angle:",folding_angle)
			G=make_graph.main(N,r)
			G=folder(
				G=G,
				this_folding=this_folding,
				angle=folding_angle
			)
			close_neighborings,mean_close_neighborings=evaluate_folding(G,threshold)
			if close_neighborings !={}:
				print("->match at",folding_angle,"=",mean_close_neighborings)
				close_neighborings_list=sorted(list(close_neighborings.keys()))
				close_neighborings_id="*".join(close_neighborings_list)
				thismatch={
					"close_neighbors":close_neighborings_id,
					"close_neighborings_count":len(close_neighborings),
					"angle":folding_angle,
					"mean_close_neighborings":mean_close_neighborings,
					"this_folding":this_folding,
					"this_folding_np_id":"_".join([str(i) for i in [N,iter_step]])
				}
				if graphit:
					make_graph.draw_graph(G)
				e=open('outputs/%s/matches.txt' %(str(N)),'a')
				e.write("\n\n"+json.dumps(thismatch))
				e.close()
			print("loop time-->",time.time()-loop_st)
			iter_step+=1
		
		seconds_per_iter=(time.time()-st)/iter_step
		print("%d of %d steps completed in %d seconds. estimated %d minutes remaining" %(iter_step, total_work_list_length, int(time.time()-st),seconds_per_iter*(total_work_list_length-iter_step)/60))
		
		
	print("job completed in %d hours" %((time.time()-st)/3600))

if __name__=="__main__":
	N=int(sys.argv[1])
	if not N%2==0:
		print("N must be even. You supplied",N)
		exit()
	try:
		graphit=sys.argv[2]
		if graphit.lower().strip()=="false":
			graphit=False
		else:
			graphit=True
	except:
		graphit=True
	
	main(N,graphit=graphit)