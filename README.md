---
title : diff2parse
author : Dillon Niederhut
---

## About

`diff2parse` is a Python wrapper for [FSL's probtrackx2](http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT/UserGuide#PROBTRACKX_-_probabilistic_tracking_with_crossing_fibres) that uses prior knowledge about the conservative evolution of mammalian brains to describe functional segments of the cerebral cortex in any clade of mammal.

This process requires [bedpostX](http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT/UserGuide#BEDPOSTX) output and 8 user defined binary masks for the following structures for each hemisphere :

1. amygdala
2. inferior colliculus
3. superior colliculus
4. globus pallidus
5. mammillothalamic tract
6. medial lemniscus
7. optic tract
8. putamen

unless the brain in question is human, in which case we recommend using standardized neuroanatomical atlases.

## Usage

Many of FSL's functions take > 10 parameters. To simplify function calls, these parameters have been moved to the options file. Edit the options file with the locations of the data, masks, and probtrackx2 options, either by editing the text file by hand, or by resetting values from the command line :

~~~
python diff2parse.py --reset --pairs <KEY> <VALUE>
~~~

then, parcellate the thalamic nuclei :

~~~
python diff2parse.py --parse-thalamus
~~~

finally, parcellate the cerebral cortex :

~~~
python diff2parse.py --parse-cortex
~~~

## Tips

* `diff2parse` expects that your shell has `$FSLDIR` in its environment and FSL's binaries in its search path.

* flagging `--dry-run` and `--verbose` together will print out the `diff2parse` FSL calls instead of calling them
