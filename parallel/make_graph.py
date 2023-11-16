from math import cos, sin, sqrt, floor, pi
import sys
import os
import networkx as nx
from sympy.geometry import Point,Point3D, Line3D,Plane,Segment3D
import numpy as np

def main(N,r=1000):

	N=N

	alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ'

	acycles=int(floor((N+2)/len(alphabet)))
	G = nx.Graph()

	#this will get us up to a 702-sided figure
	buffer=''
	idx=0
	prev_v=None
	for c in range(acycles+1):
		if c > 0:
			buffer=alphabet[c-1]
		if c == acycles:
			leftoverlettersindex=(N+2)%len(alphabet)-1
			if leftoverlettersindex > 0:
				for a in alphabet[:leftoverlettersindex]:
					this_v=''.join([buffer,a])
					G.add_node(this_v,set='outer',index=idx)
					if prev_v is not None:
						G.add_edge(prev_v,this_v,set='outer',index=None)
					prev_v=this_v
					idx+=1
		else:
			for a in alphabet:
				if alphabet.index(a)<=N:
					this_v=''.join([buffer,a])
					G.add_node(this_v,set='outer',index=idx)
					if prev_v is not None:
						G.add_edge(prev_v,this_v, set='outer',index=None)
					prev_v=this_v
					idx+=1

	outernodeslist=[(n,G.nodes[n]['index']) for n in G.nodes]
	outervertexlabels=[v[0] for v in outernodeslist]

	innernodeslist=[
		"_".join(
			[
				outernodeslist[2*i-1][0],
				outernodeslist[(2*i)][0]
			]
		) for i in range(int((len(outernodeslist)-1)/2))
	]

	innernodeslist[0]="first"
	innernodeslist.append('last')

	prev_v=None

	spoke_indices=[]

	for this_v in innernodeslist:
	
		G.add_node(this_v,set='inner')
		if prev_v is not None:
			G.add_edge(prev_v,this_v,set='inner',index=None)
	
		innernodeindices=[]
		if this_v not in ('first','last'):
			for outernodename in this_v.split('_'):
		
				outernode=G.nodes[outernodename]
		
				spoke_index=outernode['index']
				
				G.add_edge(this_v,outernodename, set='spokes',index=spoke_index)
		
				spoke_indices.append(spoke_index)
		
				innernodeindices.append(outernode['index'])
		
				prev_v=this_v
		
			innernodeindex=min(innernodeindices)
	
			G.nodes[this_v]['index']=innernodeindex
		elif this_v=='first':
			G.nodes[this_v]['index']=0
			G.add_edge('first',outervertexlabels[0],set='spokes',index=0)
		elif this_v=='last':
			G.nodes[this_v]
			G.add_edge('last',outervertexlabels[-2],set='spokes',index=None)
			G.add_edge('last',outervertexlabels[-1],set='spokes',index=None)

	G.nodes['last']['index']=max(spoke_indices)+1
	G.edges[('last'),outervertexlabels[-2]]['index']=max(spoke_indices)+1
	G.edges[('last'),outervertexlabels[-1]]['index']=max(spoke_indices)+2
	G.add_edge('first',innernodeslist[1],set='inner',index=None)

	for node in outernodeslist:
	
		node_id,node_idx=node
	
		node_x=r*sin((node_idx%N)*pi/(N/2))
	
		node_y=r*cos((node_idx%N)*pi/(N/2))
		
		G.nodes[node_id]['pos']=(node_x,node_y,0)
	def node_xy(g,node_id):
		n=g.nodes[node_id]
		return (n['x'],n['y'])

	for node_id in innernodeslist:
		if node_id not in ("first","last"):
			outer_a_label,outer_b_label=node_id.split("_")
		
			outer_a_counterpart_idx=(outervertexlabels.index(outer_a_label)+3)%len(outervertexlabels)
			if outer_a_counterpart_idx==1:
				outer_a_counterpart_idx=2
		
			outer_a_counterpart_label=outervertexlabels[outer_a_counterpart_idx]
		
			outer_b_counterpart_idx=(outervertexlabels.index(outer_a_label)-2)
		
			if outer_b_counterpart_idx==-1:
				outer_b_counterpart_idx=-2
			
			outer_b_counterpart_label=outervertexlabels[outer_b_counterpart_idx]
		
			outer_a=G.nodes[outer_a_label]
		
			outer_b=G.nodes[outer_b_label]
		
			outer_a_counterpart=G.nodes[outer_a_counterpart_label]
		
			outer_b_counterpart=G.nodes[outer_b_counterpart_label]
		
		else:
		
			outer_a_counterpart_label=outervertexlabels[+2]
		
			outer_a_counterpart=G.nodes[outer_a_counterpart_label]
		
			outer_b_counterpart_label=outervertexlabels[-4]
		
			outer_b_counterpart=G.nodes[outer_b_counterpart_label]
		
			outer_a_label=outervertexlabels[-2]
		
			outer_a=G.nodes[outer_a_label]
		
			outer_b_label=outervertexlabels[0]
		
			outer_b=G.nodes[outer_b_label]
		A_Ac=Line3D(
			Point3D(outer_a['pos'][0],outer_a['pos'][1]),
			Point3D(outer_a_counterpart['pos'][0],outer_a_counterpart['pos'][1])
		)
	
		B_Bc=Line3D(
			Point3D(outer_b['pos'][0],outer_b['pos'][1]),
			Point3D(outer_b_counterpart['pos'][0],outer_b_counterpart['pos'][1])
		)
	
		np=A_Ac.intersection(B_Bc)[0]
		
		G.nodes[node_id]['pos']=(np.x,np.y,0)
		G.add_edge("last",innernodeslist[-2],set="inner")

	first_inner_node=G.nodes[innernodeslist[0]]
	for i in [0,1,2]:
		G.nodes['last']['pos']=first_inner_node['pos']
	
	return G
	

