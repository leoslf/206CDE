"use strict";

function cookie_dict() {
    var dict = {},
        lst = decodeURIComponent(document.cookie).split(";")
                    .map(x => x.trim());

    lst.forEach(function (e) {
        if (e != "") {
            var name = e.substring(0, e.indexOf("=")),
                value = e.substring(e.indexOf("=") + 1, e.length)
                            .replace(/"([^"]+(?="))"/g, "$1");
            dict[name] = value;
        }
    });
    return dict;
}

function get_cookie(name) {
    var dict = cookie_dict();
    return name in dict ? dict[name] : "";
}


function set_cookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    var expires = "expires="+ d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}


