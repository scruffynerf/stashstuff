import os
import sys
import json

try:
    import stashapi.log as log
    from stashapi.tools import human_bytes
    from stashapi.types import PhashDistance
    from stashapi.stashapp import StashInterface
    from stashapi.stashbox import StashBoxInterface
except ModuleNotFoundError:
    print("You need to install the stashapp-tools (stashapi) python module. (CLI: pip install stashapp-tools)", file=sys.stderr)

# plugins don't start in the right directory, let's switch to the local directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))

if not os.path.exists("config.py"):
    with open("prescreen_defaults.py", 'r') as default:
        config_lines = default.readlines()
    with open("config.py", 'w') as firstrun:
        firstrun.write("from prescreen_defaults import *\n")
        for line in config_lines:
            if not line.startswith("##"):
                firstrun.write(f"#{line}")

import config

def configfile_edit(configfile, name: str, state: str):
    found = 0
    with open(configfile, 'r') as file:
        config_lines = file.readlines()
    with open(configfile, 'w') as file_w:
        for line in config_lines:
            if name == line.split("=")[0].strip():
                file_w.write(f"{name} = {state}\n")
                found += 1
            elif "#" + name == line.split("=")[0].strip():
                file_w.write(f"{name} = {state}\n")
                found += 1
            else:
                file_w.write(line)
        if not found:
            file_w.write(f"#\n{name} = {state}\n")
            found = 1
    return found

def exit_plugin(msg=None, err=None):
    if msg is None and err is None:
        msg = "plugin ended"
    output_json = {"output": msg, "error": err}
    print(json.dumps(output_json))
    sys.exit()

def get_ids(obj):
    ids = []
    for item in obj:
        ids.append(item['id'])
    return ids

def get_names(obj):
    names = []
    for item in obj:
        names.append(item['name'])
    return names

def parent_tag(tag_id):
    parenttagname = config.ratio_parent_name
    parent_tag_id = stash.find_tag(parenttagname, create=True).get("id")
    tag_update = {}
    tag_update["id"] = tag_id
    tag_update["parent_ids"] = parent_tag_id
    stash.update_tag(tag_update)
    return

def prescreen_all():
    fragment = """
        id
        tags {
           id
           }
        title
        phash
        oshash
    """
    found = stash.find_scenes(f={
	"stash_id": {
                      "value": "",
                      "modifier": "IS_NULL"
                },
        }, fragment=fragment)
    #	"tags": {
    #                  "value": alltags,
    #                  "modifier": "EXCLUDES"
    #            }
    total = len(found)
    #log.debug(f"found {total}")
    for count, scene in enumerate(found):
        #log.debug(scene)
        result = prescreen(scene)
        #log.debug(f"{scene['title']}")
        log.progress((1+count)/(total))
    return

def isBlank (myString):
    return not (myString and myString.strip())

def prescreen(scene):
    newtags = []
    phash = scene.get('phash')
    oshash = scene.get('oshash')
    title = scene.get('title')
    tags = get_ids(scene.get('tags'))
    log.debug(f"info = {phash} {oshash} {title}")
    #log.debug(f"info2 = {tags}")
    #filename = scene.get('filename')
    search = []
    if phash is not None and phash !="":
       search.append(phash)
    if oshash:
       search.append(oshash)
    if search != []:
        for item, endpoint in enumerate(stashboxes):
            if endpoint["endpoint"] == "https://metadataapi.net/graphql":
                continue
                ## tpdb doesn't work with the below, so we work around
                #log.debug(endpoint)
                #results = stash.stashbox_scene_scraper(scene.get('id'), item)
                #log.debug(results)
                #return
            if endpoint["noresult"] in tags:
               continue
            if endpoint["oneresult"] in tags:
               continue
            if endpoint["manyresult"] in tags:
               continue
            stashboxconnection = StashBoxInterface(endpoint)
            try:
                count = stashboxconnection.find_scenes_count({
                'fingerprints': {
		 	'value': search,
		 	"modifier": "INCLUDES"
			}
                })
                log.info(f"found {count} @ {endpoint['name']} for {title}")
                if count == 0:
                   newtags.append(endpoint["noresult"])
                elif count == 1:
                   newtags.append(endpoint["oneresult"])
                else:
                  newtags.append(endpoint["manyresult"])
            except:
                log.error(f"error calling {endpoint['name']} for {title}")

        #elif title is not None or filename is not None:
            # perform search for title or filename here
            # and update tags accordingly
        stash.update_scenes({
                'ids': [scene['id']],
                'tag_ids': {
                    'mode': 'ADD',
                    'ids': newtags
                }
              })
    return

