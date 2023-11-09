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

def main(N,worker_number,number_of_workers,r=1000):
	
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
	
	## -----> HERE IS WHERE WE SET UP THE WRAPPER WE'LL PUT ON OUR WORK
	
	## AND BEFORE YOU START, REMEMBER THAT WE ALWAYS START COUNTING AT 0
	## SO IF YOU HAVE 5 WORKERS, THEY WILL HAVE THE FOLLOWING ID'S: [0,1,2,3,4]
	
	## 1. WE DON'T JUST NEED TO KNOW HOW MUCH WORK WE'VE GOT (TOTAL_WORK_LIST_LENGTH)
	#### WE ALSO NEED TO HAVE SOME PRINCIPLE FOR DIVVYING IT UP AMONGST OUR WORKERS
	#### HERE, I USE NUMPY TO CREATE THE INDEX AS AN ARRAY
	
	total_work_list=np.array(range(number_of_possible_folds))
	
	## 2. AND IN FACT I'M GONNA GET A LITTLE TRICKY WITH IT
	#### SPECIFICALLY, I'M GOING TO SET UP A CHECKPOINTING SYSTEM
	#### SO THAT I CAN PICK THE JOB UP WHERE IT WAS LEFT OF
	#### AND I'M GOING TO DO IT WITHOUT PEEKING INSIDE THE ITERATOR
	
	checkpointfilepath="outputs/%s/checkpoint.txt" %str(N)
	if os.path.exists(checkpointfilepath):
		## IF THERE'S A CHECKPOINT FILE IN EXISTENCE, READ IT OUT
		## WHAT IT WILL CONTAIN ARE THE INDICES FROM OUR TOTAL_WORK_LIST
		### ---> WHEN A PRIOR JOB COMPLETED THAT STEP
		d=open(checkpointfilepath,'r')
		t=d.read()
		d.close()
		lines=t.split("\n")
		checkpoints=np.array([int(l) for l in lines if l!=''])
		## SCREEN THOSE INDICES OUT OF YOUR WORK LIST
		remaining_work=np.array([i for i in total_work_list if i not in checkpoints])
	else:
		##
		os.makedirs('outputs/%s/' %str(N), exist_ok=True)
		remaining_work=np.array(total_work_list)
	
	print("total amount of work remaining:",len(remaining_work))
	#### 3. NOW SPLIT UP THE REMAINING WORK
	#### YOU'LL USE THIS ALL THE TIME IN PARALLELIZATION
	#### https://numpy.org/doc/stable/reference/generated/numpy.array_split.html
	workbatches=np.array_split(remaining_work,number_of_workers)
	
	#### AND PULL THE WORK ASSIGNMENTS FOR THIS WORKER
	this_work_batch=workbatches[worker_number]
	total_work_this_worker=len(this_work_batch)
	print("work remaining for this worker:",total_work_this_worker)
	
	st=time.time()
	#we can still use a raw "iter step" counter to keep track of
	#how much work we've done in this process -- but it can't serve as our index within
	#the iterator anymore
	iter_step=0
	
	## 4. We're now wrapping our work inside the batch that this worker is assigned
	print(this_work_batch)
	for this_step_idx in this_work_batch:
		print(this_step_idx)
		#open up your checkpoint file handler in append-only mode
		d=open(checkpointfilepath,'a')
		#### another super useful tool for handling split-up workloads
		#### https://docs.python.org/3/library/itertools.html#itertools.islice
		#### but you do have to be careful when combining it with iterators (this is a python thing)
		#### python iterators can only be used once, and it's more efficient to keep regenerating them
		#### https://docs.python.org/3/library/itertools.html#itertools-recipes
		possible_folds=product([i for i in [-1,1]],repeat=len(fold_spoke_indices))
		for this_folding in islice(possible_folds,this_step_idx,this_step_idx+1):
			print("+++this folding:",this_folding)
			matches=[]
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
					matches.append({
						"close_neighbors":close_neighborings_id,
						"close_neighborings_count":len(close_neighborings),
						"angle":folding_angle,
						"mean_close_neighborings":mean_close_neighborings,
						"this_folding":this_folding,
						"this_folding_np_id":"_".join([str(i) for i in [N,this_step_idx]])
					})
					# Sorry, no visualization on a batch-submitted job!!
					# make_graph.draw_graph(G)
				print("loop time-->",time.time()-loop_st)
				iter_step+=1
			if len(matches)>0:
				# 5. AND MAKE SURE THAT YOU DIFFERENTIATE YOUR OUTPUT FILES BY WORKER
				### YOU'LL HAVE TO GATHER THOSE OUTPUTS TOGETHER AFTER THE FACT
				### BUT IT'S BETTER THAN HAVING YOUR DIFFERENT WORKERS TRY TO WRITE
				### TO THE SAME FILE AT ONCE, AND EITHER FAIL, OR MESS UP YOUR OUTPUTS
				e=open('outputs/%s/%s.txt' %(str(N),str(worker_number)),'a')
				for thismatch in matches:
					e.write("\n\n"+json.dumps(thismatch))
				e.close()
			#here, we record the step indices for later checkpointing use
			d.write('\n%s' %str(this_step_idx))
			seconds_per_iter=(time.time()-st)/iter_step
			print("%d of %d steps completed in %d seconds. estimated %d minutes remaining" %(iter_step, total_work_this_worker, int(time.time()-st),seconds_per_iter*(total_work_this_worker-iter_step)/60))
		d.close()
		
	print("job completed in %d hours" %((time.time()-st)/3600))

if __name__=="__main__":
	N=int(sys.argv[1])
	worker_number=int(sys.argv[2])
	number_of_workers=int(sys.argv[3])
	print("MAKING NET WITH %d-GON. This is worker index %d of %d" %(N,worker_number,number_of_workers))
	main(N,worker_number,number_of_workers)