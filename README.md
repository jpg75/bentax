# bentax
An Agent-Based simulation model for tax evasion and tax compliance.

In this model, taxpayers are heterogeneous and intereact with eachothers in a public (it is actually a 'common') good game 
context. Heterogeneity has been introduced by designing the agents like simple heuristics and they can belong to distinct 
cross-sectional types: employee and self-employed. Agents are free to dynamically switch between heuristics and cross 
sectional types in order to satisfy their needs.
The network of agents is also dynamic: agents can join or leave (die).

This code is in Python and designed to run using AESOP-ACP simulator: http://aesop-acp.sourceforge.net/ 
therfore, you first need to dowload and install AESOP-ACP. 
The simulator docs and howtos are provided at the simulator homepage (the previous url).

Configuration files and runner file (bash) for the rimulations are provided in the repo. Especially the runner file might require editing to fit specific installation details.
Everything has been design and coded on Unix.

