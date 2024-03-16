import json
import os
import sys
import graderUtil

# a dict stores the final result
task_result = {
    "ini_cost": -1,
    "best_cost": -1,
    "locations": []
} 

#######################################################################
# read task file content
task_file = sys.argv[1]
task_content = graderUtil.load_task_file(task_file)
if task_content:
    print(task_content)
# BEGIN_YOUR_CODE

#task_result["ini_cost"] = 15
#task_result["best_cost"] = 9
#task_result["locations"] = [[1,2]]

#task_result["best_cost"] = 7
#task_result["locations"] = [[2,1]]


#task_result["ini_cost"] = 9
#task_result["best_cost"] = 7
#task_result["locations"] = [[0,1],[1,2]]

task_result["best_cost"] = 5
task_result["locations"] = [[1,0],[2,1]]


# END_YOUR_CODE
#######################################################################

# output your final result
print(json.dumps(task_result))