//#include<bits/stdc++.h>
#include <cstdio>
#include <iostream>
#include <vector>
#include <algorithm>
#include <cstring>
#include <string>
using namespace std;
int kp=9;
vector<int>E1[200005];
vector<int>E2[200005];
//double Mat[4005][4005];
int N1,N2;
int Match[5005];
double finalres;
double alpha;
struct Point{
	int a[9];
	bool operator<(const Point& p)const{
		for(int i=0;i<9-1;i++)
			if(a[i]!=p.a[i])return a[i]<p.a[i];
		return a[8]<p.a[8];
	}
	bool operator!=(const Point& p)const{
		for(int i=0;i<9;i++)
			if(a[i]!=p.a[i])return 1;
		return 0;
	}
};
Point p1[5005];
Point p2[5005];
const int MAXN = 5005;
const int INF = 0x3f3f3f3f;
double weight[MAXN][MAXN];
double eleft[MAXN];
double eright[MAXN];
bool okleft[MAXN];
bool okright[MAXN];
int match[MAXN];
double slack[MAXN];
int N;
double ans=0;
int ansk=0;
bool dfs(int lnode){
    okleft[lnode] = true;
    for (int rnode = 0; rnode < N; ++rnode) {
        if (okright[rnode]) continue;
        double gap = eleft[lnode] + eright[rnode] - weight[lnode][rnode];
        if (abs(gap) <= 1e-7) {
            okright[rnode] = true;
            if (match[rnode] == -1 || dfs( match[rnode] )) {
                match[rnode] = lnode;
                return true;
            }
        } else slack[rnode] = min(slack[rnode], gap);
    }
    return false;
}
double KM(){
    memset(match, -1, sizeof match);
    fill(eright,eright+MAXN,0);
    for (int i = 0; i < N; ++i) {
        eleft[i] = weight[i][0];
        for (int j=1;j<N;++j)eleft[i] = max(eleft[i], weight[i][j]);
    }
    for (int i = 0; i < N; ++i) {
        fill(slack, slack + N, INF);
        while (1) {
        	for(int i=0;i<=N;i++)okleft[i]=okright[i]=0;
        	memset(okleft,0,sizeof(okleft));
        	memset(okright,0,sizeof(okright));
            if (dfs(i)) break;
            double d = INF;
            for (int j = 0; j < N; ++j) if (!okright[j]) d = min(d, slack[j]);
            for (int j = 0; j < N; ++j) {
                if (okleft[j]) eleft[j] -= d;
                if (okright[j]) eright[j] += d;
                else slack[j] -= d;
            }
        }
    }
    double res=0;
    for(int i=0;i<N;++i)res+=weight[match[i]][i];
    return res;
}
double nodeKernel(int i,int j){
	int a,b;a=b=1;
	for(int k=0;k<kp;k++){
		a+=min(p1[i].a[k],p2[j].a[k]);
		b+=max(p1[i].a[k],p2[j].a[k]);
	}
	return a*1.0/b;
}
//double calc(int root1,int root2){
void calc(int root1,int root2){
//	printf("%d %d %d %f\n",root1,root2,ansk,ans);
	vector<int>floor1;
	vector<int>floor2;
	if(root1!=-1)for(int i=0;i<E1[root1].size();i++)floor1.push_back(E1[root1][i]);
	if(root2!=-1)for(int i=0;i<E2[root2].size();i++)floor2.push_back(E2[root2][i]);
	if(floor1.size()==0&&floor2.size()==0)return;
	int n;
	n=N=max(floor1.size(),floor2.size());
	ansk+=n;
	bool issame=1;
	if(floor1.size()!=floor2.size())issame=0;
	vector<pair<Point,int> >va,vb;
	if(issame){
		for(int i=0;i<floor1.size();i++)va.push_back({p1[floor1[i]],floor1[i]});
		for(int i=0;i<floor2.size();i++)vb.push_back({p2[floor2[i]],floor2[i]});
		sort(va.begin(),va.end());
		sort(vb.begin(),vb.end());
		for(int i=0;i<floor1.size();i++)
			if(va[i].first!=vb[i].first)issame=0;
	}
	if(issame){
		for(int i=0;i<n;i++)ans+=nodeKernel(va[i].second,vb[i].second);
//		for(int i=0;i<n;i++)calc(floor1[i],floor2[i]);
		for(int i=0;i<n;i++)calc(va[i].second,vb[i].second);
	}else{
		for(int i=0;i<n;i++)for(int j=0;j<n;j++)weight[i][j]=0;
		for(int i=0;i<floor1.size();i++)for(int j=0;j<floor2.size();j++)weight[i][j]=nodeKernel(floor1[i],floor2[j]);
		ans+=KM();
		vector<int>matchL;
		vector<double>res;
		for(int i=0;i<n;i++)matchL.push_back(match[i]);
		for(int i=0;i<n;i++)res.push_back(0);
		for(int i=0;i<n;i++)res[matchL[i]]=weight[match[i]][i];
		for(int i=0;i<n;i++){
			if(i>=(int)floor2.size()){
				calc(floor1[matchL[i]],-1);
			}else if(matchL[i]>=(int)floor1.size()){
				calc(-1,floor2[i]);
				continue;
			}else{
				Match[floor1[matchL[i]]]=floor2[i];
				calc(floor1[matchL[i]],floor2[i]);
			}
		}
	}
}

void solve(){
	for(int i=0;i<N1;i++)Match[i]=-1;
	finalres=0;
	calc(0,0);
//	cout<<ans<<endl;
//	cout<<ansk<<endl;
	cout<<ans/ansk<<endl;
}
int main(){
	cin.tie(0);ios::sync_with_stdio(false);
	int nedge,tu,tv;
	cin>>N1>>nedge;
	while(nedge--){cin>>tu>>tv;E1[tu].push_back(tv);}
	cin>>N2>>nedge;
	while(nedge--){cin>>tu>>tv;E2[tu].push_back(tv);}
	for(int i=0;i<N1;i++)
		for(int j=0;j<kp;j++)
			cin>>p1[i].a[j];
	for(int i=0;i<N2;i++)
		for(int j=0;j<kp;j++)
			cin>>p2[i].a[j];
	solve();
    return 0;	
}
