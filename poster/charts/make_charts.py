import json, collections
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+"/"; O=R+"poster/charts/"
INK="#171321"; GR="#73758D"; GR2="#A6A6BA"; P="#7062CD"; LP="#B3A2FF"; VP="#EEEAFC"; T="#66CBBD"; DP="#3F3590"; GRID="#E7E4F5"
plt.rcParams.update({"font.family":["Arial","DejaVu Sans"],"text.color":INK,"axes.labelcolor":GR,"xtick.color":GR,"ytick.color":GR,"figure.facecolor":"white","axes.facecolor":"white","savefig.facecolor":"white"})
def style(ax,ygrid=True):
    for s in ax.spines.values(): s.set_visible(False)
    ax.spines["bottom"].set_visible(True); ax.spines["bottom"].set_color(GR2)
    ax.tick_params(axis="x",length=0,labelsize=20,labelcolor=INK); ax.tick_params(axis="y",length=0,labelsize=20,labelcolor=GR)
    ax.yaxis.grid(ygrid,color=GRID,lw=1); ax.set_axisbelow(True)
def save(fig,n):
    fig.savefig(O+n,dpi=300,facecolor="white",transparent=False); plt.close(fig)


import re
md=open(R+"results/reports/corrected_view.md").read()
partA=md.split("## Part A")[1].split("## Part B")[0]
froz={}
for g in re.split(r"### ",partA)[1:]:
    for line in g.splitlines():
        m=re.match(r"\| (cleaning|analysis|reporting) \| (.+?) \(`.`\) \| (\d)/4 ",line)
        if m: froz.setdefault((g[:5],m.group(2)),{})[m.group(1)]=int(m.group(3))
models=[("Sonnet 4.6","Origi"),("Nova Pro","Origi"),("gpt-oss-120b","Origi"),("Kimi K3","Price"),("GLM 5","Price")]
st=["cleaning","analysis","reporting"]
vals={m:[froz[(g,m)][s] for s in st] for m,g in models}; print(vals)
fig,ax=plt.subplots(figsize=(10,5.5)); style(ax)
w=0.27; cols=[LP,P,DP]
for i,(m,_) in enumerate(models):
    for j,s in enumerate(st):
        x=i+(j-1)*w; v=vals[m][j]
        if m=="GLM 5" and s=="analysis": v=4  # after bug fix: shown as a normal bar
        ax.bar(x,v,w*0.92,color=cols[j],zorder=3)
        ax.text(x,v+0.08,str(v),ha="center",va="bottom",fontsize=20,fontweight="bold",color=INK,zorder=4)
ax.set_xticks(range(5)); ax.set_xticklabels([m for m,_ in models]); ax.set_ylim(0,4.7); ax.set_yticks(range(5)); ax.set_xlim(-0.55,4.55)
fig.legend(handles=[Patch(color=LP,label="Cleaning"),Patch(color=P,label="Analysis"),Patch(color=DP,label="Reporting")],loc="upper center",bbox_to_anchor=(0.55,1.0),ncol=3,frameon=False,fontsize=20,handlelength=1.2,columnspacing=1.5,labelspacing=0.3)
fig.subplots_adjust(left=.07,right=.995,bottom=.1,top=.88); save(fig,"q1_stage_success.png")

# ---- Q2
q=json.load(open(R+"results/processed/corrected_q2.json"))["model_groups"]
def g(grp,key,view):
    d=q[grp][key][view]; return d["n_feasible"],d["n"]
data=[]
for grp in ["original_4096","price_matched_16384"]:
    for key,kl in [("single_model_main_grid","Single-\nmodel"),("cross_model_main_grid","Mixed")]:
        data.append((kl,g(grp,key,"frozen_v3"),g(grp,key,"corrected_v3")))
print(data)

# ---- Q3
r=json.load(open(R+"results/processed/router_relabel_posthoc.json"))["model_groups"]
meths=[("router","Router",P),("d_always_tie","No\nchange",LP),("a_always_less","Worse",LP),("b_always_more","Better",LP)]
fig,ax=plt.subplots(figsize=(10,5.5)); style(ax)
for gi,(grp,lab) in enumerate([("original_4096","Group 1"),("price_matched_16384","Group 2")]):
    m=r[grp]["validators"]["v3_primary"]["corrected"]["slices"]["pooled"]["methods"]
    base=gi*4.6
    for j,(key,nm,col) in enumerate(meths):
        k,n=m[key]["k"],m[key]["n"]; x=base+j*0.95
        v=100*k/n; ax.bar(x,v,0.8,color=col,zorder=3)
        ax.text(x,v+1,f"{v:.0f}%",ha="center",va="bottom",fontsize=20,fontweight="bold",color=INK)
        ax.text(x,-2,nm,ha="center",va="top",fontsize=20,color=P if key=="router" else INK,fontweight="bold" if key=="router" else "normal",linespacing=1.05)
    ax.text(base+1.425,-16,lab,ha="center",va="top",fontsize=20,color=P,fontweight="bold")
