#ifndef PLANNER_WRAPPER_H_
#define PLANNER_WRAPPER_H_
#include <map>
#include <vector>
#include "search_space.h"
#include "aras_state.h"
#include "wa_star_search.h"

using namespace std;

class PlannerWrapper
{
	map<ArasState, State> memory;
	WAStarSearchEngine* planner;
public:
	void get_goals(set<ArasState>& goals);
	void expand(SearchSpace& search_space, SearchNode& node, int limit);
	void memorize(vector<const Operator*>& path);
	PlannerWrapper(WAStarSearchEngine* was) : planner(was){}
	virtual ~PlannerWrapper();
	map<ArasState, State>::iterator test(){
		return memory.begin();
	}
};

#endif /*PLANNER_WRAPPER_H_*/
