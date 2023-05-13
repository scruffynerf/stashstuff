import os
import sys
import json

try:
    import stashapi.log as log
    from stashapi.stashapp import StashInterface
except ModuleNotFoundError:
    print("You need to install the stashapp-tools (stashapi) python module. (CLI: pip install stashapp-tools)", file=sys.stderr)

# plugins don't start in the right directory, let's switch to the local directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))

if not os.path.exists("config.py"):
    with open("dupetitle_defaults.py", 'r') as default:
        config_lines = default.readlines()
    with open("config.py", 'w') as firstrun:
        firstrun.write("from dupetitle_defaults import *\n")
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

def dupefindall():
    filter = {}
    filterlimits = {}
    filterlimits["per_page"] = -1
    found = stash.find_scenes(filter, filterlimits, fragment="id title url stash_ids {stash_id}")
    total = len(found)
    for count, scene in enumerate(found):
       #log.debug(f"{scene['id']} - {scene['title']}")
       #checktitle(scene)
       checkstashid(scene)
       checkurl(scene)
       log.progress((1+count)/total)

def checktitle(scene):
    # if no title - leave
    if not scene['title']:
       log.debug(f"Scene {scene['id']} has no title")
       return
    scene = stash.find_scene(scene['id'])
    if not scene:
       log.debug("Scene issue")
       return
    existing_tags = get_names(scene.get("tags"))
    dupetitle_id = stash.find_tag(config.dupetitle_tagname, create=True).get("id")

    # check number of scenes with this title

    # add title filter
    filtertitle = {}
    filtertitle["value"] = scene['title'].strip()
    filtertitle["modifier"] = "EQUALS"
    filter = {}
    filter["title"] = filtertitle
    filterlimits = {}
    filterlimits["per_page"] = 5

    numberofscenes = len(stash.find_scenes(filter, filterlimits, fragment="id"))

    # if dupe tagged now and number = 1, remove
    if numberofscenes == 1 and config.dupetitle_tagname in existing_tags:
        stash.update_scenes({
            'ids': [scene['id']],
            'tag_ids': {
                'mode': 'REMOVE',
                'ids': [dupetitle_id]
            }
        })
        log.info(f"{scene['id']} - {scene['title']} is unique, untagged as duplicate")
        return

    # if not dupe tagged now, and number > 1, add
    if numberofscenes > 1 and config.dupetitle_tagname not in existing_tags:
        stash.update_scenes({
            'ids': [scene['id']],
            'tag_ids': {
                'mode': 'ADD',
                'ids': [dupetitle_id]
            }
        })
        log.info(f"{scene['id']} - {scene['title']} is not unique, tagged as duplicate")
        return

    log.debug(f"no change to {scene['id']} - {scene['title']}")
    #return

def checkstashid(scene):
    # if no stashid - leave
    if not scene['stash_ids']:
       log.debug(f"Scene {scene['id']} has no StashID")
       return
    scene = stash.find_scene(scene['id'])
    if not scene:
       log.debug("Scene issue")
       return
    existing_tags = get_names(scene.get("tags"))
    dupestashid_id = stash.find_tag(config.dupestashid_tagname, create=True).get("id")

    # check number of scenes with this title

    # add stashid filter
    filterstashid = {}
    filterstashid["value"] = scene['stash_ids'][0]["stash_id"]
    filterstashid["modifier"] = "EQUALS"
    filter = {}
    filter["stash_id"] = filterstashid
    filterlimits = {}
    filterlimits["per_page"] = 5

    numberofscenes = len(stash.find_scenes(filter, filterlimits, fragment="id"))

    # if dupe tagged now and number = 1, remove
    if numberofscenes == 1 and config.dupestashid_tagname in existing_tags:
        stash.update_scenes({
            'ids': [scene['id']],
            'tag_ids': {
                'mode': 'REMOVE',
                'ids': [dupestashid_id]
            }
        })
        log.info(f"{scene['id']} - {scene['title']} is unique stashid, untagged as duplicate")
        return

    # if not dupe tagged now, and number > 1, add
    if numberofscenes > 1 and config.dupestashid_tagname not in existing_tags:
        stash.update_scenes({
            'ids': [scene['id']],
            'tag_ids': {
                'mode': 'ADD',
                'ids': [dupestashid_id]
            }
        })
        log.info(f"{scene['id']} - {scene['title']} is not unique stashid, tagged as duplicate")
        return

    log.debug(f"no change to {scene['id']} - {scene['title']}")
    #return