global stash
global stashboxes
global stashboxconnections
global alltags

json_input = json.loads(sys.stdin.read())
FRAGMENT_SERVER = json_input["server_connection"]
PLUGIN_ARGS = False
HOOKCONTEXT = False
alltags = config.alltags
enabled = config.enabled

if not enabled:
   exit_plugin("Prescreening plugin disabled")

try:
        PLUGIN_ARGS = json_input['args']["mode"]
except:
        pass

if PLUGIN_ARGS:
        log.debug("--Starting Plugin 'Prescreening'--")
        if "prescreen_all" in PLUGIN_ARGS:
            log.info("Catching up with Prescreening tagging on older files")
            stash = StashInterface(FRAGMENT_SERVER)
            stashboxes = stash.get_stashbox_connections()
            if len(alltags) != len(stashboxes)*3:
                for item, endpoint in enumerate(stashboxes):
                   endpoint_name = endpoint["name"]
                   noresult = f'{endpoint_name} - no result'
                   stashboxes[item]["noresult"] = stash.find_tag(noresult, create=True).get("id")
                   alltags.append(stashboxes[item]["noresult"])
                   oneresult = f'{endpoint_name} - single'
                   stashboxes[item]["oneresult"] = stash.find_tag(oneresult, create=True).get("id")
                   alltags.append(stashboxes[item]["oneresult"])
                   manyresult = f'{endpoint_name} - multi'
                   stashboxes[item]["manyresult"] = stash.find_tag(manyresult, create=True).get("id")
                   alltags.append(stashboxes[item]["manyresult"])
                configfile_edit("config.py", "alltags", str(alltags))
            else:
                for item, endpoint in enumerate(stashboxes):
                   stashboxes[item]["noresult"] = alltags[item*3]
                   stashboxes[item]["oneresult"] = alltags[1+(item*3)]
                   stashboxes[item]["manyresult"] = alltags[2+(item*3)]
            prescreen_all() #loops thru all scenes, and tag
        exit_plugin("Prescreening plugin finished")

try:
        HOOKCONTEXT = json_input['args']["hookContext"]
except:
        exit_plugin("Prescreening hook: No hook context")

log.debug("--Starting Hook 'Prescreening'--")
stash = StashInterface(FRAGMENT_SERVER)
stashboxes = stash.get_stashbox_connections()
if len(alltags) != len(stashboxes)*3:
                for item, endpoint in enumerate(stashboxes):
                   endpoint_name = endpoint["name"]
                   noresult = f'{endpoint_name} - no result'
                   stashboxes[item]["noresult"] = stash.find_tag(noresult, create=True).get("id")
                   alltags.append(stashboxes[item]["noresult"])
                   oneresult = f'{endpoint_name} - single'
                   stashboxes[item]["oneresult"] = stash.find_tag(oneresult, create=True).get("id")
                   alltags.append(stashboxes[item]["oneresult"])
                   manyresult = f'{endpoint_name} - multi'
                   stashboxes[item]["manyresult"] = stash.find_tag(manyresult, create=True).get("id")
                   alltags.append(stashboxes[item]["manyresult"])
                configfile_edit("config.py", "alltags", str(alltags))
else:
                for item, endpoint in enumerate(stashboxes):
                   stashboxes[item]["noresult"] = alltags[item*3]
                   stashboxes[item]["oneresult"] = alltags[1+(item*3)]
                   stashboxes[item]["manyresult"] = alltags[2+(item*3)]
sceneID = HOOKCONTEXT['id']
scene = stash.find_scene(sceneID)
#log.debug(HOOKCONTEXT)
if scene['stash_ids']:
       # add cleanup of old prescreen tags
       stash.update_scenes({
                'ids': [scene['id']],
                'tag_ids': {
                    'mode': 'REMOVE',
                    'ids': alltags
                }
              })
       exit_plugin("has stashid already, prescreen tags cleaned")
else:
       if HOOKCONTEXT['type'] == "Scene.Create.Post":
           #log.debug(scene)
           prescreen(scene)
exit_plugin()

