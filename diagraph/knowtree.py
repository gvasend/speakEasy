
"""
Implement a knowledge tree to guide Conv AI to find intent and the solution that goes with intent

KBA to prompt
KBA     instance_id    value   factor
111     app         NeL     0.2
111

instance_id    Context     Prompt                  Type        switch_context      required
app              {"SolutionID":"sol001", "instance_id":"app", "Value":"nel", "Correlation":0.5},   root        Which app?              Combo       yes                 no
uic         root        What is you UIC?        string      no                  yes
url         nel         What url?               string      no                  yes
course      nel         What course             string      no                  no
edipi       root        What is your EDIPI      string      no                  yes
issue       nel         What is your NeL issue? spanless    yes                 yes
sshot       ticket      Do you have any screen shots to add?    upload


Impact what questions to ask:

value of earlier prompt
user attribute

"""

import neo4j

from neo4j import GraphDatabase
import uuid

driver = GraphDatabase.driver("neo4j://localhost:7687",
                              auth=("neo4j", "password"))

context_lst = ['root', 'nel', 'other', 'ticket']
context = 'root'

solution_to_prompt_lst = [
        {"SolutionID":"sol1", "instance_id":"app", "Value":"nel", "Eliminate":0.98},
        {"SolutionID":"sol1", "instance_id":"nel_url", "Value":"ashore", "Eliminate":0.5},
        {"SolutionID":"sol1", "instance_id":"sol1-sol2", "Value":"finding", "Eliminate":0.5},
        {"SolutionID":"sol1", "instance_id":"nel_issue", "Value":"sol001Problem", "Eliminate":0.95},
        
        {"SolutionID":"sol2", "instance_id":"app", "Value":"nel", "Eliminate":0.98},
        {"SolutionID":"sol2", "instance_id":"nel_url", "Value":"ashore", "Eliminate":0.5},
        {"SolutionID":"sol2", "instance_id":"sol1-sol2", "Value":"process", "Eliminate":0.5},
        {"SolutionID":"sol2", "instance_id":"nel_issue", "Value":"sol002Problem", "Eliminate":0.95},

        {"SolutionID":"sol4", "instance_id":"app", "Value":"nel", "Eliminate":0.98},
        {"SolutionID":"sol4", "instance_id":"nel_url", "Value":"afloat", "Eliminate":0.5},
        {"SolutionID":"sol4", "instance_id":"nel_issue", "Value":"sol004Problem", "Eliminate":0.95},
        
        {"SolutionID":"sol5", "instance_id":"app", "Value":"nel", "Eliminate":0.98},
        {"SolutionID":"sol5", "instance_id":"nel_url", "Value":"ashore", "Eliminate":0.5},
        {"SolutionID":"sol5", "instance_id":"nel_issue", "Value":"sol005Problem", "Eliminate":0.95},
        
        {"SolutionID":"sol6", "instance_id":"app", "Value":"nel", "Eliminate":0.98},
        {"SolutionID":"sol6", "instance_id":"nel_url", "Value":"afloat", "Eliminate":0.5},
        {"SolutionID":"sol6", "instance_id":"nel_issue", "Value":"sol006Problem", "Eliminate":0.95},

        {"SolutionID":"sol3", "instance_id":"app", "Value":"other", "Eliminate":0.98},
        {"SolutionID":"sol3", "instance_id":"other_issue", "Value":"sol003Problem", "Eliminate":0.95},
        
        {"SolutionID":"sol7", "instance_id":"app", "Value":"other", "Eliminate":0.98},
        {"SolutionID":"sol7", "instance_id":"other_issue", "Value":"sol007Problem", "Eliminate":0.95},
        
        {"SolutionID":"ticket", "instance_id":"uic", "Value":"other", "Eliminate":0.98},
        {"SolutionID":"ticket", "instance_id":"nel_url", "Value":"nel", "Eliminate":0.5},
        {"SolutionID":"ticket", "instance_id":"nel_course", "Value":"sol003Problem", "Eliminate":0.95},
    ]

