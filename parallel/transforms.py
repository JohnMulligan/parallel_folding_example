from sympy.geometry import Point,Point3D, Line3D
from math import cos, sin, sqrt  
import networkx as nx

def rotate(axis,p0,theta):
	## PointRotate.py Version 1.02
	## Copyright (c) 2006 Bruce Vaughan, BV Detailing & Design, Inc.
	## All rights reserved.
	## NOT FOR SALE. The software is provided "as is" without any warranty.
	#############################################################################
	"""
		Return a point rotated about an arbitrary axis in 3D.
		Positive angles are counter-clockwise looking down the axis toward the origin.
		The coordinate system is assumed to be right-hand.
		Arguments: 'axis point 1', 'axis point 2', 'point to be rotated', 'angle of rotation (in radians)' >> 'new point'
		Revision History:
			Version 1.01 (11/11/06) - Revised function code
			Version 1.02 (11/16/06) - Rewrote PointRotate3D function

		Reference 'Rotate A Point About An Arbitrary Axis (3D)' - Paul Bourke        
	"""
	
	p1,p2=axis.points

	# Translate so axis is at origin    
	p = p0 - p1
	N = (p2-p1)
	Nm = sqrt(N.x**2 + N.y**2 + N.z**2)

	# Rotation axis unit vector
	n = Point(N.x/Nm, N.y/Nm, N.z/Nm)

	# Matrix common factors     
	c = cos(theta)
	t = (1 - cos(theta))
	s = sin(theta)
	X = n.x
	Y = n.y
	Z = n.z

	# Matrix 'M'
	d11 = t*X**2 + c
	d12 = t*X*Y - s*Z
	d13 = t*X*Z + s*Y
	d21 = t*X*Y + s*Z
	d22 = t*Y**2 + c
	d23 = t*Y*Z - s*X
	d31 = t*X*Z - s*Y
	d32 = t*Y*Z + s*X
	d33 = t*Z**2 + c

	#            |p.x|
	# Matrix 'M'*|p.y|
	#            |p.z|
	qx = d11*p.x + d12*p.y + d13*p.z
	qy = d21*p.x + d22*p.y + d23*p.z
	qz = d31*p.x + d32*p.y + d33*p.z

	q=Point3D(qx,qy,qz)
	# Translate axis and rotated point back to original location    
	endpoint=q+p1
	return endpoint

def folder(G,this_folding,angle):
	'''
		This function takes
			1. A networkx graph object representing one of my shapes/nets for an N-gon
			2. An N-1 long array of +1 or -1 to instruct us how to fold on each "spoke"
			3. The angle by which to fold
	'''
	spokes=nx.Graph([(u,v,d) for u,v,d in G.edges(data=True) if d['set']=='spokes'])
	spoke_indices=[spokes.edges[e]['index'] for e in spokes.edges if spokes.edges[e]['index'] is not None]
	spoke_indices.sort()
	fold_spoke_indices=spoke_indices[1:-1]
	for r in fold_spoke_indices:
		this_spoke_name=[e for e in spokes.edges if spokes.edges[e[0],e[1]]['index']==r][0]
		subsequent_spoke_idxs=fold_spoke_indices[r:]
		affected_nodes=[]
		
		rna=G.nodes[this_spoke_name[0]]
		rnb=G.nodes[this_spoke_name[1]]
		rna['name']=this_spoke_name[0]
		rnb['name']=this_spoke_name[1]
		
		if rna['set']=='inner':
			tmp=rna
			rna=rnb
			rnb=tmp
		rotation_axis=Line3D(
			Point3D(rna['pos']),
			Point3D(rnb['pos'])
		)
		sign=this_folding[fold_spoke_indices.index(r)]
		these_affected_nodes=[]
		for n_id in G.nodes():
			if G.nodes[n_id]['index']>r:
				these_affected_nodes.append(n_id)

		for n_id in these_affected_nodes:
			
			n=G.nodes[n_id]
			affected_point=Point3D(n['pos'])
			affected_point_post_rotation=rotate(rotation_axis,affected_point,angle*sign)
			G.nodes[n_id]['pos']=(
				affected_point_post_rotation.x,
				affected_point_post_rotation.y,
				affected_point_post_rotation.z
			)
	return G
