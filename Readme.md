# Dihedral angles experiment

## Installation

1. Kick off a virtual environment: ```python3 -m venv venv```
1. Use it: ```source venv/bin/activate```
1. Install the necessary packages: ```pip install -r requirements.txt```

## Introduction

This is an adaptation of my old folding experiment to illustrate high-throughput parallelization.

The problem is this: we have found that if you cut up an even-sided polygon in a particular way, it can fold in specific ways to create interesting forms.

![Sample image](../assets/sample_decagon.png)

We know:

* There are specific angles that work with for specific N-gons
* And there are a whole bunch of different ways of folding at that angle that work

What we *don't* know is which of those an

And, to complicate it... as the number of sides goes up

* The processing time goes up for each simulation
* The number of simulations *doubles* with each step

So we want to come up with a creative way of parallelizing this work. I like this example because it shows how we can

* Cleverly define a parameter space without using much memory in Python using itertools
* Sweep that space rigorously and record our good results
* Even go so far as parameterizing the way we're generating that work list
* And use *checkpointing* so that our jobs can pick up where they left off

This allows us to parallelize massively.

## Serial Folder

This group of files shows you the basics of the experiment, running on a single thread

### make_graph.py

This script is used by all the other processes as it builds the object we're analyzing. It uses NetworkX and SymPy to

1. make an N-sided polygon (where N is even) A
1. make
	1. an N/2-sided polygon B within A ...
	1. buffered by a ring of triangles and trapezoids
	1. with duplicate nodes at the start/end to allow us to fold the shape
1. connect all of these points in a manner that will allow us to fold the shape

You can call it like ```python make_graph.py 10``` to make a 10-sided shape. It accepts an optional boolean argument in position 2 (default is false) which, if true, will render a visual of the starting state, like ```python make_graph.py 10 true```:

![Sample image](../assets/sample_decagon.png)

So what we have here is a NetworkX graph of vertices with x,y,z coords and then edges connecting them. We'll be manipulating these nets along particular vertices as though they were rigid surfaces -- like Origami.

### transforms.py

This contains two functions: folder() and rotate().

"Folder" takes:

1. Your networkx graph of vertices (x,y,z) and edges (source,target)
1. Your instructions folding on specific vertices [-1,1,-1....]
1. The angle you'll be folding at

It then hands off to the "Rotate" function, which I happily found had been written by Bruce Vaughan in 2006. This performs the actual rotation using Python's SymPy package.

### main.py bundles these together to find good matches

You invoke it by telling it the size of your N-gon, e.g., ```python main.py 10```

It will then generate the graph, come up with the full list of folds it has to test, and begin running through these. You will see it output its results, and display good matches as it finds them.

Keep an eye on the running time. Then try it with a larger number -- up to 18 in this repo.

## Parallel Folder

As you've seen, the amount of time per simulation goes up as you add sides to your N-gon, and the amount of work doubles with the addition of each additional side. This is a great candidate for parallelization.

In the parallelization folder, the only things we've changed are:

1. altered main.py so that it takes a couple new arguments
1. added a scavenger.slurm file

### changes to main.py

main.py now takes a couple new arguments:

* number of workers
* worker id

You can try this on the command line like ```python main.py 10 2 5```. This command would:

1. create a 10-sided figure as before
2. split the workload up among 5 worker processes
3. kick off that work as the *THIRD* worker process (always start counting at zero!)

You'll see that the amount of work for that worker has gone down dramatically.

How does that parallelization work? Take a look at the new comments in main.py You'll see that we generate the full work list but then use that generator to split it up into chunks. Each worker then only gets that subset of work.

We also use *checkpointing* to keep track of which simulations we've run, so that we can effortlessly pick up where we left off if the job didn't finish.

There's a great write-up of checkpointing here: https://chtc.cs.wisc.edu/uw-research-computing/checkpointing

### scavenger.slurm

This allows you to submit a whole bunch of jobs at once. You invoke this like ```sbatch scavenger.slurm --array=0-49```, which would give you 50 worker processes, from index 0 to index 49.