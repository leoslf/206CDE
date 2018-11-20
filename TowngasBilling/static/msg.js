function dump_msg() {
    var cookies = cookie_dict();
    const msgType = ["successmsg", "infomsg", "warnmsg", "errmsg"];
    msgType.forEach(function (e) {
        if (e in cookies && cookies[e].length > 0) {
            $("#" + e + "  .modal-text").text(cookies[e]);
            set_cookie(e, "", 0);	
	    $("#" + e).modal('open');
        }
    });
    const id_existances = msgType.map(type => $("#" + type).length > 0);
    // if all(id does not exist)
    // by (not even some if the id exists)
    if (!id_existances.some(id_exist => id_exist === true)) {
        for (var key in cookies) {
            if (cookies[key].length > 0) {
                alert(key + ": " + cookies[key]);
            }
        }
    }
    
    // the "href" attribute of the modal trigger must specify the modal ID that wants to be triggered
    $('.modal').modal();

}

window.addEventListener("load", dump_msg, false);
                      

        
