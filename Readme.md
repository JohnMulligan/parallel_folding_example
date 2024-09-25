# Dihedral angles experiment

## Installation

1. Kick off a virtual environment: ```python3 -m venv venv```
1. Use it: ```source venv/bin/activate```
1. Install the necessary packages: ```pip install -r requirements.txt```

## Introduction

This is an adaptation of my old folding experiment to illustrate high-throughput parallelization.

The problem is this: we have found that if you cut up an even-sided polygon in a particular way, it can fold in specific ways to create interesting forms.

![Sample image](/assets/sample_decagon.png)

We know:

* There are specific angles that work with for specific N-gons
	* this is a bit of a cheat for this exercise
	* there's a much bigger parameter sweep possible here)
* And there are a whole bunch of different ways of folding at that angle that work
	* every new side you add to the shape
	* doubles the number of possible ways you can fold the shape, whatever the angle

What we *don't* know is which of those an

And, to complicate it... as the number of sides goes up

* The processing time goes up for each simulation
* The number of simulations *doubles* with each step

So we want to come up with a creative way of parallelizing this work. I like this example because it shows how we can

* Cleverly define a parameter space
	* In this case, in Python, without using much memory using itertools
* Sweep that space rigorously and record our good results
* Even go so far as parameterizing the way we're generating that work list
* And use *checkpointing* so that our jobs can pick up where they left off

This allows us to parallelize massively.

## Visualizing results

In a serial run, you'll get matches written out to a file like ```outputs/{{N}}/matches.txt``` where N is the number of sides on your polygon. In a parallel run, they'll be written out to files like ```ouputs/{{N}}/{{P}}.txt``` where P is the task id in your high-throughput job that generated it.

To render all of the matches that your process found along the way, use, in either folder, ```python visualize_results.py {{N}}```. It will gather these up and render the as 3d graphs in your browser.

I have a sample file in ```serial/outputs/12/matches.txt```, which you can test by running ```python visualize_results.py 12```.

## Serial Folder

This group of files shows you the basics of the experiment, running on a single thread

### make_graph.py

This script is used by all the other processes as it builds the object we're analyzing. It uses the Python NetworkX and SymPy packages to

1. make an N-sided polygon (where N is even) A
1. make
	1. an N/2-sided polygon B within A ...
	1. buffered by a ring of triangles and trapezoids
	1. with duplicate nodes at the start/end to allow us to fold the shape
1. connect all of these points in a manner that will allow us to fold the shape

You can call it like ```python make_graph.py 10``` to make a 10-sided shape. It accepts an optional boolean argument in position 2 (default is false) which, if true, will render a visual of the starting state, like ```python make_graph.py 10 true```:

![Sample image](/assets/sample_folded_decagon.png)

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

In the parallelization folder, the only things we've changed:

1. Altered main.py so that it takes a couple new arguments
1. Added a scavenger.slurm file

### changes to main.py

main.py now takes a couple new arguments:

* Number of workers
* Worker id

You can try this on the command line like ```python main.py 10 2 5```. This command would:

1. create a 10-sided figure as before
2. split the workload up among 5 worker processes
3. kick off that work as the *THIRD* worker process (always start counting at zero!)

You'll see that the amount of work for that worker has gone down dramatically.

How does that parallelization work? Take a look at the new comments in main.py You'll see that we generate the full work list but then use that generator to split it up into chunks. Each worker then only gets that subset of work.

We also use *checkpointing* to keep track of which simulations we've run, so that we can effortlessly pick up where we left off if the job didn't finish.

	Note: we also added a ```main_multiproc.py``` version of this, which uses Python's multiprocessing package. It allows us to demonstrate how the job parallelizes on a PC, without needing a cluster and job scheduler.

### checkpointing

Checkpointing is a way that users handle the fact that they do not have unlimited access to the pool of resources provided by a cluster. No matter what system mediates your access, it will cut you off at a certain point, either by:

* Limiting how many cores you can use at the same time (or how many of a type)
* Limiting how long you can use those cores
* Limiting your network architectural prereqs (how tightly-knit your cores must be)
* Charging you impossible amounts of money in the commercial cloud

![Wisconsin](https://chtc.cs.wisc.edu/uw-research-computing/checkpointing) provides a great overview of checkpointing, though our example today isn't exit-driven but rather is managed on a rolling basis. 

### scavenger.slurm

This allows you to submit a whole bunch of jobs at once. Set your job array in ```scavenger.slurm```, and invoke this like ```sbatch scavenger.slurm 10```, which would try a 10-sided figure with 50 worker processes, those workers having indices 0 through 49.

#### What is slurm, and what is sbatch?

SLURM is the job-scheduling system used by Rice's NOTS cluster.

Job scheduling is a method of allowing many users to use a large pool of resources in an organized manner, in order to enable equitable access to these. It's essentially a traffic cop that tries to enable the most efficient use of the infrastructure so everyone can make the most of it.

Why is that important? The ratio of CPU hours used / CPU hours available is not super exciting to humans -- but then research computing isn't human (or it's all too human).

However, when you're waiting in traffic you can appreciate the significance of a broken traffic light. You know on a personal level what a half-kilometer of street undriven-upon means for a person's time when you're that person. And if you actually live in Houston, that's something that should be self-evident. But then infrastructure is something that civilians only notice when it breaks, and otherwise they complain about their taxes, or why they didn't know about why their taxes were important.

There are therefore different "queues," like the EZPass lane, the HOV lane, etc., that enable the more efficient use of these resources.

#### What is a scavenge queue?

Resource-hungry, inefficient apex predators, under conditions of scarcity or often just unevenness, fail. Scavengers, however, simply carrion.

SLURM provides settings that enable the optimization of your job on the infrastructure it's running on. But if you can manage your own job efficiently, like carpooling, you can make the most of these rules-based systems -- which is good for you and good for the system.

The Scavenge queue has a very short wall-time (the length that a job can run) but it can use a lot of cores and has a very short wait time.

The job in this repository uses that queue but its principle, of parameterizing a job as fully as possible, applies generally as a means of enabling scalability on any architecture.

#### What's next?

If you don't have the time to fully decompose your problem into a parameter space, then the points at which you'll hit sticking points usually, in well-developed languages like python, have in-built parallelization that will get you pretty far. Look for commands like "cores" or "processes" in the documentation. However, it's worth noting that these in-built parallelizations always plateau out at a certain point in terms of performance gains.

You might also, if you want to consider building out your parallelization on your own, look at -- and I'm only familiar with Python -- packages like: 

* MPI4py: https://mpi4py.readthedocs.io/en/stable/ (though I've hit memory leak issues here in passing varying arrays)
* Multiproc: https://docs.python.org/3/library/multiprocessing.html

------

Copyright John Connor Mulligan, 2023. Written for Rice University's Center for Research Computing.