prompt_lst = [
      {"instance_id":"app",    "Prompt":"Which app is this regarding?", "Type":"workflow:promptApp", "Switch":"yes", "Context":"root", "Required":"yes"},
      {"instance_id":"sol1-sol2",    "Prompt":"Are you having a problem knowing how to search for a course or actually finding it", "Type":"combo", "Switch":"yes", "Context":"nel", "Required":"yes", "Values":"finding;searching"},
      {"instance_id":"uic",    "Prompt":"What is your UIC?", "Type":"string", "Switch":"no", "Context":"root", "Required":"yes"},
      {"instance_id":"nel_url",    "Prompt":"What url are you using?", "Type":"url", "Switch":"yes", "Context":"nel", "Required":"yes"},
      {"instance_id":"nel_course", "Prompt":"Which course is this regarding?", "Type":"workflow:getCourse", "Switch":"no", "Context":"nel", "Required":"yes"},
      {"instance_id":"edipi",    "Prompt":"Please enter your edipi", "Type":"workflow:getUserDetail", "Switch":"no", "Context":"root", "Required":"yes", },
      {"instance_id":"nel_issue",    "Prompt":"What is your Navy eLearning Issue?", "Type":"entity:courseIssueType", "Switch":"yes", "Context":"nel", "Required":"yes"},
      {"instance_id":"other_issue",    "Prompt":"Please describe your issue?", "Type":"worklow:KBASearch", "Switch":"yes", "Context":"other", "Required":"yes"},
      {"instance_id":"sshot",    "Prompt":"Do you want to add a screen shot?", "Type":"workflow:appendFile", "Switch":"no", "Context":"ticket", "Required":"yes"}
    ]

# check if a solution is blocked by a bound prompt
# match path=(s:Solution{instance_id:"sol5"})-[r1:SUPPORTS]-(p1:Prompt)-[r2:VALUE]-(c:Conversation {instance_id:"35a5447a-4cbb-46b8-aa2a-148b5d59337a"}) WHERE r1.value<>r2.value return s,p1

prompt_dct = {}
cypher_results = []

def cypher(tx,query):
    global cypher_results
    print('cypher:',query)
    cypher_results = [record['n'] for record in tx.run(query)]

def create_node(tx,nodeID,nodeType,properties=None):
    props_str = ""
    if properties:
        for prop in properties:
            prop_str = ', %s: "%s"' % (prop, properties[prop])
            props_str += prop_str
        print(props_str)
    query = ("MERGE (a:%s {instance_id: $name %s}) " % (nodeType, props_str))
    tx.run(query, name=nodeID, label=nodeType)

def create_contexts(tx):
    for context in context_lst:
        create_node(tx, context, 'Context')

def create_solutions(tx):
    create_node(tx, 'ticket', 'Solution')
    for sol in range(20):
        sol_id = "sol%s" % sol
        create_node(tx, sol_id,'Solution')

def create_prompt(tx,prompt):
    create_node(tx, prompt['instance_id'], 'Prompt', properties=prompt)

def create_prompts(tx):
    for prompt in prompt_lst:
        create_prompt(tx,prompt)
        
def link_prompts(tx):
    print('link_prompts')
    for s2p in solution_to_prompt_lst:
        sol = s2p['SolutionID']
        prompt = s2p['instance_id']
        value = s2p['Value']
        impact = s2p['Eliminate']
        cypher(tx,'MATCH (p:Prompt{instance_id: "%s"}),(s:Solution{instance_id: "%s"}) MERGE (p)-[:SUPPORTS  {value: "%s", impact: %f}]->(s)' % (prompt,sol,value,impact))
        
def link_contexts(tx):
    for context in context_lst:
        cypher(tx, 'MATCH (c:Context{instance_id: "%s"}), (p:Prompt{Context:"%s"}) MERGE (c)-[:CONTAINS]->(p)' % (context, context))


def collect_data(prompts):
    for prompt in prompts:
        if prompt['Required']:
            ask(prompt)
    
def prompt(aPrompt):
    value = ask(aPrompt)
    if switching(aPrompt):
        context = value
    return value

