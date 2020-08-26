# This script requires Python2

# regex needed
import re

#########
#########
# Reading from the file 
# TODO: Figure out a neater way to divide the text file into an array

# This file contain infromation of installed packages
filePath = "/var/lib/dpkg/status"
# in demo version we use custom file
filePath = "status.real"

# This is the keyword for diving the file into smaller pieces
separator = "Package:"

print "Reading from file "+filePath

# Read through the file
with open(filePath) as myFile:
  text = myFile.read()

# file into an array, each containing info of individual package
result = text.split(separator)
resultTmp = []

# add the Package keyword that was removed by split
for r in result:
    if r != '':
        resultTmp.append("Package:"+r)

result = resultTmp

###############
###############
# Preprocessing
# TODO: Add try-catch to description part

# This dictionary will have packagenames as keys and contain dictionaries of info related to packages 
packages = {}
print "Processing "+str(len(result))+ " entries."

# extracts info
for package in result:
    name = ""
    descriptionShort = ""
    descriptionLong = ""
    dependsOn = ""
    # processing to make data more browser/HTML friendly: remove \, otherwise browser may crash
    package = re.sub(r"\\"," ",package)
    # needs to be added for HTML-fle writing
    package = re.sub(r"\"","\\\"",package)
    
    if re.search(r'Package: (.*)', package):#.group() 
        name = re.search(r'Package: (.*)', package).group(1)

    if re.search(r'Description: (.*)', package, re.M + re.DOTALL):#.group() 
        descriptionShort = re.search(r'Description: ([^\n]*)\n(.*)', package,re.M|re.DOTALL).group(1)
        # this might need some try catching
        descriptionLong = re.search(r'Description: ([^\n]*)\n(.*)', package,re.M|re.DOTALL).group(2)
        # some HTML preprocessing
        descriptionLong = descriptionLong.replace("\n","<br />")
        
    if re.search(r'Depends: (.*)', package):#.group() 
        matches = re.search(r'Depends: (.*)', package).group(1)
        # remove version information : remove here everything inside paranthesis        
        matches = re.sub("\(.*?\)", "", matches ) 
        matches = matches.split(",")
        # remove white spaces
        # TODO: is this really neccessary?
        matches =  [i.strip() for i in matches]
        dependsOn = matches
    packages[name] = { "DescriptionShort":descriptionShort,"DescriptionLong":descriptionLong, "Depends":dependsOn, "RequiredBy":[]}


# We need to fill the requiredBy field
# go through every packets dependencies and add the name of the package to the RequiredBy list of the dependent package
# for every packet 
for p_name in sorted(packages.keys()):
    for dp in packages[p_name]["Depends"]:
        if packages.get(dp):
            packages[dp]["RequiredBy"].append(p_name)
        #else:
        #    print "! Package "+str(dp)+" not in list"

##############
##############
# HTML-file generation
# TODO: find out do we need two link_line functions

