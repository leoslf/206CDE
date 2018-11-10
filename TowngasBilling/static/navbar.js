function navbar_active() {
    //$("#shared_navbar").find("a").each(function(index, element) {
    $("a").each(function(index, element) {
        var href = $(element).attr("href");
        // console.log("href: " + href + " vs " + window.location.href);
        if (window.location.pathname.indexOf(href) != -1)
            $(element).addClass("active");
    });
}

$("#account_list > li > a").click(function () {
    var account_id = $(this).attr("account_id"),
        self = this;
    $.post("/use_account", {
            account_id: account_id
        },
        function (data) {
            console.log("POST /use_account with account_id = " + account_id + "\n" + JSON.stringify(data));
            $(".selected_account").each(function () {
                $(this).removeClass("selected_account");
                console.log(this);
            });
            $(self).addClass("selected_account");
            console.log(self);
        });
});

$("#customer_list > li > a").click(function () {
    var customer_id = $(this).attr("customer_id"),
        self = this;
    $.post("/use_customer_id", {
            customer_id: customer_id
        },
        function (data) {
            console.log("POST /use_customer_id with customer_id = " + customer_id + "\n" + JSON.stringify(data));
            $(".selected_customer").each(function () {
                $(this).removeClass("selected_customer");
                console.log(this);
            });
            $(self).addClass("selected_customer");
            console.log(self);
        });
});

window.addEventListener("load", navbar_active, false);