def draw_graph(G,title=None):
	import plotly.graph_objs as go
	
	node_xyz = np.array([G.nodes[v]['pos'] for v in sorted(G)])
	
	labels=[n for n in G.nodes]
	
	edge_xyz = np.array([
		(
			G.nodes[u]['pos'],
			G.nodes[v]['pos']
		) for u, v in G.edges()
	])
	
	Xn=[float(n[0]) for n in node_xyz]
	Yn=[float(n[1]) for n in node_xyz]
	Zn=[float(n[2]) for n in node_xyz]
	
	Xe=[]
	Ye=[]
	Ze=[]
	for e in edge_xyz:
		Xe.append(float(e[0][0]))
		Xe.append(float(e[1][0]))
		Xe.append(None)
		Ye.append(float(e[0][1]))
		Ye.append(float(e[1][1]))
		Ye.append(None)
		Ze.append(float(e[0][2]))
		Ze.append(float(e[1][2]))
		Ze.append(None)
	
	trace1=go.Scatter3d(
		x=Xe,
		y=Ye,
		z=Ze,
		mode='lines',
		line=dict(color='rgb(125,125,125)', width=3),
		hoverinfo='none',
		name="Edges"
	)
	
	trace2=go.Scatter3d(
		x=Xn,
		y=Yn,
		z=Zn,
		mode='markers',
		text=labels,
		hoverinfo='text',
		name="Vertices"
	)

	data=[trace1,trace2]
	
	fig=go.Figure(data=data)

	if title is not None:
		fig.update_layout(
			title=title
		)

	fig.show()

if __name__=="__main__":
	N=int(sys.argv[1])
	if not N%2==0:
		print("N must be even. You supplied",N)
		exit()
	try:
		graphit=bool(sys.argv[2])
	except:
		graphit=False
	g=main(N)
	if graphit:
		draw_graph(g)