# s will eventually we written to the HTML file
s = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {
  font-family: Arial;
  color: white;
}
.split {
  padding:0px;
  height: 100%;
  width: 50%;
  position: fixed;
  z-index: 1;
  top: 0;
  overflow-x: hidden;
}
.left {
  left: 0;
  background-color: #111;
}
.right {
  right: 0;
  background-color: red;
}
.centered { text-align: center; }
</style>
</head>
<script>\n"""

# will hold the data
s += "data = []\n"

# will hold the package names
dataNames = ','.join(map( lambda s : "\""+s+"\"",sorted(packages.keys())))

s += "dataNames = [" + str(dataNames) + "]\n"

#link_line = lambda p_name : "<a id=\""+p_name+"\" href=\"#\" onclick=\"show('"+p_name+"');\">"+p_name+"</a><br /> \n"
link_line2 = lambda p_name : '<a id="'+p_name+'" href="#" onclick="show("'+p_name+'");">'+p_name+'"</a><br /> \n'
link_line3 = lambda p_name : '<a href=\\\"#\\\" onclick=\\\"show(\\\''+p_name+'\\\');\\\">'+p_name+'</a>'


# dependencies list contain char '|' we need a parser to loop through all dependency possibilities
def parser(line):
    if line.find('|') != -1:
        line = line.split('|')
        line =  [i.strip() for i in line]

        temp = []
        tmpS = ""
        for l in line:
            if l in packages.keys():
                tmpS = '<a href=\\\"#\\\" onclick=\\\"show(\\\''+l+'\\\');\\\">'+l+'</a>'
            else:
                tmpS = l                
            temp.append(tmpS)
        return '|'.join(temp)
    else:
        return link_line3(line)

for p_name in sorted(packages.keys()):
    p = packages[p_name]
    
    deps = '<br />'.join(map( parser, p["Depends"]))
    reqs = '<br />'.join(map( parser, p["RequiredBy"]))

    s += "data.push({"
    s += "name:\""+p_name+"\","
    s += "description_short:\""+p.get("DescriptionShort")+"\","
    s += "description_long:\""+p.get("DescriptionLong")+"\","
    s += "depends_on:\""+deps+"\",required_by:\""+reqs+"\""
    s += "});\n"

s += """
// render the left side
function renderPackets(){
    var searchTerm = document.getElementById('searchField').value
    var list = dataNames.filter(word => word.includes(searchTerm) ).sort()
    
    var container = document.getElementById('packets')
    //debugger;
    
    var listCopy = []
    var prev = ""
    var cur = ""

    // for adding the alphabets to make more readable
    for( var i = 0; i < list.length; i++ ) {
        cur = list[i][0]
        if( cur !== prev ) {
            listCopy.push("<hr/><h2>"+cur.toUpperCase()+"</h2>")
            prev = cur
        }
        listCopy.push(list[i])
    }

    list = listCopy;

    var context = list.map((p_name) => { return p_name[0] === '<' ? p_name : "<a id='"+p_name+"' href='#' onclick=\\\"show('"+p_name+"');\\\">"+p_name+"</a><br />" })
    context = context.join("");

    container.innerHTML = context
}

// for the show more/less info button
function toggleDescriptionVisibilityState(){
    if(document.getElementById('description_longID').style.display == 'none') {
        document.getElementById('description_longID').style.display='block'
        document.getElementById('description_longID_toggler').textContent = "Show less"
    }
    else{
        document.getElementById('description_longID').style.display='none'
        document.getElementById('description_longID_toggler').textContent = "Show more"
    }
}
// for the right side
function show(item){ 
    console.log(data)
    data.forEach( (value) => { 
        if( item === value.name ) { 
            console.log(value.name);
            document.getElementById("nameID").innerHTML = value.name 
            document.getElementById("description_shortID").innerHTML = value.description_short 
            document.getElementById("description_longID").innerHTML = value.description_long 
            document.getElementById("depends_onID").innerHTML = value.depends_on ? value.depends_on : "None"
            document.getElementById("required_byID").innerHTML = value.required_by ? value.required_by : "None"  

        } } ) 
};

function init(){
    toggleDescriptionVisibilityState();
    show(data[0].name);
    renderPackets();

}

</script>
<body onload="init()">"""

s += """
 <div class="split left">
  <div class="centered">
    <h2>Packets</h2>
    <h4>Search:</h4>
     <input type="text" id="searchField" onkeyup="renderPackets()"> 

    <div id="packets"></div>
"""

s += """
  </div>
</div>

<div class="split right">
  <div class="centered">
    <h2 id="nameID"></h2>
    <p id="description_shortID"></p>
    <p id="description_longID"></p>
    <button id="description_longID_toggler" onClick="toggleDescriptionVisibilityState()"; ">Show Less</button>
    <h4>Depends on</h4>
    <div id="depends_onID"></div>
    <h4>Is required by</h4>
    <div id="required_byID"></div>
  </div>
</div> 
"""

s += """</body>
</html>"""


f = open("status.html", "w")
f.write(s)
f.close()
print "HTML-file generated."