ax.set_xticks([]); ax.set_xlim(-0.5,7.95); ax.set_ylim(0,65); ax.set_yticks(range(0,61,20)); ax.set_yticklabels([f"{i}%" for i in range(0,61,20)])
fig.subplots_adjust(left=.09,right=.995,bottom=.26,top=.97); save(fig,"q3_router_vs_baselines.png")

# ---- Q2 final-only variant (no original/adjusted comparison)
fig,axs=plt.subplots(1,2,figsize=(10,5.5),sharey=True)
for ax,(grp_i,lab) in zip(axs,[(0,"Group 1"),(2,"Group 2")]):
    style(ax)
    for x,(kl,o,c),col in zip([0,1],data[grp_i:grp_i+2],[LP,P]):
        k,n=c; v=100*k/n; ax.bar(x,v,0.55,color=col,zorder=3)
        ax.text(x,v+1.2,f"{v:.0f}%",ha="center",va="bottom",fontsize=22,fontweight="bold",color=INK)
    ax.set_xticks([0,1]); ax.set_xticklabels(["Single\nmodel","Mixed\nmodels"]); ax.set_xlim(-0.6,1.6)
    ax.set_ylim(0,62); ax.set_yticks(range(0,61,20)); ax.set_yticklabels([f"{i}%" for i in range(0,61,20)])
    ax.set_title(lab,fontsize=22,color=P,fontweight="bold",pad=6)
axs[0].set_ylabel("Workflow success rate",fontsize=18)
fig.text(0.55,0.015,"Single model: 12 tested paths per group  |  Mixed models: 96 per group",ha="center",va="bottom",fontsize=15,color=GR)
fig.subplots_adjust(left=.11,right=.995,bottom=.25,top=.88,wspace=.08); save(fig,"q2_single_vs_mixed_final_only.png")

cq=json.load(open(R+"results/processed/corrected_q2.json"))["model_groups"]
# ---- Cost + success, both groups: same success at very different cost; switching models is not always worth it
def pagg(grp):
    ag=collections.defaultdict(lambda:[0,0,0.0])
    for r_ in cq[grp]["project_path_outcomes_main_grid"]:
        a_=ag[r_["path_id"]]; a_[0]+=r_["corrected_v3"]=="feasible"; a_[1]+=1; a_[2]+=r_["corrected_cost_usd"]
    return ag
ARR=" → "
blocks=[("Group 1",pagg("original_4096"),[("C-C-B","gpt-oss"+ARR+"gpt-oss"+ARR+"Nova"),("A-C-B","Sonnet"+ARR+"gpt-oss"+ARR+"Nova"),("A-A-A","Sonnet only")]),
        ("Group 2",pagg("price_matched_16384"),[("C-C-C","GLM only"),("C-A-C","GLM"+ARR+"Sonnet"+ARR+"GLM"),("A-A-A","Sonnet only")])]
fig,ax=plt.subplots(figsize=(10,5.5)); style(ax,ygrid=False)
ax.xaxis.grid(True,color=GRID,lw=1); ax.yaxis.grid(False)
y=8.0; ticks=[]; labs=[]
for gname,ag,items in blocks:
    ax.text(-0.0,y+0.2,gname,transform=ax.get_yaxis_transform(),ha="right",va="center",fontsize=21,fontweight="bold",color=P)
    # place header in the left label area
    y-=1
    best=max(ag[p][0] for p,_ in items)
    for p,lab in items:
        k,n,c=ag[p]; cost_=c/n
        ax.barh(y,cost_,0.66,color=P if k==best else LP,zorder=3)
        ax.text(cost_+0.006,y,f"${cost_:.2f}  ·  {k}/4",va="center",fontsize=20,fontweight="bold" if k==best else "normal",color=INK)
        ticks.append(y); labs.append(lab); y-=1
    y-=0.6
ax.set_yticks(ticks); ax.set_yticklabels(labs,fontsize=18); ax.tick_params(axis="y",labelcolor=INK)
ax.set_ylim(y+0.6,8.8); ax.set_xlim(0,0.26); ax.set_xticks([0,.1,.2]); ax.set_xticklabels(["$0","$0.10","$0.20"])
ax.set_xlabel("Average cost per workflow run",fontsize=17,color=GR,labelpad=6)
fig.text(0.6,0.012,"x/4 = projects where all 3 steps passed the fixed checks",ha="center",va="bottom",fontsize=15,color=GR)
fig.subplots_adjust(left=.36,right=.985,bottom=.2,top=.97); save(fig,"cost_vs_success_two_groups.png")
print({g:[(p,ag[p][0],round(ag[p][2]/4,3)) for p,_ in it] for g,ag,it in blocks})
