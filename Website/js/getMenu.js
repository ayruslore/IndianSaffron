var DATA;
var uid;

function getMenu(){
  $.ajax({
    type: "GET",
    url: redisDb+"/get_menu",
    success: function(data){
      console.log('Success!');
      DATA=data;
      populate();
      viewMenu();
      courses();
      courses2();
      document.getElementById("course1").click();

    },
    error: function(data){
      console.log('Nope!');
    }
  });
}

function getURL(){
  var str = window.location.href;
  uid="";
  for (var i = 0; i<=str.length; i++){
    //console.log(str.charAt(i));
    if (str.charAt(i) == "="){
      for ( var j=i+1; j<str.length; j++){
        if(str.charAt(j)=="#")
          break;
        uid = uid + str.charAt(j);
      }
      break;
    }
  }
  console.log(str);
  console.log(uid);
}