def checkurl(scene):
    # if no url - leave
    if not scene['url']:
       log.debug(f"Scene {scene['id']} has no URL")
       return
    scene = stash.find_scene(scene['id'])
    if not scene:
       log.debug("Scene issue")
       return
    existing_tags = get_names(scene.get("tags"))
    dupeurl_id = stash.find_tag(config.dupeurl_tagname, create=True).get("id")

    # check number of scenes with this url

    # add url filter
    filterurl = {}
    filterurl["value"] = scene['url']
    filterurl["modifier"] = "EQUALS"
    filter = {}
    filter["url"] = filterurl
    filterlimits = {}
    filterlimits["per_page"] = 5

    numberofscenes = len(stash.find_scenes(filter, filterlimits, fragment="id"))

    # if dupe tagged now and number = 1, remove
    if numberofscenes == 1 and config.dupeurl_tagname in existing_tags:
        stash.update_scenes({
            'ids': [scene['id']],
            'tag_ids': {
                'mode': 'REMOVE',
                'ids': [dupeurl_id]
            }
        })
        log.info(f"{scene['id']} - {scene['title']} is unique url, untagged as duplicate")
        return

    # if not dupe tagged now, and number > 1, add
    if numberofscenes > 1 and config.dupeurl_tagname not in existing_tags:
        stash.update_scenes({
            'ids': [scene['id']],
            'tag_ids': {
                'mode': 'ADD',
                'ids': [dupeurl_id]
            }
        })
        log.info(f"{scene['id']} - {scene['title']} is not unique url, tagged as duplicate")
        return

    log.debug(f"no change to {scene['id']} - {scene['title']}")
    #return

def find_duplicate_title(scene):
    result = {}
    DuplicateTitleTag = stash.find_tag("Duplicate Title", create=True).get("id")
    currenttags = get_id(scene["tags"])
    #if DuplicateTitleTag in currenttags:
    #  log.debug("Title is already tagged as duplicate")
    #  return result

    query = """
          query titledupe($title: String!){
                  findScenes(
                    filter: {per_page: 10}
                    scene_filter:{
                      title: {
                        value: $title
                        modifier: EQUALS
                      }
                    }
                  ){
                   count
                   scenes{ id }
                   }
                 }
            """
    variables = {
          "title": scene["title"]
    }
    scenecount = call_graphql(query, variables)
    #log.debug(scenecount)
    if scenecount["findScenes"]["count"] == 1:
       if DuplicateTitleTag in currenttags:
          log.debug("Title is wrongly tagged as duplicate.  Fixing.")
          tagging = {}
          tagging["id"] = scene["id"]
          tagging["tag_ids"] = currenttags
          tagging["tag_ids"].remove(DuplicateTitleTag)
          query = """
            mutation tagsubmitted($input: SceneUpdateInput!) {
                  sceneUpdate(input: $input) {
                   title
                  }
            }
            """
          variables = {
             "input": tagging
          }
          #log.debug(variables)
          tagging = call_graphql(query, variables)
          #if tagging:
          #   log.debug(tagging)
          return result
    if scenecount["findScenes"]["count"] > 1:
          for sceneid in get_id(scenecount["findScenes"]["scenes"]):
              tagging = {}
              tagging["id"] = sceneid
              thisscene = graphql.getScene(sceneid)
              tagging["tag_ids"] = currenttags = get_id(thisscene["tags"])
              if DuplicateTitleTag in tagging["tag_ids"]:
                 log.debug("Scene already has a duplicate title, not tagging it")
              else:
                 log.debug("Scene is a duplicate title, and not yet tagged. tagging it")
                 tagging["tag_ids"].append(DuplicateTitleTag)
                 query = """
            mutation tagsubmitted($input: SceneUpdateInput!) {
                  sceneUpdate(input: $input) {
                   title
                  }
            }
            """
                 variables = {
                    "input": tagging
                 }
                 #log.debug(variables)
                 tagging = call_graphql(query, variables)
                 if tagging:
                    log.debug(tagging)
    else:
       log.debug("Scene has no duplicate title")
    return result

def main():
    global stash

    json_input = json.loads(sys.stdin.read())
    FRAGMENT_SERVER = json_input["server_connection"]
    PLUGIN_ARGS = False
    HOOKCONTEXT = False

    try:
        PLUGIN_ARGS = json_input['args']["mode"]
    except:
        pass

    if PLUGIN_ARGS:
        log.debug("--Starting Plugin 'Duplicate Title'--")
        stash = StashInterface(FRAGMENT_SERVER)
        if "dupefindall" in PLUGIN_ARGS:
            log.info("Duplicate Title tagging")
            dupefindall() #loops thru all scenes, and tag
        exit_plugin("Duplicate Title plugin finished")

    enabled = config.enabled
    if not enabled:
        exit_plugin("Duplicate Title plugin disabled")

    try:
        HOOKCONTEXT = json_input['args']["hookContext"]
    except:
        exit_plugin("Duplicate Title hook: No hook context")

    log.debug("--Starting Hook 'Duplicate Title'--")

    stash = StashInterface(FRAGMENT_SERVER)
    sceneID = HOOKCONTEXT['id']
    scene = stash.find_scene(sceneID)

    if config.titledupe:
        if scene["title"]:
            results = checktitle(scene)
        else:
            log.debug("Scene lacks title, so it was not checked.")

    if config.stashiddupe:
        if scene['stash_ids']:
            results = checkstashid(scene)
        else:
            log.debug("Scene lacks stashid, so it was not checked.")

    if config.urldupe:
        if scene['url']:
            results = checkurl(scene)
        else:
            log.debug("Scene lacks url, so it was not checked.")

    exit_plugin("Duplicate Title hook completed")

main()
