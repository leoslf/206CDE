function navbar_active() {
    //$("#shared_navbar").find("a").each(function(index, element) {
    $("a").each(function(index, element) {
        var href = $(element).attr("href");
        // console.log("href: " + href + " vs " + window.location.href);
        if (window.location.pathname.indexOf(href) != -1)
            $(element).addClass("active");
    });
}

window.addEventListener("load", navbar_active, false);

