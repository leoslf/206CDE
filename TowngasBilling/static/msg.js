function dump_msg() {
    var cookies = cookie_dict();
    const msgType = ["successmsg", "infomsg", "warnmsg", "errmsg"];
    msgType.forEach(function (e) {
        if (e in cookies && cookies[e].length > 0) {
            $("#" + e).removeClass("hidden")
                      .append(cookies[e]);
            set_cookie(e, "", 0);
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

}

window.addEventListener("load", dump_msg, false);
                      

        
