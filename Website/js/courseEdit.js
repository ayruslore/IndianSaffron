function addC(){
    document.getElementById("ad").innerHTML='<input id="new_course" type="text" value="">';
    document.getElementById("ad").innerHTML+='<button onclick="addCo()">Add</button>';
}

function addCo(){
  console.log(document.getElementById("new_course").value);
  DATA["Courses"][toTitleCase(document.getElementById("new_course").value)]={};
  keys.push(toTitleCase(document.getElementById("new_course").value));
  console.log(keys);
  alert("Add dishes to the course to make it a valid course!");
}