def ask(prompt):
    print('[[[',prompt,']]]')
    print('%s: ' % prompt['Prompt'])
    if prompt not in prompt_dct:
        response = input()
        response = map_response(prompt,response)
        store_prompt(prompt,response)
        
def map_response(prompt,input):
    if prompt['Type'] == 'entity:courseIssueType':
        return "sol005Problem"
    return input
        

def store_prompt(prompt,value):
    global prompt_dct, context
    write_cypher('MATCH (c:Conversation {instance_id: "%s"}), (p:Prompt {instance_id: "%s"}) MERGE (c)-[v:VALUE {value: "%s"}]->(p)' % (convo['instance_id'],prompt['instance_id'],value))
    if prompt['Switch'] == 'yes':
        context = value
    prompt_dct[prompt['instance_id']] = value


def switch_context(prompt):
    if prompt['switch_context']:
        return True
    return False

def get_prompts(tx, context):
    global context_prompts
    query = ('MATCH (p:Prompt) where p.Context = $context' ' RETURN p')
    context_prompts = [record['p'] for record in tx.run(query, context=context)]

# match (p:Prompt)-[r:SUPPORTS]-(s:Solution)-[r1:SUPPORTS]-(:Prompt)-[r2:VALUE]-(:Conversation) WHERE r1.value=r2.value 

def get_all_prompts(tx):
    global context_prompts
    print('getting all prompts')
    query = ('MATCH (p:Prompt {Switch:"yes"})-[]->(s:Solution) RETURN p,count(s) ORDER by count(s) DESC ')
    context_prompts = [(record['count(s)'],record['p']) for record in tx.run(query)]
    
def get_unbound_prompts(tx, convo_id):
    global context_prompts
    print('find unbound prompts')
    num_bound_prompts = [record['count(p)'] for record in tx.run('MATCH (c:Conversation {instance_id: "%s"})-[:VALUE]-(p:Prompt) return count(p)' % (convo_id))][0]
    query = ('match (p:Prompt)-[r:SUPPORTS]-(s:Solution)-[r1:SUPPORTS]-(p1:Prompt)-[r2:VALUE]-(c:Conversation {instance_id:"%s"}) WHERE NOT (p)-[]-(c) AND r1.value=r2.value return p , count(s) ORDER by count(s) DESC' % (convo_id))
    print(query)
    context_prompts = [(record['count(s)'],record['p']) for record in tx.run(query)]
    print('unbound:')
    for record in context_prompts:
        print('unbound_prompts',record[0],record[1]['instance_id'])
    if num_bound_prompts < 1:
        print('no unbound prompts, get all prompts')
        get_all_prompts(tx)
        print('#prompts:',len(context_prompts))

def diagnose():
    global context
    more = True

    while(more):
        with driver.session(database="neo4j") as session:
            session.execute_read(get_unbound_prompts, convo['instance_id'])
        print('context:',context)
        data_prompts = [prompt[1] for prompt in context_prompts if prompt[1]['Switch'] == 'no']
        switch_prompts = [prompt[1] for prompt in context_prompts if prompt[1]['Switch'] == 'yes']
        print('data:',data_prompts)
        print('switch:',switch_prompts)
        print('prompt for context prompts')
        if len(switch_prompts) < 1:
            more = False
            print('have solution')
        else:
            collect_data(switch_prompts[:1])
            input('Continue?')

def write_cypher(query):
    with driver.session(database="neo4j") as session:
        session.execute_write(cypher, query)

def read_cypher(query):
    with driver.session(database="neo4j") as session:
        session.execute_read(cypher, query)

def create_graph():
    with driver.session(database="neo4j") as session:
        session.execute_write(create_solutions)
        session.execute_write(create_prompts)
        session.execute_write(link_prompts)
        session.execute_write(create_contexts)
        session.execute_write(link_contexts)


def create_conversation():
    global convo
    convo = uuid.uuid4()
    write_cypher('CREATE (n:Conversation {instance_id: "%s"}) RETURN n' % convo)
    convo = cypher_results[0]
    print('convo:',convo)

create_graph()
create_conversation()
diagnose()

driver.close()

print('prompt_dct',prompt_dct)
