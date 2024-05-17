%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%% MiniZinc parametric model for FREEDA %%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%include "v0.1.dzn";
include "globals.mzn";

%%%%%%%%%%%%%%%%%%%%%%
%%%%% Parameters %%%%%
%%%%%%%%%%%%%%%%%%%%%%

enum CRes;
enum NRes;
enum Comps;
enum Flavs;
enum Nodes;
enum Res = C(CRes) ++ N(NRes);
array[Comps] of set of Flavs: Flav;
array[CompFlavs] of set of Comps: Uses;
set of Comps: mustComps;
array[CompFlavs] of set of Res: Req_cf = [
  {r | r in Res where comReq[cf,r] != worstBounds[r]} | cf in CompFlavs
];
array[Comps,Comps] of set of Res: Req_cc = array2d(Comps, Comps, [
  {r | r in Res where depReq[c1,c2,r] != worstBounds[r]} | c1 in Comps, 
                                                           c2 in Comps
]);
array[Nodes] of set of Res: Req_nr = [
  {r | r in Res where nodeCap[n,r] != worstBounds[r]} | n in Nodes
];
array[CompFlavs,Res] of int: comReq;
array[Comps,Comps,Res] of int: depReq;
array[Nodes0,Res] of int: nodeCap;
array[Nodes0,Nodes0,Res] of int: linkCap;
array[Nodes0,Res] of int: cost;
array[Nodes0,Res] of int: cons;
int: costWeight;
int: consWeight;
int: costBudget;
int: consBudget;
array[Comps, Flavs] of int: imp;

%%%%% Auxiliary parameters %%%%%

% I(c,f) is the row index of component c in flavour f in the deployment matrix.
function int: 
I(Comps: c, Flavs: f) = 
  sum (i in 1..c-1) (length(Flav[Comps[i]])) + arg_max([f = i | i in Flav[c]]);
set of int: Nodes0 = {0} union Nodes;
set of int: CompFlavs = 1..sum (c in Comps)( length(Flav[c]) );
int: MAX_BOUND;
array[Res] of 0..MAX_BOUND: bestBounds;
array[Res] of 0..MAX_BOUND: worstBounds;

%%%%%%%%%%%%%%%%%%%%%
%%%%% Variables %%%%%
%%%%%%%%%%%%%%%%%%%%%

% D[I(c,f),j] = 1 iff component c is deployed in flavour f on node j.
array [{0} union CompFlavs, Nodes0] of var 0..1: D;

% node[c] is the node where c is deployed, or node[c] = 0 if not deployed.
array [Comps] of var Nodes0: node; constraint node = [
  sum(i in Flav[c], j in Nodes)( j*D[I(c,i), j] ) | c in Comps
];

% Total cost of the deployment.
var int: totCost = sum(c in Comps, i in Flav[c], r in Req_cf[I(c,i)]) (
  comReq[I(c,i), r] * cost[node[c], r] * D[I(c,i), node[c]]
);

% Total energy consumption of the deployment.
var int: totCons = sum(c in Comps, i in Flav[c], r in Req_cf[I(c,i)])(
  comReq[I(c,i), r] * cons[node[c], r] * D[I(c,i), node[c]]
);

%%%%%%%%%%%%%%%%%%%%%%%
%%%%% Constraints %%%%%
%%%%%%%%%%%%%%%%%%%%%%%

% Zero values for D[0,j] and D[i,0].
constraint forall(j in Nodes0)( D[0,j] = 0 );
constraint forall(i in CompFlavs)( D[i,0] = 0 );

% Components that must be deployed
constraint forall (c in mustComps) (
  sum (i in Flav[c], j in Nodes)( D[i,j] ) > 0 /\ node[c] > 0
);

% Each component is deployed in at most one flavour, on at most one node
constraint forall(c in Comps) (
  sum(i in Flav[c], j in Nodes)( D[I(c,i), j] ) <= 1
);

% If component c is deployed in flavour i, all components used by c in that
% flavour must be deployed on some node
constraint forall(c in Comps, i in Flav[c], c1 in Uses[I(c,i)]) (
  sum(j in Nodes)( D[I(c,i), j] ) <=
  sum(i1 in Flav[c1], j1 in Nodes)( D[I(c1,i1), j1] )
);

% If component c deployed in flavour i requires a certain amount of resource r,
% then node c must have capacity for r
constraint forall(c in Comps, i in Flav[c], r in Req_cf[I(c,i)]) (
  if worstBounds[r] = 0 then
    comReq[I(c,i), r] * D[I(c,i), node[c]] <= nodeCap[node[c], r]
  else
    comReq[I(c,i), r] * D[I(c,i), node[c]] >= nodeCap[node[c], r]
  endif
);

% Each node j has a sufficient quantity of a certain resource r to meet the 
% demands of all the components deployed on it
constraint forall(j in Nodes, r in Req_nr[j] where r in CRes) (
  if worstBounds[r] = 0 then
    sum(c in Comps, i in Flav[c] where r in Req_cf[I(c,i)])
      (comReq[I(c,i), r] * D[I(c,i), j]) <= nodeCap[j,r]
  else
    sum(c in Comps, i in Flav[c] where r in Req_cf[I(c,i)])
      (comReq[I(c,i), r] * D[I(c,i), j]) >= nodeCap[j,r]
  endif
);

% Dependency requirements.
constraint forall(c in Comps, i in Flav[c], c1 in Uses[I(c,i)], 
                                             r in Req_cc[c,c1]) (
  if worstBounds[r] = 0 then
    depReq[c,c1,r] <= linkCap[node[c], node[c1], r]
  else
    depReq[c,c1,r] >= linkCap[node[c], node[c1], r]
  endif
);

% Budget requirements.
constraint totCost <= costBudget;
constraint totCons <= consBudget;

%%%%%%%%%%%%%%%%%%%%%
%%%%% Objective %%%%%
%%%%%%%%%%%%%%%%%%%%%

var int: obj = sum(c in Comps, i in Flav[c])(
  imp[c,i] * sum([D[I(c,i),j] | j in Nodes])
);
solve maximize obj;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%% Output formatting %%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

output [
  if fix(node[c]) > 0 then 
    "Component \(c) deployed in flavour \([Flavs[i] | i in Flav[c] where 
    D[I(c,i),node[c]] > 0][1]) on node \(Nodes[node[c]]).\n"
  else
    "Component \(c) not deployed.\n" 
  endif | c in Comps] ++ ["Objective value: \(obj)\n\tTotal cost: \(totCost)" ++
                                          "\n\tTotal consumption: \(totCons)"];
                                          